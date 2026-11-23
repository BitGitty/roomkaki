"""RoomKaki Market data: HDB rents + resale prices from official data.gov.sg datasets -> /market pages.
  python market/build_market.py            # download fresh data, build pages
  python market/build_market.py --no-fetch # rebuild from market/raw/*.csv
Sources (HDB, via data.gov.sg): Renting Out of Flats d_c9f57187485a850908655db0e8cfe651 (owner-declared, indicative);
Resale flat prices d_8b84c4ee58e3cfc0ece0d773c8ca6abc. Run monthly by .github/workflows/market.yml.
"""
import csv
import html
import json
import re
import statistics as st
import sys
import time
import urllib.error
import urllib.request
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "raw"
SITE = "https://roomkaki.com"
RENT_ID, RESALE_ID = "d_c9f57187485a850908655db0e8cfe651", "d_8b84c4ee58e3cfc0ece0d773c8ca6abc"
PRIVATE_ID = "d_8e4c50283fb7052a391dfb746a05c853"   # URA Private Residential Rental Index (2009-Q1 = 100), quarterly
TYPES = ["3-ROOM", "4-ROOM", "5-ROOM", "EXECUTIVE"]
BEDROOMS = {"3-ROOM": 2, "4-ROOM": 3, "5-ROOM": 3, "EXECUTIVE": 3}
MIN_N = 5          # don't publish a median from fewer than 5 records


UA = {"User-Agent": "Mozilla/5.0 (compatible; RoomKaki-market/1.0; +https://roomkaki.com)"}  # default urllib UA gets 403


def get(url, tries=6):
    """data.gov.sg rate-limits anonymous calls (429): back off 20s, 40s, 60s… instead of failing the monthly job."""
    for n in range(tries):
        try:
            return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120).read()
        except urllib.error.HTTPError as e:
            if e.code != 429 or n == tries - 1:
                raise
            time.sleep(20 * (n + 1))


def fetch(ds):
    api = "https://api-open.data.gov.sg/v1/public/api/datasets/" + ds
    get(api + "/initiate-download")
    for _ in range(20):
        time.sleep(3)
        d = json.loads(get(api + "/poll-download"))["data"]
        if d.get("url"):
            RAW.mkdir(exist_ok=True)
            data = get(d["url"])
            if data.count(b"\n") < 10:
                raise RuntimeError(f"{ds}: download looks empty")
            (RAW / f"{ds}.csv").write_bytes(data)
            return
    raise RuntimeError(f"download of {ds} never became ready")


def months_back(latest, n):
    y, m = map(int, latest.split("-"))
    out = []
    for _ in range(n):
        out.append(f"{y:04d}-{m:02d}")
        m -= 1
        if m == 0:
            y, m = y - 1, 12
    return out[::-1]


def slug(town):
    return re.sub(r"[^a-z0-9]+", "-", town.lower()).strip("-")


def title(town):
    return town.title().replace("/", " / ")


def med(xs):
    return round(st.median(xs)) if len(xs) >= MIN_N else None


def pct(a, b):
    return round((a - b) / b * 100, 1) if a and b else None


def load():
    rent = list(csv.DictReader(open(RAW / f"{RENT_ID}.csv", encoding="utf-8")))
    sale = list(csv.DictReader(open(RAW / f"{RESALE_ID}.csv", encoding="utf-8")))
    return rent, sale


def analyse(rent, sale):
    r_last = max(r["rent_approval_date"] for r in rent)
    s_last = max(s["month"] for s in sale)
    r12, r24 = months_back(r_last, 12), months_back(r_last, 24)
    s12, s24 = months_back(s_last, 12), months_back(s_last, 24)
    R, S, RS, SS = defaultdict(list), defaultdict(list), defaultdict(list), defaultdict(list)
    for r in rent:
        t, f, mo, v = r["town"], r["flat_type"], r["rent_approval_date"], float(r["monthly_rent"])
        if f not in TYPES:
            continue
        if mo in r12: R[(t, f, "now")].append(v)
        elif mo in r24: R[(t, f, "prev")].append(v)
        if mo in r24: RS[(t, f, mo)].append(v); RS[("ALL", f, mo)].append(v)
    for s in sale:
        t, f, mo, v = s["town"], s["flat_type"].replace(" ", "-"), s["month"], float(s["resale_price"])
        if f not in TYPES:
            continue
        if mo in s12: S[(t, f, "now")].append(v)
        elif mo in s24: S[(t, f, "prev")].append(v)
        if mo in s24: SS[(t, f, mo)].append(v); SS[("ALL", f, mo)].append(v)
    towns = sorted({r["town"] for r in rent} | {s["town"] for s in sale})
    out = {"rent_latest": r_last, "resale_latest": s_last, "towns": {}, "national": {}}
    for t in towns + ["ALL"]:
        row = {}
        for f in TYPES:
            if t == "ALL":
                rn = [v for k, vs in R.items() if k[1] == f and k[2] == "now" for v in vs]
                rp = [v for k, vs in R.items() if k[1] == f and k[2] == "prev" for v in vs]
                sn = [v for k, vs in S.items() if k[1] == f and k[2] == "now" for v in vs]
                sp = [v for k, vs in S.items() if k[1] == f and k[2] == "prev" for v in vs]
            else:
                rn, rp, sn, sp = R[(t, f, "now")], R[(t, f, "prev")], S[(t, f, "now")], S[(t, f, "prev")]
            rm, sm = med(rn), med(sn)
            row[f] = {"rent": rm, "rent_n": len(rn), "rent_yoy": pct(rm, med(rp)),
                      "room_est": round(rm / BEDROOMS[f] / 10) * 10 if rm else None,
                      "resale": sm, "resale_n": len(sn), "resale_yoy": pct(sm, med(sp)),
                      "rent_series": [med(RS[(t, f, m)]) for m in r24],
                      "resale_series": [med(SS[(t, f, m)]) for m in s24]}
        if t == "ALL":
            out["national"] = row
        else:
            out["towns"][t] = row
    out["rent_months"], out["resale_months"] = r24, s24
    return out


# ---------- rendering ----------
HEAD = """<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} · RoomKaki</title><meta name="description" content="{desc}">
<link rel="stylesheet" href="/styles.css"><link rel="stylesheet" href="/tools/tools.css">
<link rel="canonical" href="{site}/market/{path}">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🏠</text></svg>">
<meta property="og:title" content="{title} · RoomKaki"><meta property="og:description" content="{desc}">
<meta property="og:image" content="{site}/og.png">
<script type="application/ld+json">{ld}</script>
</head><body>
<header><a class="logo" href="/"><b>Room</b>Kaki<span>SINGAPORE</span></a><div class="grow"></div>
<a class="cta" href="/" style="text-decoration:none">Find a room</a></header>
<nav class="tabs" aria-label="Sections"><a href="/">🏠 Rooms</a><a href="/blog/">📖 Guides</a><a href="/tools/">🧰 Tools</a><a href="/market/" class="on">📊 Market</a></nav>
<main class="tool">
"""
FOOT = """
<p class="note">Source: HDB via data.gov.sg — "Renting Out of Flats" (rents declared by flat owners when renting out a
whole flat; indicative) and "Resale flat prices". Medians of the last 12 months; change = vs the 12 months before.
*Per bedroom = whole-flat median rent ÷ bedrooms. Renting a single room from a live-in owner is usually cheaper than this — see room asking prices in our Area finder tool. Updated monthly.</p>
</main>
<footer><p><b>RoomKaki</b> — free market data for renting in Singapore</p>
<p><a href="/market/">All towns</a> · <a href="/tools/">Tools</a> · <a href="/">Rooms</a></p></footer>
<script>/* first-party analytics */(function(){try{fetch("https://uumiwuvbxzmtxuwmutis.supabase.co/rest/v1/rpc/track_view",{method:"POST",headers:{"apikey":"sb_publishable_E2ECaIgR-2fLWAEeDfVnMA_5_balO9b","Authorization":"Bearer sb_publishable_E2ECaIgR-2fLWAEeDfVnMA_5_balO9b","Content-Type":"application/json"},body:JSON.stringify({p_site:"roomkaki",p_path:location.pathname+location.search,p_ref:document.referrer||null}),keepalive:true}).catch(function(){})}catch(e){}})();</script>
</body></html>
"""


def note_panel():
    """Monthly market note: key figures QUOTED from a published report, credited + linked (never scraped).
    Update market/notes/latest.json each month after reading the new report."""
    f = ROOT / "notes" / "latest.json"
    if not f.exists():
        return ""
    n = json.loads(f.read_text(encoding="utf-8"))
    pts = "".join(f"<li>{html.escape(p)}</li>" for p in n["points"])
    return (f"<div class='panelbox'><p class='fld' style='margin-top:0'>📰 Market note — {html.escape(n['month'])}</p>"
            f"<ul>{pts}</ul><p class='note'>{html.escape(n['room_note'])}</p>"
            f"<p class='note'>Figures quoted from <a href='{html.escape(n['source_url'])}' rel='noopener' target='_blank'>"
            f"{html.escape(n['source_name'])}</a> (checked {html.escape(n['checked'])}).</p></div>")


def private_panel():
    """Condo (non-landed) rent index by region: latest quarter, change vs 4 quarters earlier, 12-quarter trend."""
    f = RAW / f"{PRIVATE_ID}.csv"
    if not f.exists():
        return ""
    rows = [r for r in csv.DictReader(open(f, encoding="utf-8")) if r["property_type"] == "Non-Landed"]
    by = defaultdict(dict)
    for r in rows:
        try:
            by[r["locality"]][r["quarter"]] = float(r["index"])
        except ValueError:
            continue
    qs = sorted({q for d in by.values() for q in d})
    last12, latest = qs[-12:], qs[-1]
    prev = qs[-5] if len(qs) >= 5 else None
    names = {"Core Central Region": "Core Central (prime: Orchard, CBD)", "Rest of Central Region": "Rest of Central",
             "Outside Central Region": "Outside Central (suburbs)", "Whole Island": "Whole island"}
    trs = ""
    for loc in ["Whole Island", "Outside Central Region", "Rest of Central Region", "Core Central Region"]:
        d = by.get(loc, {})
        if latest in d:
            trs += f"<tr><td>{names[loc]}</td><td>{d[latest]:.1f}</td><td>{chg(pct(d[latest], d.get(prev)))}</td></tr>"
    wi = by.get("Whole Island") or by.get("Outside Central Region", {})
    series = [wi.get(q) for q in last12]
    return (f"<div class='panelbox'><p class='fld' style='margin-top:0'>Condo rents (private, non-landed) — URA rental index</p>"
            f"<div style='overflow-x:auto'><table class='tt'><tr><th>Region</th><th>Index {latest}</th><th>vs a year ago</th></tr>"
            f"{trs}</table></div><p class='fld'>Whole-island condo rent index, last 12 quarters</p>"
            f"{spark_idx(series, last12)}<p class='note'>Index: 2009-Q1 = 100 (URA via data.gov.sg). It shows how rents "
            f"move, not a dollar amount — e.g. 174 means rents are about 74% higher than in early 2009.</p></div>")


def spark_idx(series, labels):
    s = spark([round(v * 100) if v else None for v in series], labels, "#005ec4")
    return re.sub(r"S\$([\d,]+)", lambda m: f"{int(m.group(1).replace(',', '')) / 100:.0f}", s)


def dataset_ld(name, desc, path, d, place="Singapore"):
    """schema.org Dataset — lets search engines and AI assistants cite RoomKaki as the source of these figures."""
    return json.dumps({
        "@context": "https://schema.org", "@type": "Dataset", "name": name, "description": desc,
        "url": f"{SITE}/market/{path}", "creator": {"@type": "Organization", "name": "RoomKaki", "url": SITE},
        "isBasedOn": [f"https://data.gov.sg/datasets/{RENT_ID}/view", f"https://data.gov.sg/datasets/{RESALE_ID}/view"],
        "license": "https://data.gov.sg/open-data-licence", "spatialCoverage": {"@type": "Place", "name": place},
        "temporalCoverage": f"{d['rent_months'][0]}/{d['rent_latest']}", "dateModified": d["rent_latest"],
        "variableMeasured": ["median monthly HDB rent", "median HDB resale price"], "inLanguage": "en"},
        ensure_ascii=False).replace("</", "<\\/")


def money(v):
    return f"S${v:,.0f}" if v else "–"


def chg(v):
    if v is None:
        return '<span class="mut">–</span>'
    col = "#c0392b" if v > 0 else "#0a7a3d" if v < 0 else "var(--mut)"
    return f'<span style="color:{col};font-weight:700">{"+" if v > 0 else ""}{v}%</span>'


def spark(series, months, color="#0d9488"):
    raw = [(i, v) for i, v in enumerate(series) if v]
    if len(raw) < 4:
        return '<p class="mut">Not enough data for a trend.</p>'
    # 3-month rolling average: monthly medians move in S$100 steps and look jumpier than the real trend
    pts = [(i, sum(v for _, v in raw[max(0, k - 2):k + 1]) / len(raw[max(0, k - 2):k + 1])) for k, (i, _) in enumerate(raw)]
    W, H, P = 640, 180, 28
    lo, hi = min(v for _, v in pts), max(v for _, v in pts)
    mid, need = (lo + hi) / 2, 0.2 * sum(v for _, v in pts) / len(pts)   # show at least a ±10% band so noise stays small
    if hi - lo < need:
        lo, hi = mid - need / 2, mid + need / 2
    span = (hi - lo) or 1
    xy = [(P + i * (W - 2 * P) / (len(series) - 1), H - P - (v - lo) / span * (H - 2 * P)) for i, v in pts]
    path = " ".join(f"{'M' if k == 0 else 'L'}{x:.1f},{y:.1f}" for k, (x, y) in enumerate(xy))
    lab = lambda v: f"S${v/1000:.0f}k" if v >= 10000 else f"S${v:,.0f}"           # noqa: E731
    return (f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="trend" style="width:100%;height:auto">'
            f'<path d="{path}" fill="none" stroke="{color}" stroke-width="3" stroke-linejoin="round"/>'
            f'<text x="{P}" y="14" font-size="12" fill="currentColor" opacity=".6">{lab(hi)}</text>'
            f'<text x="{P}" y="{H-6}" font-size="12" fill="currentColor" opacity=".6">{lab(lo)}</text>'
            f'<text x="{W-P}" y="{H-6}" font-size="12" text-anchor="end" fill="currentColor" opacity=".6">'
            f'{months[0]} → {months[-1]}</text></svg>')


def table(row):
    trs = "".join(
        f"<tr><td><b>{f.title()}</b></td><td>{money(d['rent'])}<br><small class='mut'>{d['rent_n']} rentals</small></td>"
        f"<td>{chg(d['rent_yoy'])}</td><td>{money(d['room_est'])}</td><td>{money(d['resale'])}<br>"
        f"<small class='mut'>{d['resale_n']} sales</small></td><td>{chg(d['resale_yoy'])}</td></tr>"
        for f, d in row.items() if d["rent"] or d["resale"])
    return ("<div style='overflow-x:auto'><table class='tt'><tr><th>Flat</th><th>Median rent /mo</th><th>Rent change</th>"
            f"<th>Per bedroom*</th><th>Median resale</th><th>Price change</th></tr>{trs}</table></div>")


def render(d):
    out_dir = ROOT
    nat = d["national"]
    towns = d["towns"]
    rows = sorted(((t, r["4-ROOM"]) for t, r in towns.items() if r["4-ROOM"]["rent"]), key=lambda x: x[1]["rent"])
    town_list = "".join(
        f"<tr><td><a href='/market/{slug(t)}.html'>{title(t)}</a></td><td>{money(x['rent'])}</td>"
        f"<td>{chg(x['rent_yoy'])}</td><td>{money(x['room_est'])}</td></tr>" for t, x in rows)
    n4 = nat["4-ROOM"]
    idx = HEAD.format(title="HDB rent & resale prices by town", path="",
                      ld=dataset_ld("HDB rent and resale prices by town, Singapore",
                                    "Median HDB whole-flat rents and resale prices for every Singapore town, from official HDB data.", "", d),
                      desc=f"Median HDB rents and resale prices for every Singapore town, from official HDB data. "
                           f"Updated to {d['rent_latest']}.", site=SITE)
    idx += (f"<h1>📊 HDB rent &amp; price data</h1><p class='lead'>Real rents and resale prices from HDB's official data — "
            f"rents to {d['rent_latest']}, sales to {d['resale_latest']}.</p>"
            f"<div class='panelbox'><p class='fld' style='margin-top:0'>Singapore-wide, 4-room flat</p>"
            f"<div class='result'><div class='big'>{money(n4['rent'])} / month</div><p>median whole-flat rent · {chg(n4['rent_yoy'])} vs a year ago · "
            f"per bedroom {money(n4['room_est'])}*</p></div><p class='fld'>4-room median rent, last 24 months</p>"
            f"{spark(n4['rent_series'], d['rent_months'])}</div>"
            f"<div class='panelbox'><p class='fld' style='margin-top:0'>All flat types, Singapore-wide</p>{table(nat)}</div>"
            + note_panel() + private_panel() +
            f"<div class='panelbox'><p class='fld' style='margin-top:0'>4-room rent by town (cheapest first) — tap a town</p>"
            f"<div style='overflow-x:auto'><table class='tt'><tr><th>Town</th><th>Median rent</th><th>Change</th><th>Per bedroom*</th></tr>"
            f"{town_list}</table></div></div>" + FOOT)
    (out_dir / "index.html").write_text(idx, encoding="utf-8")
    for t, row in towns.items():
        x = row["4-ROOM"] if row["4-ROOM"]["rent"] else next((v for v in row.values() if v["rent"]), None)
        if not x:
            continue
        pg = HEAD.format(title=f"{title(t)} HDB rent & resale prices", path=f"{slug(t)}.html", site=SITE,
                         ld=dataset_ld(f"HDB rent and resale prices in {title(t)}, Singapore",
                                       f"Median HDB rents and resale prices in {title(t)} by flat type, from official HDB data.",
                                       f"{slug(t)}.html", d, f"{title(t)}, Singapore"),
                         desc=f"Median HDB rent and resale prices in {title(t)}, Singapore, from official HDB data "
                              f"to {d['rent_latest']}.")
        pg += (f"<p class='crumb'><a href='/market/'>← All towns</a></p><h1>{title(t)}: HDB rent &amp; prices</h1>"
               f"<p class='lead'>Official HDB data, rents to {d['rent_latest']}, sales to {d['resale_latest']}.</p>"
               f"<div class='panelbox'><p class='fld' style='margin-top:0'>Rent trend (median, 4-room)</p>"
               f"{spark(row['4-ROOM']['rent_series'], d['rent_months'])}"
               f"<p class='fld'>Resale price trend (median, 4-room)</p>"
               f"{spark(row['4-ROOM']['resale_series'], d['resale_months'], '#6d4bb5')}</div>"
               f"<div class='panelbox'>{table(row)}</div>"
               f"<p><a class='cta' href='/?q={html.escape(title(t).split(' / ')[0])}' style='text-decoration:none'>"
               f"See rooms in {title(t)} →</a></p>" + FOOT)
        (out_dir / f"{slug(t)}.html").write_text(pg, encoding="utf-8")
    (out_dir / "market.json").write_text(json.dumps(d, separators=(",", ":")), encoding="utf-8")
    sm = ROOT.parent / "sitemap.xml"
    xml = re.sub(r"\s*<url><loc>https://roomkaki\.com/market/[^<]*</loc></url>", "", sm.read_text(encoding="utf-8"))
    ent = [f"<url><loc>{SITE}/market/</loc></url>"] + [f"<url><loc>{SITE}/market/{slug(t)}.html</loc></url>" for t in towns]
    sm.write_text(xml.replace("</urlset>", "  " + "\n  ".join(ent) + "\n</urlset>"), encoding="utf-8")
    print(f"market build: index + {len(towns)} town pages; rent to {d['rent_latest']}, resale to {d['resale_latest']}")


if __name__ == "__main__":
    if "--no-fetch" not in sys.argv:
        fetch(RENT_ID); fetch(RESALE_ID); fetch(PRIVATE_ID)
    render(analyse(*load()))
