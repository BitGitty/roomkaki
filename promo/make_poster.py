"""Printable A4 QR poster for community spots (Peninsula Plaza, temples, shops). Burmese written natively by
Gemini (owner rule 11-21). Outputs promo/poster.html and promo/poster_A4.pdf (rendered by Chromium so Burmese
shapes correctly).  python promo/make_poster.py"""
import asyncio
import json
import sys
import unicodedata
import urllib.request
from datetime import date
from pathlib import Path

import segno
from playwright.async_api import async_playwright

sys.path.insert(0, r"D:\_tmp\gg\episodes")
import tts_gemini as T  # noqa: E402

HERE = Path(__file__).resolve().parent
EN = {"head": "Need a room in Singapore?", "sub": "Or have a room to rent out?",
      "points": ["Free to post and browse", "No agent fees", "Every post checked before it goes live",
                 "Burmese and English", "Room alerts on Telegram"],
      "scan": "Scan to find or post a room", "tg": "Join our Telegram channel"}


def gemini_my():
    prompt = ("You are a native Burmese writer. Translate these short poster lines into natural, friendly everyday "
              "Burmese (Myanmar Unicode, not Zawgyi) the way a Myanmar person in Singapore would say them — short and "
              "clear for a printed poster. Keep 'Telegram' in English. Return ONLY JSON with the same keys and the "
              "points as a list.\n\n" + json.dumps(EN, ensure_ascii=False))
    for key in T.keys():
        for model in ("gemini-3.5-flash", "gemini-3.8-flash"):
            try:
                req = urllib.request.Request(
                    f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}",
                    data=json.dumps({"contents": [{"parts": [{"text": prompt}]}],
                                     "generationConfig": {"responseMimeType": "application/json"}}).encode(),
                    headers={"Content-Type": "application/json"})
                with urllib.request.urlopen(req, timeout=120) as r:
                    out = json.loads(json.load(r)["candidates"][0]["content"]["parts"][0]["text"])
                    return json.loads(unicodedata.normalize("NFC", json.dumps(out, ensure_ascii=False))), model
            except Exception:                                    # noqa: BLE001
                continue
    raise SystemExit("no Gemini key worked")


my, model = gemini_my()
(Path(r"D:\progress-ledger\BURMESE_NATIVE") / f"{date.today().isoformat()}_roomkaki_poster.txt").write_text(
    f"[Gemini {model}]\n{json.dumps(my, ensure_ascii=False, indent=1)}\n", encoding="utf-8")
qr_site = segno.make("https://roomkaki.com/?src=poster", error="h").svg_inline(scale=10, dark="#0a3f3a")
qr_tg = segno.make("https://t.me/roomkaki", error="m").svg_inline(scale=6, dark="#229ED9")
li = "".join(f"<li>✅ {e}<br><span class='my'>{m}</span></li>" for e, m in zip(EN["points"], my["points"]))
page = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><title>RoomKaki poster</title>
<style>
@page {{ size: A4; margin: 0 }}
body {{ margin:0; font-family: 'Segoe UI', 'Myanmar Text', 'Noto Sans Myanmar', sans-serif; color:#15201d }}
.p {{ width:210mm; height:297mm; box-sizing:border-box; padding:16mm 16mm 12mm; display:flex; flex-direction:column;
      background: linear-gradient(180deg,#0d9488 0 74mm,#fff 74mm) }}
.logo {{ color:#fff; font-size:16mm; font-weight:800; letter-spacing:-.5mm }} .logo b {{ color:#bff3ea }}
.head {{ color:#fff; font-size:9mm; font-weight:800; margin-top:3mm }} .head .my {{ color:#e6fffa; font-size:6.5mm }}
.sub {{ font-size:7mm; font-weight:700; margin:16mm 0 4mm }} .sub .my {{ font-size:5.5mm; color:#3d4f4a }}
ul {{ list-style:none; padding:0; margin:0; font-size:5.6mm; line-height:1.35 }} li {{ margin-bottom:3.2mm }}
.my {{ font-family:'Myanmar Text','Noto Sans Myanmar',sans-serif; font-weight:600 }}
.qrs {{ margin-top:auto; display:flex; align-items:flex-end; justify-content:space-between }}
.q1 svg {{ width:62mm; height:62mm }} .q2 svg {{ width:30mm; height:30mm }}
.cap {{ font-size:5mm; font-weight:800; text-align:center }} .url {{ font-size:7mm; font-weight:800; color:#0d9488; text-align:center }}
</style></head><body><div class="p">
<div class="logo"><b>Room</b>Kaki</div>
<div class="head">{EN['head']}<br><span class="my">{my['head']}</span></div>
<div class="sub">{EN['sub']}<br><span class="my">{my['sub']}</span></div>
<ul>{li}</ul>
<div class="qrs"><div class="q1">{qr_site}<div class="cap">{EN['scan']}<br><span class="my">{my['scan']}</span></div>
<div class="url">roomkaki.com</div></div>
<div class="q2">{qr_tg}<div class="cap" style="font-size:3.8mm">{EN['tg']}<br><span class="my">{my['tg']}</span></div></div></div>
</div></body></html>"""
(HERE / "poster.html").write_text(page, encoding="utf-8")


async def pdf():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page()
        await pg.goto((HERE / "poster.html").as_uri())
        await pg.pdf(path=str(HERE / "poster_A4.pdf"), format="A4", print_background=True)
        await pg.set_viewport_size({"width": 794, "height": 1123})
        await pg.screenshot(path=str(HERE / "poster_preview.png"))
        await b.close()

asyncio.run(pdf())
print("poster done:", HERE / "poster_A4.pdf")
