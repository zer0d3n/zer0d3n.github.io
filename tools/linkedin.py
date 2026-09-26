#!/usr/bin/env python3
"""Abre un aviso (issue) con el texto para LinkedIn de cada entrada publicada que aún no lo tenga.

Lo ejecuta la pipeline justo después de desplegar la web, así que el enlace del aviso ya funciona.
- Una entrada genera un solo aviso, aunque la edites y vuelvas a hacer push: se reconoce por el
  nombre del fichero, que va escondido en el cuerpo del aviso.
- Las entradas programadas (fecha futura) esperan a su día, igual que hace Jekyll.
- `linkedin: false` en la cabecera de una entrada la deja fuera.

Uso local, sin tocar GitHub:  python3 tools/linkedin.py --prueba
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from datetime import date, datetime, time
from pathlib import Path
from zoneinfo import ZoneInfo

import yaml

RAIZ = Path(__file__).resolve().parents[1]
ETIQUETA = "linkedin"
NOMBRE = re.compile(r"^(\d{4}-\d{2}-\d{2})-(.+)\.(md|markdown)$")
MARCA = "<!-- entrada: {} -->"


def cabecera(path: Path) -> dict:
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", path.read_text(encoding="utf-8"), re.S)
    return (yaml.safe_load(m.group(1)) or {}) if m else {}


def fecha_de(valor, respaldo: str, zona: ZoneInfo) -> datetime:
    """La fecha de publicación como la entiende Jekyll: sin hora es medianoche y sin zona, la del sitio."""
    if isinstance(valor, str):  # «2026-09-27 10:00:00 +0200», el formato de Chirpy, llega como texto
        for formato in ("%Y-%m-%d %H:%M:%S %z", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
            try:
                valor = datetime.strptime(valor.strip(), formato)
                break
            except ValueError:
                continue
        else:
            raise SystemExit(f"Fecha que no entiendo en una entrada: {valor!r}")
    if valor is None:
        valor = date.fromisoformat(respaldo)
    if not isinstance(valor, datetime):
        valor = datetime.combine(valor, time())
    return valor if valor.tzinfo else valor.replace(tzinfo=zona)


def hashtags(etiquetas) -> str:
    limpias = [re.sub(r"[^0-9A-Za-zÁÉÍÓÚÜÑáéíóúüñ]", "", str(e)) for e in (etiquetas or [])]
    return " ".join(f"#{e}" for e in limpias[:5] if e)


def publicadas(config: dict, ahora: datetime):
    zona = ZoneInfo(config.get("timezone") or "UTC")
    base = (config.get("url") or "").rstrip("/") + (config.get("baseurl") or "")
    for p in sorted((RAIZ / "_posts").glob("*.md")):
        m = NOMBRE.match(p.name)
        if not m:
            continue
        fm = cabecera(p)
        if fm.get("published") is False or fm.get("linkedin") is False:
            continue
        if fecha_de(fm.get("date"), m.group(1), zona) > ahora:
            continue  # programada: todavía no está en la web
        slug = fm.get("slug") or m.group(2)
        url = base + (fm.get("permalink") or f"/posts/{slug}/")
        yield p, fm, url


def cuerpo(p: Path, fm: dict, url: str) -> str:
    titulo = fm.get("title") or p.stem
    texto = (fm.get("linkedin") or "").strip()
    por_defecto = not texto
    if por_defecto:
        texto = f"{titulo}\n\n{(fm.get('description') or '').strip()}".strip()
    etiquetas = hashtags(fm.get("tags"))
    if etiquetas and "#" not in texto:
        texto += f"\n\n{etiquetas}"
    lineas = [
        f"La entrada **{titulo}** ya está publicada: {url}",
        "",
        "Copia este texto en una publicación nueva de LinkedIn (el botón de copiar está arriba a la derecha del bloque):",
        "",
        "````text",
        f"{texto}\n\n{url}",
        "````",
        "",
    ]
    if por_defecto:
        lineas += ["> La entrada no tenía `linkedin:` en la cabecera, así que este es un texto genérico. "
                   "Uno escrito para LinkedIn (qué hiciste, qué aprendiste, una pregunta al final) funciona mucho mejor.", ""]
    lineas += ["Cuando lo publiques, cierra este aviso.", "", MARCA.format(p.relative_to(RAIZ).as_posix())]
    return "\n".join(lineas)


def gh(*args: str, entrada: str | None = None) -> str:
    return subprocess.run(["gh", *args], input=entrada, text=True, capture_output=True, check=True).stdout


def ya_avisadas() -> set:
    datos = json.loads(gh("issue", "list", "--label", ETIQUETA, "--state", "all", "--limit", "1000", "--json", "body"))
    return {m.group(1) for d in datos for m in [re.search(r"<!-- entrada: (.+?) -->", d.get("body") or "")] if m}


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--prueba", action="store_true", help="muestra los avisos sin crear nada en GitHub")
    args = p.parse_args()

    config = yaml.safe_load((RAIZ / "_config.yml").read_text(encoding="utf-8"))
    ahora = datetime.now(ZoneInfo(config.get("timezone") or "UTC"))
    hechas = set() if args.prueba else ya_avisadas()
    if not args.prueba:
        gh("label", "create", ETIQUETA, "--color", "0A66C2", "--description", "Entrada lista para publicar en LinkedIn", "--force")

    nuevas = 0
    for post, fm, url in publicadas(config, ahora):
        ruta = post.relative_to(RAIZ).as_posix()
        if ruta in hechas:
            continue
        titulo = f"LinkedIn: {fm.get('title') or post.stem}"
        texto = cuerpo(post, fm, url)
        nuevas += 1
        if args.prueba:
            print(f"--- {titulo}\n{texto}\n")
            continue
        creado = ["issue", "create", "--title", titulo, "--label", ETIQUETA, "--body-file", "-"]
        if os.environ.get("ASIGNAR_A"):
            creado += ["--assignee", os.environ["ASIGNAR_A"]]
        print(gh(*creado, entrada=texto).strip())

    resumen = f"Avisos de LinkedIn nuevos: {nuevas}"
    print(resumen)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as f:
            f.write(resumen + "\n")


if __name__ == "__main__":
    main()
