"""RoomKaki blog builder: blog/posts/*.json -> blog/<slug>.html + blog/index.html,
and refreshes sitemap.xml with blog URLs. Idempotent; run after blog_drip.py.

Post JSON: {slug, title_en, title_my, summary_en, body_en (HTML), body_my (HTML),
            my_approved (bool), date}
Burmese sections render ONLY when my_approved is true (owner reviews every Burmese line).
"""
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
POSTS = ROOT / "blog" / "posts"
BLOG = ROOT / "blog"
SITE = "https://roomkaki.com"

PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} · RoomKaki</title>
<meta name="description" content="{desc}">
<link rel="stylesheet" href="../styles.css">
<link rel="canonical" href="{site}/blog/{slug}.html">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🏠</text></svg>">
<meta property="og:type" content="article">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{site}/blog/{slug}.html">
<meta property="og:image" content="{site}/og.png">
<script type="application/ld+json">{ld}</script>
<style>
.post{{max-width:720px;margin:0 auto;padding:24px 16px 60px}}
.post h1{{font-size:1.6rem;line-height:1.3;margin:10px 0 6px}}
.post .date{{color:var(--mut);font-size:.85rem;margin-bottom:20px}}
.post h2{{font-size:1.15rem;margin:26px 0 8px}}
.post p,.post li{{font-size:1rem;line-height:1.7}}
.post ul{{padding-left:22px}}
.post .my-section{{border-top:2px solid var(--line);margin-top:34px;padding-top:20px}}
.ctabox{{background:var(--card);border:1.5px solid var(--brand);border-radius:16px;
padding:18px;margin:30px 0 0;text-align:center}}
.ctabox a{{text-decoration:none}}
</style>
</head>
<body>
<header>
  <a class="logo" href="../"><b>Room</b>Kaki<span>SINGAPORE</span></a>
  <div class="grow"></div>
  <a class="cta" href="../" style="text-decoration:none">Find a room</a>
</header>
<nav class="tabs" aria-label="Sections"><a href="/">🏠 Rooms</a><a href="/blog/" class="on">📖 Guides</a><a href="/tools/">🧰 Tools</a><a href="/market/">📊 Market</a></nav>
<article class="post">
<h1>{title}</h1>
<div class="date">{date} · RoomKaki guides</div>
{body_en}
{my_block}
<div class="ctabox"><b>Looking for a room in Singapore?</b><br>
Browse free listings, or post your room in 2 minutes — no agent fees.<br><br>
<a class="cta" href="../">Open RoomKaki →</a></div>
</article>
<footer>
  <p><b>RoomKaki</b> — rooms you can trust · Singapore</p>
  <p><a href="./">More guides</a> · <a href="../">Listings</a></p>
</footer>
<script src="/track.js" defer></script>
</body>
</html>
"""

INDEX_ROW = """<a class="bloglink" href="{slug}.html"><b>{title}</b><br><span>{date} · {summary}</span></a>"""

INDEX = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Guides · RoomKaki</title>
<meta name="description" content="Plain-language guides for renting a room in Singapore — scams, HDB rules, deposits, tenant rights. English + Burmese.">
<link rel="stylesheet" href="../styles.css">
<link rel="canonical" href="{site}/blog/">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🏠</text></svg>">
<style>
.bloglist{{max-width:720px;margin:0 auto;padding:24px 16px 60px}}
.bloglink{{display:block;background:var(--card);border:1px solid var(--line);border-radius:14px;
padding:16px 18px;margin-bottom:12px;text-decoration:none;box-shadow:var(--shadow)}}
.bloglink span{{color:var(--mut);font-size:.88rem}}
</style>
</head>
<body>
<header>
  <a class="logo" href="../"><b>Room</b>Kaki<span>SINGAPORE</span></a>
  <div class="grow"></div>
  <a class="cta" href="../" style="text-decoration:none">Find a room</a>
</header>
<nav class="tabs" aria-label="Sections"><a href="/">🏠 Rooms</a><a href="/blog/" class="on">📖 Guides</a><a href="/tools/">🧰 Tools</a><a href="/market/">📊 Market</a></nav>
<div class="bloglist">
<h1>Renting guides</h1>
<p style="color:var(--mut)">Plain-language guides for renting a room in Singapore. New guide every day.</p>
{rows}
</div>
<footer><p><b>RoomKaki</b> — rooms you can trust · Singapore</p></footer>
</body>
</html>
"""


def burmese_ok(s: str) -> bool:
    """Block Zawgyi-encoded or un-normalized Burmese from going live (renders as garbage)."""
    import unicodedata
    if any(0x1060 <= ord(c) <= 0x1097 for c in s):   # Zawgyi stacked-form range
        return False
    return unicodedata.normalize("NFC", s) == s


def build() -> int:
    posts = []
    for f in POSTS.glob("*.json"):
        p = json.loads(f.read_text(encoding="utf-8"))
        posts.append(p)
    posts.sort(key=lambda p: p["date"], reverse=True)

    for p in posts:
        my_block = ""
        if p.get("my_approved") and p.get("body_my") and not burmese_ok(p["body_my"] + p.get("title_my", "")):
            print(f"blog build: BLOCKED Burmese for {p['slug']} (Zawgyi or not NFC)")
        elif p.get("my_approved") and p.get("body_my"):
            my_block = (f'<div class="my-section" lang="my"><h2>{html.escape(p["title_my"])}</h2>'
                        f'{p["body_my"]}</div>')
        (BLOG / f"{p['slug']}.html").write_text(PAGE.format(
            title=html.escape(p["title_en"]), desc=html.escape(p["summary_en"]),
            slug=p["slug"], date=p["date"], body_en=p["body_en"], my_block=my_block,
            site=SITE, ld=json.dumps({
                "@context": "https://schema.org", "@type": "Article", "headline": p["title_en"],
                "description": p["summary_en"], "datePublished": p["date"], "dateModified": p["date"],
                "inLanguage": ["en", "my"] if my_block else "en", "url": f"{SITE}/blog/{p['slug']}.html",
                "image": f"{SITE}/og.png", "author": {"@type": "Organization", "name": "RoomKaki", "url": SITE},
                "publisher": {"@type": "Organization", "name": "RoomKaki", "url": SITE},
                "citation": [f["source"] for f in p.get("facts_checked", []) if f.get("source", "").startswith("http")][:8],
            }, ensure_ascii=False).replace("</", "<\\/")), encoding="utf-8")

    rows = "\n".join(INDEX_ROW.format(slug=p["slug"], title=html.escape(p["title_en"]),
                                      date=p["date"], summary=html.escape(p["summary_en"]))
                     for p in posts)
    (BLOG / "index.html").write_text(INDEX.format(rows=rows, site=SITE), encoding="utf-8")

    # homepage "latest guides" feed
    (BLOG / "latest.json").write_text(json.dumps(
        [{"slug": p["slug"], "title_en": p["title_en"], "summary_en": p["summary_en"], "date": p["date"]}
         for p in posts], ensure_ascii=False, indent=1), encoding="utf-8")

    # sitemap: root entry + blog pages (regenerate the blog section idempotently)
    sm = ROOT / "sitemap.xml"
    xml = sm.read_text(encoding="utf-8")
    xml = re.sub(r"\s*<url><loc>https://roomkaki\.com/blog/[^<]*</loc></url>", "", xml)
    entries = [f"<url><loc>{SITE}/blog/</loc></url>"] + \
              [f"<url><loc>{SITE}/blog/{p['slug']}.html</loc></url>" for p in posts]
    xml = xml.replace("</urlset>", "  " + "\n  ".join(entries) + "\n</urlset>")
    sm.write_text(xml, encoding="utf-8")
    print(f"blog build: {len(posts)} posts rendered, sitemap updated")
    return 0


if __name__ == "__main__":
    raise SystemExit(build())
