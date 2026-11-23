"""Per-market page wording (hero line, search hint, safety footer, form examples) -> markets.ui.copy.
English is written here; the Burmese versions are WRITTEN natively by Gemini (owner rule 11-21), saved to
D:/progress-ledger/BURMESE_NATIVE/, then stored. Singapore keeps its existing owner-approved wording in app.js.
  python backend/market_copy.py   (then it runs the SQL through run_sql.py)
"""
import json
import subprocess
import sys
import unicodedata
import urllib.request
from datetime import date
from pathlib import Path

sys.path.insert(0, r"D:\_tmp\gg\episodes")
import tts_gemini as T  # noqa: E402

HERE = Path(__file__).resolve().parent
COPY = {
    "th": {"logo_sub": "THAILAND",
           "hero_sub_en": "Moderated listings · owner-direct rooms · BTS/MRT search. Built for Myanmar and other communities in Thailand, in your language.",
           "search_ph_en": "Search area or BTS/MRT station… e.g. On Nut",
           "safety_en": "Safety first: never transfer money before viewing the room in person.",
           "ph_station": "On Nut", "ph_area": "Bang Na", "ph_title": "Furnished room, 5 min to On Nut BTS",
           "ph_title_wanted": "Working lady looking for a room near Mo Chit", "ph_phone": "+66 8x xxx xxxx"},
    "mm": {"logo_sub": "MYANMAR",
           "hero_sub_en": "Moderated listings · owner-direct rooms. Built for our community in Myanmar, in your language.",
           "search_ph_en": "Search township or area… e.g. Sanchaung",
           "safety_en": "Safety first: never transfer money before viewing the room in person.",
           "ph_station": "", "ph_area": "Sanchaung", "ph_title": "Room for rent in Sanchaung, near Hledan",
           "ph_title_wanted": "Student looking for a room near Hledan", "ph_phone": "+95 9 xxx xxx xxx"},
}
PROMPT = """You are a native Burmese writer for a room-rental website used by Myanmar people.
Write natural, everyday Burmese (Myanmar Unicode, NOT Zawgyi) for each English line below — short website UI text,
the way a Myanmar person would say it, not word-by-word. Keep place names, BTS, MRT and "e.g." examples in English.
Return ONLY JSON with the same keys: {"hero_sub": "...", "search_ph": "...", "safety": "..."}

%s"""


def gemini(text):
    for key in T.keys():
        for model in ("gemini-3.5-flash", "gemini-3.8-flash"):
            try:
                body = {"contents": [{"parts": [{"text": PROMPT % text}]}],
                        "generationConfig": {"responseMimeType": "application/json"}}
                req = urllib.request.Request(
                    f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}",
                    data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
                with urllib.request.urlopen(req, timeout=120) as r:
                    return json.loads(json.load(r)["candidates"][0]["content"]["parts"][0]["text"]), model
            except Exception:                                    # noqa: BLE001 — try next model/key
                continue
    raise RuntimeError("no Gemini key worked")


sql = []
bank = Path(r"D:\progress-ledger\BURMESE_NATIVE") / f"{date.today().isoformat()}_roomkaki_market_copy.txt"
log = []
for mk, c in COPY.items():
    en = json.dumps({"hero_sub": c["hero_sub_en"], "search_ph": c["search_ph_en"], "safety": c["safety_en"]}, ensure_ascii=False)
    my, model = gemini(en)
    for k in ("hero_sub", "search_ph", "safety"):
        v = unicodedata.normalize("NFC", my[k].strip())
        assert any("\u1000" <= ch <= "\u109f" for ch in v), f"{mk}.{k}: no Burmese"
        assert not any(0x1060 <= ord(ch) <= 0x1097 for ch in v), f"{mk}.{k}: Zawgyi"
        c[k + "_my"] = v
    log.append(f"[{mk} — Gemini {model}]\n" + json.dumps({k: c[k] for k in c if k.endswith('_my')}, ensure_ascii=False, indent=1))
    sql.append(f"update markets set ui = jsonb_set(ui, '{{copy}}', '{json.dumps(c, ensure_ascii=False).replace(chr(39), chr(39)*2)}'::jsonb) where id = '{mk}';")
bank.write_text("\n\n".join(log) + "\n", encoding="utf-8")
(HERE / "market_copy.sql").write_text("\n".join(sql) + "\n", encoding="utf-8")
print(subprocess.run([sys.executable, str(HERE / "run_sql.py"), str(HERE / "market_copy.sql")],
                     capture_output=True, text=True, encoding="utf-8").stdout[-200:])
