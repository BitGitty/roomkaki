"""Builds roomkaki.com/tools/: one page per tool from tools/src/<slug>.html + tools/index.html.
Every page gets the same header, tabs, disclaimer footer and analytics. Run after editing any tool source.
  python tools/build_tools.py
"""
import html
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SITE = "https://roomkaki.com"

TOOLS = [  # (slug, icon, title, one-line description) — order = order on the Tools page
    ("commute", "🚇", "Commute checker", "From your room's MRT to your work's MRT: line changes and rough travel time."),
    ("true-cost", "🧮", "True monthly cost", "Rent + bills + transport + food. Compare up to 3 rooms honestly."),
    ("stamp-duty", "🧾", "Tenancy stamp duty", "How much stamp duty your rental agreement needs (IRAS formula)."),
    ("hdb-room-check", "🏠", "HDB room-rental check", "Is this HDB room set-up allowed? 6 quick questions."),
    ("scam-check", "🛡️", "Scam-risk check", "Answer 8 yes/no questions about an ad before you pay anything."),
    ("bill-split", "💡", "Bill splitter", "Split a PUB bill fairly by people, days stayed and aircon use."),
    ("move-out-dates", "📅", "Move-out & deposit dates", "Your last day from the notice period, and when your deposit is due."),
    ("rent-budget", "💰", "Rent budget", "How much rent fits your salary, after sending money home."),
    ("tenancy-agreement", "📝", "Simple tenancy agreement", "Fill in the blanks, print a plain-English room rental agreement."),
    ("area-finder", "🗺️", "Area finder", "Your budget + work MRT line → areas worth looking at."),
]

HEAD = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} · RoomKaki</title>
<meta name="description" content="{desc}">
<link rel="stylesheet" href="/styles.css">
<link rel="stylesheet" href="/tools/tools.css">
<link rel="canonical" href="{site}/tools/{path}">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🏠</text></svg>">
<meta property="og:title" content="{title} · RoomKaki">
<meta property="og:description" content="{desc}">
<meta property="og:image" content="{site}/og.png">
</head>
<body>
<header>
  <a class="logo" href="/"><b>Room</b>Kaki<span>SINGAPORE</span></a>
  <div class="grow"></div>
  <a class="cta" href="/" style="text-decoration:none">Find a room</a>
</header>
<nav class="tabs" aria-label="Sections"><a href="/">🏠 Rooms</a><a href="/blog/">📖 Guides</a><a href="/tools/" class="on">🧰 Tools</a><a href="/market/">📊 Market</a></nav>
<main class="tool">
"""

FOOT = """
</main>
<footer>
  <p><b>RoomKaki</b> — free tools for renting a room in Singapore</p>
  <p>Results are a guide, not legal or financial advice. Rules can change — check the official site named in each tool.</p>
  <p><a href="/tools/">All tools</a> · <a href="/blog/">Guides</a> · <a href="/">Rooms</a></p>
</footer>
<script>/* first-party analytics */(function(){try{fetch("https://uumiwuvbxzmtxuwmutis.supabase.co/rest/v1/rpc/track_view",{method:"POST",headers:{"apikey":"sb_publishable_E2ECaIgR-2fLWAEeDfVnMA_5_balO9b","Authorization":"Bearer sb_publishable_E2ECaIgR-2fLWAEeDfVnMA_5_balO9b","Content-Type":"application/json"},body:JSON.stringify({p_site:"roomkaki",p_path:location.pathname+location.search,p_ref:document.referrer||null}),keepalive:true}).catch(function(){})}catch(e){}})();</script>
</body>
</html>
"""


def build() -> int:
    built = 0
    for slug, icon, title, desc in TOOLS:
        src = ROOT / "src" / f"{slug}.html"
        if not src.exists():
            continue
        body = src.read_text(encoding="utf-8")
        page = HEAD.format(title=html.escape(title), desc=html.escape(desc), site=SITE, path=f"{slug}.html") + \
            f'<p class="crumb"><a href="/tools/">← All tools</a></p>\n<h1>{icon} {html.escape(title)}</h1>\n' + \
            f'<p class="lead">{html.escape(desc)}</p>\n' + body + FOOT
        (ROOT / f"{slug}.html").write_text(page, encoding="utf-8")
        built += 1
    cards = "\n".join(
        f'<a class="toolcard" href="/tools/{s}.html"><span class="ti">{i}</span><b>{html.escape(t)}</b>'
        f'<span>{html.escape(d)}</span></a>'
        for s, i, t, d in TOOLS if (ROOT / "src" / f"{s}.html").exists())
    index = HEAD.format(title="Free renting tools", desc="Free tools for renting a room in Singapore: commute, "
                        "stamp duty, scam check, bill splitting and more.", site=SITE, path="") + \
        '<h1>🧰 Free renting tools</h1>\n<p class="lead">Quick, free tools for renting a room in Singapore. ' \
        'No sign-up. Nothing you type is saved.</p>\n' + f'<div class="toolgrid">\n{cards}\n</div>' + FOOT
    (ROOT / "index.html").write_text(index, encoding="utf-8")
    sm = ROOT.parent / "sitemap.xml"
    xml = re.sub(r"\s*<url><loc>https://roomkaki\.com/tools/[^<]*</loc></url>", "", sm.read_text(encoding="utf-8"))
    entries = [f"<url><loc>{SITE}/tools/</loc></url>"] + [
        f"<url><loc>{SITE}/tools/{s}.html</loc></url>" for s, *_ in TOOLS if (ROOT / "src" / f"{s}.html").exists()]
    sm.write_text(xml.replace("</urlset>", "  " + "\n  ".join(entries) + "\n</urlset>"), encoding="utf-8")
    print(f"tools build: {built} tool pages + index, sitemap updated")
    return 0


if __name__ == "__main__":
    raise SystemExit(build())
