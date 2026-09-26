# zer0d3n.github.io

My weekly blog about the road to cloud security: <https://zer0d3n.github.io>. Built with
[Jekyll](https://jekyllrb.com) and the [Chirpy](https://github.com/cotes2020/jekyll-theme-chirpy) theme, and
published with GitHub Actions on every push to `main`.

## Publishing a post

1. In the study plan repo, generate the week's draft: `python3 tools/borrador_blog.py` (built from the tracker and
   the daily notes; it stays there, private, in `seguimiento/borradores-blog/`).
2. Rewrite it in your own voice and go through the «Never publish» list below.
3. Copy it here as `_posts/YYYY-MM-DD-name.md`. The name, lowercase with no spaces or accents, becomes the URL:
   `_posts/2026-09-27-week-01-02.md` → `https://zer0d3n.github.io/posts/week-01-02/`.
4. `git add`, `git commit` and `git push`.

A couple of minutes later the site is updated and there is a new issue («LinkedIn: post title») with the text ready
to copy and the link. Paste it into a new LinkedIn post and close the issue. Each post gets a single issue, even if
you fix it later.

### Front matter

```yaml
---
title: "Week 3: I hardened a VM and finished Bandit"
date: 2026-10-04 18:00:00 +0200
categories: [Learning log, Block 1]
tags: [learn-to-cloud, linux, bash]
description: "One sentence: it shows up in search engines and in the link preview."
linkedin: |
  The text for LinkedIn, written for LinkedIn: what you did, what you learned
  and a question at the end for your network.
---
```

- **Scheduling a post:** give it a future date. It goes live on its own the morning of that day (the pipeline runs
  every day at 06:00 UTC) and the LinkedIn issue arrives then.
- **No LinkedIn issue:** `linkedin: false` in the front matter.
- **Drafts:** don't use `_drafts/`. This repo is public and anyone can read the files even if the site doesn't show
  them. Drafts stay in the private study plan repo.

## Preview locally

```bash
bundle config set --local path vendor/bundle   # once
bundle install
bundle exec jekyll s --future                  # http://127.0.0.1:4000, scheduled posts included
```

## What the pipeline does

`.github/workflows/pages-deploy.yml`, on every push to `main`, every morning and manually from the Actions tab:

1. **secrets:** gitleaks scans the history. If it finds a secret, nothing gets published.
2. **build:** Jekyll builds the site and htmlproofer checks for broken internal links.
3. **deploy:** publishes it to GitHub Pages.
4. **linkedin:** `tools/linkedin.py` opens an issue for every published post that doesn't have one yet.
   Try it without touching GitHub with `python3 tools/linkedin.py --dry-run`.

## One-time setup

- **Settings → Pages → Build and deployment → Source: GitHub Actions.** Without it, the deploy step fails.
- **LinkedIn on the site (optional):** add your profile URL to `social.links` in `_config.yml` and uncomment the
  block in `_data/contact.yml`.
- **gitleaks hook on your machine:** `git config core.hooksPath tools/hooks`.
- **Private commit email:** `git config user.email "<id>+zer0d3n@users.noreply.github.com"` (your address is in
  GitHub → Settings → Emails), so this public repo doesn't expose your personal email.
- **dev.to (optional, free extra readers):** on dev.to, Settings → Extensions → publish from RSS with
  `https://zer0d3n.github.io/feed.xml`, marking this blog as the canonical URL. Each post is imported as a draft
  that you review and publish there, and the original keeps the credit.

## Never publish

AWS account IDs, full ARNs, IPs, keys, tokens, passwords, challenge flags or solutions (OverTheWire, the Learn to
Cloud CTFs), or anything from a client without their written permission. Share the method, not the answer.
`tools/borrador_blog.py` flags the obvious ones and gitleaks blocks keys; the rest is your review.

## License

The template comes from [Chirpy](https://github.com/cotes2020/jekyll-theme-chirpy) (MIT, see `LICENSE`). Post
content is mine and published under the license shown in the site footer.
