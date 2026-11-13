#!/usr/bin/env python3
"""Builds the 9nth Dimension site from content/ into docs/ (served by GitHub Pages).

Usage: python3 build.py
Content:
  content/site.yml            site settings (url, base path, name)
  content/rungs/<n>-<slug>.md one hub per rung of the Spiritual Ladder
  content/articles/<slug>.md  question articles (front matter: rung, date, faq...)
  content/pages/<slug>.md     standalone pages (about, ladder overview)
"""
import datetime as dt
import html
import json
import re
import shutil
from pathlib import Path

import markdown
import yaml

ROOT = Path(__file__).parent
CONTENT = ROOT / "content"
OUT = ROOT / "docs"
STATIC = ROOT / "static"

SEAL_SVG = ('<svg class="seal" viewBox="0 0 64 64" aria-hidden="true">'
            '<circle cx="32" cy="32" r="29" fill="#6e1214" stroke="#b5925b" stroke-width="3"/>'
            '<circle cx="32" cy="32" r="22" fill="none" stroke="#b5925b" stroke-width="1"/>'
            '<path d="M32 21v22M21 32h22" stroke="#b5925b" stroke-width="3" stroke-linecap="round"/></svg>')

AI_AND_SEARCH_BOTS = [
    "Googlebot", "Bingbot", "GPTBot", "OAI-SearchBot", "ChatGPT-User",
    "PerplexityBot", "Perplexity-User", "ClaudeBot", "Claude-SearchBot",
    "Google-Extended", "Applebot", "Applebot-Extended", "DuckDuckBot",
]


def read_md(path):
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    if not m:
        raise SystemExit(f"{path}: missing front matter")
    meta = yaml.safe_load(m.group(1)) or {}
    meta["body_md"] = m.group(2).strip()
    meta["source"] = path
    return meta


def md_to_html(text):
    return markdown.markdown(text, extensions=["extra", "sane_lists", "toc"])


def esc(s):
    return html.escape(str(s), quote=True)


def as_date(v):
    if isinstance(v, dt.date):
        return v
    return dt.date.fromisoformat(str(v))


ROMAN = {1: "I", 2: "II", 3: "III", 4: "IV", 5: "V", 6: "VI", 7: "VII", 8: "VIII"}


SOCIAL_ICONS = {
    "TikTok": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M16.6 3c.4 2.2 1.8 3.7 4 3.9v3.2c-1.5 0-2.8-.4-4-1.2v6.1c0 3.4-2.7 6-6.1 6S4.4 18.4 4.4 15s2.7-6 6.1-6c.3 0 .6 0 .9.1v3.3a2.9 2.9 0 1 0 2 2.7V3h3.2z" fill="currentColor"/></svg>',
    "YouTube": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M22.5 7.2a2.8 2.8 0 0 0-2-2C18.8 4.8 12 4.8 12 4.8s-6.8 0-8.5.4a2.8 2.8 0 0 0-2 2C1.1 8.9 1.1 12 1.1 12s0 3.1.4 4.8a2.8 2.8 0 0 0 2 2c1.7.4 8.5.4 8.5.4s6.8 0 8.5-.4a2.8 2.8 0 0 0 2-2c.4-1.7.4-4.8.4-4.8s0-3.1-.4-4.8zM9.8 15.1V8.9l5.6 3.1-5.6 3.1z" fill="currentColor"/></svg>',
    "Facebook": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M13.5 21.9v-7.6h2.6l.4-3h-3V9.4c0-.9.3-1.5 1.5-1.5h1.6V5.2c-.3 0-1.2-.1-2.3-.1-2.3 0-3.9 1.4-3.9 4v2.2H7.8v3h2.6v7.6h3.1z" fill="currentColor"/></svg>',
}


class Site:
    def __init__(self):
        self.cfg = yaml.safe_load((CONTENT / "site.yml").read_text())
        self.base = self.cfg["base_path"].rstrip("/")
        self.url = self.cfg["url"].rstrip("/")
        self.today = dt.date.today()
        self.rungs = sorted(
            (read_md(p) for p in (CONTENT / "rungs").glob("*.md")),
            key=lambda r: r["number"],
        )
        self.rung_by_slug = {r["slug"]: r for r in self.rungs}
        self.articles = []
        for p in sorted((CONTENT / "articles").glob("*.md")):
            a = read_md(p)
            a["slug"] = p.stem
            a["date"] = as_date(a["date"])
            a["updated"] = as_date(a.get("updated", a["date"]))
            if a["date"] > self.today:  # scheduled for later, not published yet
                continue
            if a["rung"] not in self.rung_by_slug:
                raise SystemExit(f"{p}: unknown rung '{a['rung']}'")
            self.articles.append(a)
        self.articles.sort(key=lambda a: a["date"], reverse=True)
        self.pages = [read_md(p) | {"slug": p.stem} for p in (CONTENT / "pages").glob("*.md")]
        self.sitemap = []

    def socials_html(self, cls):
        links = "".join(
            f'<a href="{esc(s["url"])}" rel="me noopener" target="_blank" aria-label="9nth Dimension on {esc(s["name"])}">'
            f'{SOCIAL_ICONS.get(s["name"], "")}<span>{esc(s["name"])}</span></a>'
            for s in self.cfg.get("socials", [])
        )
        return f'<nav class="{cls}" aria-label="9nth Dimension on social media">{links}</nav>' if links else ""

    # ---------- urls ----------
    def href(self, path):
        return f"{self.base}{path}"

    def abs(self, path):
        return f"{self.url}{self.base}{path}"

    def rung_path(self, r):
        return f"/ladder/{r['slug']}/"

    def article_path(self, a):
        return f"/ladder/{a['rung']}/{a['slug']}/"

    # ---------- analytics ----------
    def tracking_tags(self):
        """Google Search Console verification and Google Analytics 4, each only when set in site.yml."""
        out = []
        ver = str(self.cfg.get("search_console_verification") or "").strip()
        if ver:
            out.append(f'<meta name="google-site-verification" content="{esc(ver)}">')
        ga = str(self.cfg.get("ga4_measurement_id") or "").strip()
        if ga:
            out.append(f'<script async src="https://www.googletagmanager.com/gtag/js?id={esc(ga)}"></script>\n'
                       f'<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}'
                       f'gtag("js",new Date());gtag("config",{json.dumps(ga)});</script>')
        return "".join(t + "\n" for t in out)

    # ---------- layout ----------
    def layout(self, *, title, description, path, body, jsonld, kind="website", updated=None):
        name = self.cfg["name"]
        full_title = title if title == name else f"{title} | {name}"
        nav = "".join(
            f'<a href="{self.href(self.rung_path(r))}">{ROMAN[r["number"]]}. {esc(r["short"])}</a>'
            for r in self.rungs
        )
        modified = f'<meta property="article:modified_time" content="{updated}">' if updated else ""
        ld = "\n".join(
            f'<script type="application/ld+json">{json.dumps(j, ensure_ascii=False)}</script>'
            for j in jsonld
        )
        return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(full_title)}</title>
<meta name="description" content="{esc(description)}">
<link rel="canonical" href="{self.abs(path)}">
<meta property="og:type" content="{kind}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:url" content="{self.abs(path)}">
<meta property="og:site_name" content="{esc(name)}">
<meta name="twitter:card" content="summary">
<meta name="theme-color" content="#140b0a">
{modified}
<link rel="alternate" type="application/rss+xml" title="{esc(name)}" href="{self.href('/feed.xml')}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Anton&family=Oswald:wght@400;500&family=Spectral:ital,wght@0,400;0,600;1,400&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{self.href('/style.css')}">
<link rel="icon" href="{self.href('/seal.svg')}" type="image/svg+xml">
{self.tracking_tags()}{ld}
</head>
<body>
<header class="site-header">
  <div class="wrap header-inner">
    <a class="brand" href="{self.href('/')}" aria-label="9nth Dimension home">{SEAL_SVG}<span class="brand-words"><span class="wordmark">9NTHDIMENSION</span><span class="tagline">ANCIENT TEXTS UNSEALED</span></span></a>
    <div class="header-right"><nav class="top-nav"><a href="{self.href('/ladder/')}">The Ladder</a><a href="{self.href('/articles/')}">Articles</a><a href="{self.href('/about/')}">About</a></nav>{self.socials_html('social-icons')}</div>
  </div>
</header>
<main class="wrap">
{body}
</main>
<footer class="site-footer">
  <div class="wrap">
    <p class="footer-title">Watch the daily videos</p>
    {self.socials_html('social-links')}
    <p class="footer-title">The Spiritual Ladder</p>
    <nav class="rung-nav">{nav}</nav>
    <p class="small">&copy; {self.today.year} 9nth Dimension. Written and reviewed by the 9nth Dimension team.</p>
  </div>
</footer>
</body>
</html>
"""

    def org_ld(self):
        o = {
            "@context": "https://schema.org",
            "@type": "Organization",
            "name": self.cfg["name"],
            "url": self.abs("/"),
            "description": self.cfg["description"],
        }
        same = [s["url"] for s in self.cfg.get("socials", [])] + list(self.cfg.get("same_as") or [])
        if same:
            o["sameAs"] = same
        return o

    def breadcrumbs(self, items):
        return {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": i + 1, "name": n, "item": self.abs(p)}
                for i, (n, p) in enumerate(items)
            ],
        }

    def crumbs_html(self, items):
        parts = [f'<a href="{self.href(p)}">{esc(n)}</a>' for n, p in items[:-1]]
        parts.append(f"<span>{esc(items[-1][0])}</span>")
        return f'<nav class="crumbs" aria-label="Breadcrumb">{" / ".join(parts)}</nav>'

    def write(self, path, text, lastmod=None, in_sitemap=True):
        dest = OUT / path.lstrip("/")
        if path.endswith("/"):
            dest = dest / "index.html"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(text, encoding="utf-8")
        if in_sitemap:
            self.sitemap.append((path, lastmod or self.today))

    def article_card(self, a):
        r = self.rung_by_slug[a["rung"]]
        return (
            f'<li class="entry"><a href="{self.href(self.article_path(a))}">'
            f'<span class="entry-title">{esc(a["title"])}</span>'
            f'<span class="entry-desc">{esc(a["description"])}</span>'
            f'<span class="entry-meta">{esc(r["short"])}, rung {ROMAN[r["number"]]}</span></a></li>'
        )

    def ladder_html(self):
        rows = "".join(
            f'<li class="rung"><a href="{self.href(self.rung_path(r))}">'
            f'<span class="rung-seal" aria-hidden="true">{ROMAN[r["number"]]}</span>'
            f'<span class="rung-text"><span class="rung-name">{esc(r["short"])}</span>'
            f'<span class="rung-line">{esc(r["tagline"])}</span></span></a></li>'
            for r in reversed(self.rungs)
        )
        return f'<ol class="ladder" reversed>{rows}</ol>'

    # ---------- pages ----------
    def build_home(self):
        ladder = self.ladder_html()
        latest = "".join(self.article_card(a) for a in self.articles[:6]) or "<li class='empty'>New articles arrive every other day.</li>"
        body = f"""
<section class="hero">
  
  <h1>What Sunday school skipped</h1>
  <p class="lede">{esc(self.cfg['description'])}</p>
  <a class="button" href="{self.href('/articles/')}">Start reading</a>
  <p class="hero-sub"><a href="{self.href('/ladder/')}">Or find your place on the Spiritual Ladder</a></p>
</section>
<section>
  <h2>Latest unsealed</h2>
  <ul class="index">{latest}</ul>
</section>
<section>
  <h2>The Spiritual Ladder</h2>
  <p class="section-note">Six stages of growth. Every article sits on the rung it helps you climb.</p>
  {ladder}
</section>"""
        site_ld = {
            "@context": "https://schema.org",
            "@type": "WebSite",
            "name": self.cfg["name"],
            "url": self.abs("/"),
            "description": self.cfg["description"],
        }
        self.write("/", self.layout(title=self.cfg["name"], description=self.cfg["description"],
                                    path="/", body=body, jsonld=[site_ld, self.org_ld()]))

    def build_rung(self, r):
        arts = [a for a in self.articles if a["rung"] == r["slug"]]
        i = self.rungs.index(r)
        prev_r = self.rungs[i - 1] if i > 0 else None
        next_r = self.rungs[i + 1] if i + 1 < len(self.rungs) else None
        nav = ""
        if prev_r:
            nav += f'<a class="step" href="{self.href(self.rung_path(prev_r))}">&larr; Rung {prev_r["number"]}: {esc(prev_r["short"])}</a>'
        if next_r:
            nav += f'<a class="step next" href="{self.href(self.rung_path(next_r))}">Rung {next_r["number"]}: {esc(next_r["short"])} &rarr;</a>'
        crumbs = [("Home", "/"), ("The Ladder", "/ladder/"), (f"Rung {r['number']}: {r['short']}", self.rung_path(r))]
        listing = "".join(self.article_card(a) for a in arts) or "<li class='empty'>Articles for this rung are on the way.</li>"
        updated = max([a["updated"] for a in arts] + [as_date(r.get("updated", r["date"]))])
        body = f"""
{self.crumbs_html(crumbs)}
<article class="prose">
  <p class="kicker">Rung {ROMAN[r['number']]} of the Spiritual Ladder</p>
  <h1>{esc(r['title'])}</h1>
  <p class="updated">Last updated {updated:%B %-d, %Y}</p>
  {md_to_html(r['body_md'])}
</article>
<section>
  <h2>Questions on this rung</h2>
  <ul class="index">{listing}</ul>
</section>
<nav class="steps">{nav}</nav>"""
        ld = [self.breadcrumbs(crumbs), {
            "@context": "https://schema.org", "@type": "Article",
            "headline": r["title"], "description": r["description"],
            "datePublished": str(r["date"]), "dateModified": str(updated),
            "author": {"@type": "Organization", "name": "9nth Dimension team", "url": self.abs("/about/")},
            "publisher": self.org_ld(), "mainEntityOfPage": self.abs(self.rung_path(r)),
        }]
        self.write(self.rung_path(r), self.layout(title=r["title"], description=r["description"],
                   path=self.rung_path(r), body=body, jsonld=ld, kind="article", updated=updated), lastmod=updated)

    def build_article(self, a):
        r = self.rung_by_slug[a["rung"]]
        i = self.rungs.index(r)
        next_r = self.rungs[i + 1] if i + 1 < len(self.rungs) else None
        crumbs = [("Home", "/"), ("The Ladder", "/ladder/"),
                  (f"Rung {r['number']}: {r['short']}", self.rung_path(r)), (a["title"], self.article_path(a))]
        faq = a.get("faq") or []
        faq_html = ""
        if faq:
            items = "".join(f"<h3>{esc(q['q'])}</h3>{md_to_html(q['a'])}" for q in faq)
            faq_html = f'<section class="faq"><h2>Frequently asked questions</h2>{items}</section>'
        related = [x for x in self.articles if x["rung"] == a["rung"] and x is not a][:3]
        related_html = ""
        if related:
            related_html = f'<section><h2>More on this rung</h2><ul class="index">{"".join(self.article_card(x) for x in related)}</ul></section>'
        up = ""
        if next_r:
            up = (f'<aside class="next-step"><p class="kicker">Your next step up</p>'
                  f'<a href="{self.href(self.rung_path(next_r))}">{esc(next_r["title"])}</a></aside>')
        body = f"""
{self.crumbs_html(crumbs)}
<article class="prose">
  <p class="kicker"><a href="{self.href(self.rung_path(r))}">{esc(r['short'])}, rung {ROMAN[r['number']]}</a></p>
  <h1>{esc(a['title'])}</h1>
  <p class="updated">By the 9nth Dimension team · Published {a['date']:%B %-d, %Y} · Last updated {a['updated']:%B %-d, %Y}</p>
  {md_to_html(a['body_md'])}
  {faq_html}
</article>
{up}
{related_html}"""
        ld = [self.breadcrumbs(crumbs), {
            "@context": "https://schema.org", "@type": "Article",
            "headline": a["title"], "description": a["description"],
            "datePublished": str(a["date"]), "dateModified": str(a["updated"]),
            "author": {"@type": "Organization", "name": "9nth Dimension team", "url": self.abs("/about/")},
            "publisher": self.org_ld(), "mainEntityOfPage": self.abs(self.article_path(a)),
            "about": r["title"],
        }]
        if faq:
            ld.append({
                "@context": "https://schema.org", "@type": "FAQPage",
                "mainEntity": [{"@type": "Question", "name": q["q"],
                                "acceptedAnswer": {"@type": "Answer", "text": q["a"]}} for q in faq],
            })
        self.write(self.article_path(a), self.layout(title=a["title"], description=a["description"],
                   path=self.article_path(a), body=body, jsonld=ld, kind="article", updated=a["updated"]),
                   lastmod=a["updated"])

    def build_pages(self):
        for p in self.pages:
            path = p.get("path", f"/{p['slug']}/")
            crumbs = [("Home", "/"), (p["title"], path)]
            extra = ""
            if p["slug"] == "ladder":
                extra = self.ladder_html()
            updated = as_date(p.get("updated", p.get("date", self.today)))
            body = f"""
{self.crumbs_html(crumbs)}
<article class="prose">
  <h1>{esc(p['title'])}</h1>
  <p class="updated">Last updated {updated:%B %-d, %Y}</p>
  {md_to_html(p['body_md'])}
  {extra}
</article>"""
            self.write(path, self.layout(title=p["title"], description=p["description"], path=path,
                       body=body, jsonld=[self.breadcrumbs(crumbs), self.org_ld()]), lastmod=updated)

    def build_index(self):
        cards = "".join(self.article_card(a) for a in self.articles) or "<li class='empty'>New articles arrive every other day.</li>"
        body = f"""
{self.crumbs_html([("Home", "/"), ("Articles", "/articles/")])}
<h1>All articles</h1>
<p class="lede">Every article answers one real question from someone climbing the Spiritual Ladder.</p>
<ul class="index">{cards}</ul>"""
        self.write("/articles/", self.layout(title="All articles", description="Every 9nth Dimension article, newest first.",
                   path="/articles/", body=body, jsonld=[self.org_ld()]))

    def build_stats(self):
        """articles.json: the feed the SEO dashboard on rogeniecordero.com reads."""
        backlog_path = CONTENT / "backlog.yml"
        backlog = yaml.safe_load(backlog_path.read_text()) if backlog_path.exists() else []
        todo = [b for b in backlog if b.get("status") == "todo"]
        data = {
            "generated": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
            "site": self.abs("/"),
            "cadence_days": 2,
            "rungs": [{"number": r["number"], "slug": r["slug"], "name": r["short"],
                       "url": self.abs(self.rung_path(r))} for r in self.rungs],
            "articles": [{
                "title": a["title"], "slug": a["slug"], "rung": a["rung"],
                "rung_number": self.rung_by_slug[a["rung"]]["number"],
                "date": str(a["date"]), "updated": str(a["updated"]),
                "url": self.abs(self.article_path(a)),
                "words": len(re.sub(r"<[^>]+>", " ", a["body_md"]).split()),
                "faq": len(a.get("faq") or []),
            } for a in self.articles],
            "backlog": {
                "todo": len(todo),
                "skipped": sum(1 for b in backlog if b.get("status") == "skip"),
                "next": [{"q": b["q"], "rung": b["rung"]} for b in todo[:5]],
            },
        }
        (OUT / "articles.json").write_text(json.dumps(data, indent=1, ensure_ascii=False))

    def build_files(self):
        self.build_stats()
        robots ="\n\n".join(f"User-agent: {b}\nAllow: /" for b in AI_AND_SEARCH_BOTS)
        robots += f"\n\nUser-agent: *\nAllow: /\n\nSitemap: {self.abs('/sitemap.xml')}\n"
        (OUT / "robots.txt").write_text(robots)

        urls = "\n".join(
            f"  <url><loc>{self.abs(p)}</loc><lastmod>{d}</lastmod></url>" for p, d in self.sitemap
        )
        (OUT / "sitemap.xml").write_text(
            f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{urls}\n</urlset>\n')

        items = "\n".join(
            f"<item><title>{esc(a['title'])}</title><link>{self.abs(self.article_path(a))}</link>"
            f"<guid>{self.abs(self.article_path(a))}</guid><pubDate>{dt.datetime.combine(a['date'], dt.time(12)).strftime('%a, %d %b %Y %H:%M:%S +0000')}</pubDate>"
            f"<description>{esc(a['description'])}</description></item>"
            for a in self.articles[:30]
        )
        (OUT / "feed.xml").write_text(
            f'<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0"><channel><title>{esc(self.cfg["name"])}</title>'
            f'<link>{self.abs("/")}</link><description>{esc(self.cfg["description"])}</description>\n{items}\n</channel></rss>\n')

        lines = [f"# {self.cfg['name']}", "", f"> {self.cfg['description']}", "",
                 "## The Spiritual Ladder", ""]
        lines += [f"- [{r['title']}]({self.abs(self.rung_path(r))}): {r['description']}" for r in self.rungs]
        lines += ["", "## Articles", ""]
        lines += [f"- [{a['title']}]({self.abs(self.article_path(a))}): {a['description']}" for a in self.articles]
        (OUT / "llms.txt").write_text("\n".join(lines) + "\n")

        (OUT / ".nojekyll").write_text("")
        if self.cfg.get("custom_domain"):
            (OUT / "CNAME").write_text(self.cfg["custom_domain"] + "\n")
        shutil.copy(STATIC / "style.css", OUT / "style.css")
        (OUT / "seal.svg").write_text(SEAL_SVG.replace(' class="seal"', ' xmlns="http://www.w3.org/2000/svg"'))
        notfound = self.layout(title="Page not found", description="This page does not exist.", path="/404.html",
                               body=f'<h1>Page not found</h1><p><a href="{self.href("/ladder/")}">Start at the Spiritual Ladder</a>.</p>',
                               jsonld=[])
        (OUT / "404.html").write_text(notfound)

    def build(self):
        if OUT.exists():
            shutil.rmtree(OUT)
        OUT.mkdir()
        self.build_home()
        self.build_pages()
        for r in self.rungs:
            self.build_rung(r)
        for a in self.articles:
            self.build_article(a)
        self.build_index()
        self.build_files()
        print(f"Built {len(self.rungs)} rungs, {len(self.articles)} articles, {len(self.pages)} pages into docs/")


if __name__ == "__main__":
    Site().build()
