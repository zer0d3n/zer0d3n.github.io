# zer0d3n.github.io

Mi blog semanal sobre el camino hacia la seguridad cloud: <https://zer0d3n.github.io>. Está hecho con
[Jekyll](https://jekyllrb.com) y el tema [Chirpy](https://github.com/cotes2020/jekyll-theme-chirpy), y se publica con
GitHub Actions en cada push a `main`.

## Publicar una entrada

1. En el repo del plan, genera el borrador de la semana: `python3 tools/borrador_blog.py` (sale de tu tracker y de
   tus notas diarias y se queda allí, en privado, en `seguimiento/borradores-blog/`).
2. Reescríbelo con tu voz y repasa la lista de «Nunca publiques» de abajo.
3. Cópialo aquí como `_posts/AAAA-MM-DD-nombre.md`. El nombre, en minúsculas, sin tildes ni espacios, es la URL:
   `_posts/2026-09-27-semana-01-02.md` → `https://zer0d3n.github.io/posts/semana-01-02/`.
4. `git add`, `git commit` y `git push`.

En un par de minutos la web está actualizada y tienes un aviso en **Issues** («LinkedIn: título de la entrada») con
el texto listo para copiar y el enlace. Lo pegas en una publicación nueva de LinkedIn y cierras el aviso. Cada entrada
genera un solo aviso, aunque la corrijas después.

### Cabecera de una entrada

```yaml
---
title: "Semana 3: endurecí una VM y terminé Bandit"
date: 2026-10-04 18:00:00 +0200
categories: [Diario de aprendizaje, Bloque 1]
tags: [learn-to-cloud, linux, bash]
description: "Una frase: aparece en buscadores y en la tarjeta del enlace."
linkedin: |
  El texto para LinkedIn, escrito para LinkedIn: qué hiciste, qué aprendiste
  y una pregunta al final para tu red.
---
```

- **Programar una entrada:** ponle una fecha futura. Se publica sola la mañana de ese día (la pipeline se ejecuta
  cada día a las 6:00 UTC) y el aviso de LinkedIn llega entonces.
- **Sin aviso de LinkedIn:** `linkedin: false` en la cabecera.
- **Borradores:** no uses `_drafts/`. Este repo es público y cualquiera puede leer los ficheros aunque la web no los
  muestre. Los borradores se quedan en el repo privado del plan.

## Ver la web en local

```bash
bundle config set --local path vendor/bundle   # una sola vez
bundle install
bundle exec jekyll s --future                  # http://127.0.0.1:4000, incluidas las programadas
```

## Qué hace la pipeline

`.github/workflows/pages-deploy.yml`, en cada push a `main`, cada mañana y a mano desde la pestaña Actions:

1. **secrets:** gitleaks revisa el historial. Si encuentra un secreto, no se publica nada.
2. **build:** Jekyll construye la web y htmlproofer comprueba que no hay enlaces internos rotos.
3. **deploy:** la publica en GitHub Pages.
4. **linkedin:** `tools/linkedin.py` abre un aviso por cada entrada publicada que aún no lo tenga.
   Pruébalo sin tocar GitHub con `python3 tools/linkedin.py --prueba`.

## Configuración de una sola vez

- **Settings → Pages → Build and deployment → Source: GitHub Actions.** Sin esto, el paso de deploy falla.
- **LinkedIn en la web:** pon la URL de tu perfil en `social.links` de `_config.yml` y descomenta el bloque de
  `_data/contact.yml`.
- **Hook de gitleaks en tu máquina:** `git config core.hooksPath tools/hooks` (el mismo que en el repo del plan).
- **dev.to (opcional, más lectores gratis):** en dev.to, Settings → Extensions → publicar desde RSS con
  `https://zer0d3n.github.io/feed.xml` y la opción de marcar tu blog como URL canónica. Importa cada entrada como
  borrador; la revisas y la publicas allí sin perder el crédito del original.

## Nunca publiques

IDs de cuenta de AWS, ARNs completos, IPs, claves, tokens, contraseñas, flags o soluciones de retos (OverTheWire, los
CTF de Learn to Cloud), ni nada de un cliente sin su permiso por escrito. Cuenta el método, no la respuesta.
`tools/borrador_blog.py` avisa de lo más obvio, y gitleaks bloquea claves; el resto es tu revisión.

## Licencia

La plantilla es de [Chirpy](https://github.com/cotes2020/jekyll-theme-chirpy) (MIT, ver `LICENSE`). Los textos de las
entradas son míos y se publican con la licencia que indica el pie de la web.
