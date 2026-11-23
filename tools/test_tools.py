"""Browser tests for roomkaki.com/tools — known inputs, exact expected outputs. Run after any tool change:
  python tools/test_tools.py            (serves the repo locally on port 8765)
Exit code 1 if any check fails."""
import asyncio
import http.server
import socketserver
import sys
import threading
from functools import partial
from pathlib import Path

from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parent.parent
PORT = 8765
fails = 0


def check(ok, name, got=""):
    global fails
    print(("PASS  " if ok else "FAIL  ") + name + ("" if ok else f"   got: {got!r}"))
    fails += 0 if ok else 1


async def fill(pg, sel, val):
    await pg.fill(sel, str(val))
    await pg.dispatch_event(sel, "input")


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(headless=True)
        pg = await b.new_page()
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        u = f"http://127.0.0.1:{PORT}/tools/"

        await pg.goto(u + "stamp-duty.html")
        await fill(pg, "#rent", 800); await fill(pg, "#months", 12)
        t = await pg.inner_text("#out"); check("S$38" in t, "stamp duty 800×12 → S$38 (0.4% of 9,600, rounded down)", t)
        await fill(pg, "#rent", 80)
        t = await pg.inner_text("#out"); check("S$0" in t and "Exempt" in t, "stamp duty exempt when yearly rent ≤ S$1,000", t)
        await fill(pg, "#rent", 2000); await fill(pg, "#months", 60)
        t = await pg.inner_text("#out"); check("S$384" in t, "stamp duty >4 yrs uses 4 yrs of rent (0.4%×96,000)", t)

        await pg.goto(u + "hdb-room-check.html")
        await pg.select_option("#ft", "2"); await fill(pg, "#people", 3); await fill(pg, "#stay", 12)
        t = await pg.inner_text("#out"); check("Not allowed" in t, "HDB: 2-room cannot rent out a bedroom", t)
        await pg.select_option("#ft", "4"); await fill(pg, "#people", 7)
        t = await pg.inner_text("#out"); check("allowed" in t.lower() and "Not" not in t, "HDB: 4-room, 7 people, ends by 2028 → allowed", t)
        await pg.select_option("#ends", "after2028"); await pg.dispatch_event("#ends", "input")
        t = await pg.inner_text("#out"); check("Not allowed" in t, "HDB: 4-room, 7 people, after 2028 → over cap of 6", t)
        await pg.select_option("#ends", "by2028"); await pg.dispatch_event("#ends", "input"); await fill(pg, "#stay", 3)
        t = await pg.inner_text("#out"); check("Not allowed" in t and "6 months" in t, "HDB: 3-month stay not allowed", t)

        await pg.goto(u + "scam-check.html")
        await pg.click(".q:nth-child(1) button[data-v='1']")
        t = await pg.inner_text("#out"); check("High risk" in t, "Scam: deposit before viewing → high risk", t)

        await pg.goto(u + "bill-split.html")
        await fill(pg, "#bill", 200)
        t = await pg.inner_text("#out"); check(t.count("S$100.00") == 2, "Bill split: 200 between 2 full-month people → 100 each", t)

        await pg.goto(u + "move-out-dates.html")
        await fill(pg, "#start", "2026-01-15"); await fill(pg, "#give", "2026-03-01")
        t = await pg.inner_text("#out"); check("14 Jul 2026" in t, "Move-out: notice ends before 6-month minimum → last day 14 Jul 2026", t)
        await fill(pg, "#give", "2026-09-10")
        t = await pg.inner_text("#out"); check("9 Oct 2026" in t, "Move-out: 1-month notice from 10 Sep → last day 9 Oct 2026", t)

        await pg.goto(u + "rent-budget.html")
        await fill(pg, "#pay", 2500)
        t = await pg.inner_text("#out"); check("S$750" in t, "Rent budget: 2,500 pay → comfortable up to S$750 (30%)", t)

        await pg.goto(u + "true-cost.html")
        await fill(pg, "[data-k='rent'][data-c='0']", 800); await fill(pg, "[data-k='fare'][data-c='0']", 100)
        await fill(pg, "[data-k='cook'][data-c='0']", 0)
        t = await pg.inner_text("#out"); check("S$1,150" in t, "True cost: 800 + 100 fare + no cooking 250 → 1,150", t)

        await pg.goto(u + "area-finder.html")
        await fill(pg, "#budget", 800)
        t = await pg.inner_text("#out"); check("Sembawang" in t and "Novena" not in t, "Area finder: S$800 common room → Sembawang yes, Novena no", t)

        await pg.goto(u + "tenancy-agreement.html")
        await pg.fill("#ll", "<img src=x onerror=alert(1)>"); await pg.fill("#rent", "800")
        await pg.click("#make")
        h = await pg.inner_html("#doc"); check("&lt;img" in h and "<img src=x" not in h, "Agreement: user text is escaped (no XSS)", h[:120])

        await pg.goto(u + "commute.html")
        await pg.wait_for_function("document.getElementById('stations').options.length > 100")
        await fill(pg, "#from", "boonlay"); await fill(pg, "#to", "Raffles Place")
        t = await pg.inner_text("#out")
        check("No line change" in t and "13 stops" in t and "29 min" in t, "Commute: Boon Lay → Raffles Place = EW direct, 13 stops, ≈29 min", t)
        await fill(pg, "#from", "Woodlands"); await fill(pg, "#to", "Bugis")
        t = await pg.inner_text("#out"); check("line change" in t and "min" in t, "Commute: Woodlands → Bugis needs a line change", t)
        await fill(pg, "#from", "Bishan"); await fill(pg, "#to", "Bishan")
        t = await pg.inner_text("#out"); check("Same station" in t, "Commute: same station handled", t)

        await pg.goto(u + "fair-rent.html")
        await pg.wait_for_function("document.getElementById('town').options.length > 10")
        await pg.select_option("#what", "4-ROOM"); await pg.select_option("#town", "WOODLANDS")
        await fill(pg, "#ask", 3100)
        t = await pg.inner_text("#out"); check("Fair price" in t, "Fair rent: Woodlands 4-room at its median → fair", t)
        await fill(pg, "#ask", 1500)
        t = await pg.inner_text("#out"); check("Much cheaper" in t, "Fair rent: 4-room at half the median → scam warning", t)
        await pg.select_option("#what", "common"); await pg.dispatch_event("#what", "input"); await fill(pg, "#ask", 700)
        t = await pg.inner_text("#out"); check("Fair price" in t, "Fair rent: Woodlands common room S$700 → fair", t)

        await pg.goto(u)
        n = await pg.eval_on_selector_all(".toolcard", "c => c.length")
        check(n >= 9, "Tools index lists the built tools", n)
        check(not errs, "No JavaScript errors on any tool page", errs)
        await b.close()


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


if __name__ == "__main__":
    srv = socketserver.TCPServer(("127.0.0.1", PORT), partial(Quiet, directory=str(ROOT)))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        asyncio.run(main())
    finally:
        srv.shutdown()
    sys.exit(1 if fails else 0)
