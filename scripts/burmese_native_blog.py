"""RoomKaki blog: Gemini WRITES the Burmese natively from the English (owner rule 11-21,
memory burmese-must-be-native-gemini). Claude never authors the Burmese.

For each post JSON (blog/posts + blog/pending) whose my_review != "gemini-native":
  ask Gemini -> validate (Myanmar Unicode, not Zawgyi, NFC, same <h2> count) ->
  save Gemini's exact output to D:/progress-ledger/BURMESE_NATIVE/<date>_roomkaki_<slug>.txt ->
  put the same text into the JSON, my_approved=true, my_review="gemini-native".
  python scripts/burmese_native_blog.py [--only slug]
Keys come from tts_gemini (rotating); keys are never printed.
"""
import json
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path

sys.path.insert(0, r"D:\_tmp\gg\episodes")
import tts_gemini as T  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
BANK = Path(r"D:\progress-ledger\BURMESE_NATIVE")
MODELS = ("gemini-3.8-flash", "gemini-3.5-flash")

PROMPT = """You are a native Burmese writer for a Singapore room-rental website used by Myanmar people.
Write the Burmese version of the guide below in natural, everyday Burmese (Myanmar Unicode, NOT Zawgyi) that an
ordinary Myanmar worker in Singapore understands at first reading. Write it the way a Myanmar person would explain
it to a friend — NOT a word-by-word translation. Keep every fact, number, place name and condition exactly.
Keep English terms that Myanmar people in Singapore use as-is: HDB, MRT, PUB, WiFi, aircon, PayNow, CEA, RoomKaki,
roomkaki.com, statecourts.gov.sg, police.gov.sg, cea.gov.sg, hdb.gov.sg, ScamShield, Google Lens, S$ amounts.
Keep the SAME HTML structure: the same number of <h2>, <p>, <ul>, <li> and <b> tags in the same order.
Return ONLY a JSON object: {"title_my": "<Burmese title>", "body_my": "<Burmese HTML body>"}

ENGLISH TITLE: %s

ENGLISH BODY (HTML):
%s
"""


def ask(key, model, title, body):
    payload = {"contents": [{"parts": [{"text": PROMPT % (title, body)}]}],
               "generationConfig": {"responseMimeType": "application/json", "temperature": 0.4}}
    req = urllib.request.Request(
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}",
        data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=240) as r:
        return json.load(r)["candidates"][0]["content"]["parts"][0]["text"]


def valid(en_body, title_my, body_my):
    s = title_my + body_my
    if not re.search(r"[\u1000-\u109f]{20,}", s):
        return "no Burmese text"
    if any(0x1060 <= ord(c) <= 0x1097 for c in s):
        return "Zawgyi characters"
    if body_my.count("<h2>") != en_body.count("<h2>"):
        return f"h2 count {body_my.count('<h2>')} != {en_body.count('<h2>')}"
    if "<script" in body_my.lower() or "onerror" in body_my.lower():
        return "unsafe HTML"
    return None


def native(post):
    last = "no key worked"
    for key in T.keys():
        for model in MODELS:
            try:
                out = json.loads(ask(key, model, post["title_en"], post["body_en"]))
                t = unicodedata.normalize("NFC", out["title_my"].strip())
                b = unicodedata.normalize("NFC", out["body_my"].strip())
                err = valid(post["body_en"], t, b)
                if not err:
                    return t, b, model
                last = f"{model}: {err}"
            except urllib.error.HTTPError as e:
                last = f"{model}: HTTP {e.code}"
                if e.code == 429:
                    break          # this key is rate-limited, try the next key
            except (TimeoutError, KeyError, ValueError, json.JSONDecodeError) as e:
                last = f"{model}: {type(e).__name__}"
    raise RuntimeError(last)


def main() -> int:
    only = sys.argv[sys.argv.index("--only") + 1] if "--only" in sys.argv else None
    BANK.mkdir(parents=True, exist_ok=True)
    files = sorted(list((ROOT / "blog/posts").glob("*.json")) + list((ROOT / "blog/pending").glob("*.json")))
    ok = fail = 0
    for f in files:
        post = json.loads(f.read_text(encoding="utf-8"))
        if post.get("my_review") == "gemini-native" or (only and post["slug"] != only):
            continue
        try:
            t, b, model = native(post)
        except RuntimeError as e:
            print(f"FAIL {post['slug']}: {e}"); fail += 1; continue
        (BANK / f"{date.today().isoformat()}_roomkaki_{post['slug']}.txt").write_text(
            f"[Gemini {model}, native Burmese for roomkaki.com/blog/{post['slug']}.html]\n{t}\n\n{b}\n",
            encoding="utf-8")
        post.update(title_my=t, body_my=b, my_approved=True, my_review="gemini-native")
        f.write_text(json.dumps(post, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"OK   {post['slug']} ({model})"); ok += 1
        time.sleep(2)
    print(f"done: {ok} written natively, {fail} failed")
    return 1 if fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
