"""Apply Gemini's Burmese review (WRONG => RIGHT lines) to blog post JSONs.

Only exact matches are replaced; anything spanning tag boundaries or garbled is skipped
and reported. Rejected suggestions (meaning-changing) are listed in REJECT.
  python scripts/apply_gemini_fixes.py <review.txt>
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REJECT = {"စစ်နည်းသိရင် လွယ်လွယ်မိပါတယ်။"}   # Gemini's fix inverted the meaning


def main(review_path: str) -> int:
    text = Path(review_path).read_text(encoding="utf-8")
    blocks = re.split(r"^===== (\S+\.json) =====$", text, flags=re.M)
    applied = skipped = rejected = 0
    for i in range(1, len(blocks), 2):
        name, body = blocks[i], blocks[i + 1]
        f = next((p for p in (ROOT / "blog/posts" / name, ROOT / "blog/pending" / name) if p.exists()), None)
        if not f:
            print("missing post", name); continue
        post = json.loads(f.read_text(encoding="utf-8"))
        for m in re.finditer(r"^WRONG: (.+?) => RIGHT: (.+?)\s*$", body, flags=re.M):
            wrong, right = m.group(1).strip(), m.group(2).strip()
            if wrong in REJECT:
                rejected += 1; continue
            hit = False
            for key in ("title_my", "body_my"):
                if wrong in post.get(key, ""):
                    post[key] = post[key].replace(wrong, right, 1); hit = True; break
            if hit:
                applied += 1
            else:
                skipped += 1; print(f"  skip [{name}]: no exact match")
        post["my_approved"] = True
        post["my_review"] = "gemini-2026-11-20"
        f.write_text(json.dumps(post, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"applied {applied}, skipped {skipped}, rejected {rejected}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
