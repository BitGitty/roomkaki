// RoomKaki regression checks (CRUCIBLE 2026-11-18). Run: node backend/regression_check.js
// Fails loudly if any crucible-confirmed defect returns.
const fs = require("fs");
const path = require("path");
const root = path.join(__dirname, "..");
const app = fs.readFileSync(path.join(root, "app.js"), "utf8");
const html = fs.readFileSync(path.join(root, "index.html"), "utf8");
const assert = (ok, name) => { console.log((ok ? "PASS" : "FAIL") + "  " + name); if (!ok) process.exitCode = 1; };

// Harness: evaluate app.js definitions without a DOM.
global.LINES = { EW: { name: "East West", color: "#009645" } };
global.document = { querySelector: () => null, querySelectorAll: () => [], addEventListener: () => {}, documentElement: {} };
global.location = { search: "", hash: "", pathname: "/" };
global.localStorage = { getItem: () => null, setItem: () => {} };
global.URLSearchParams = class { has() { return false; } };
global.fetch = () => Promise.resolve();
global.SB_URL = ""; global.SB_ANON = "";
(0, eval)(app.split("// ---------- live data ----------")[0].replace(/^let /gm, "var ").replace(/^const /gm, "var "));

const hostile = {
  id: 1, price: 900, type: "Common room", line: "EW", station: "s", walk: 1, area: "a",
  gender: "Any", owner: false, verified: false, days: 1, cooking: false, aircon: false,
  wifi: true, couple: false, hdb: true, minStay: 6, grad: ["#000", "#111"], src: null,
  title: `<img src=x onerror=alert(1)>`, my: "<b>x</b>", desc: "<script>bad()</script>",
};

// C1: card() must escape user content
const out = card(hostile);
assert(!out.includes("<img src=x"), "C1 card() escapes hostile title");
assert(out.includes("&lt;img"), "C1 escaped entity present");

// C9: default filter must not hide expensive rooms
globalThis.rooms = [{ ...hostile, title: "normal listing title", price: 2800 }];
assert(filtered().length === 1, "C9 S$2800 room visible by default");

// Room-wanted posts (2026-11-21): kept out of the rooms feed, shown in the wanted feed, escaped
globalThis.rooms = [{ ...hostile, title: "normal listing title", price: 900 },
                    { ...hostile, id: 2, kind: "wanted", title: "<b>hostile wanted</b> title", price: 700 }];
assert(filtered().length === 1 && filtered()[0].id === 1, "Wanted posts excluded from rooms feed");
state.kind = "wanted";
assert(filtered().length === 1 && filtered()[0].id === 2, "Wanted feed shows only wanted posts");
const wout = card(globalThis.rooms[1]);
assert(wout.includes("Looking for a room") && !wout.includes("<b>hostile"), "Wanted card renders + escapes");
state.kind = "offer";

// Multi-country readiness (2026-11-23): Singapore default unchanged; other markets render safely
assert(money(850) === "S$850", "SG default price format unchanged");
const sgMarket = MARKET;
MARKET = { id: "th", name: "Thailand", active: false, ui: { symbol: "฿", price_max: 30000, stay_note_true: "", stay_note_false: "" } };
LINES = {};
assert(money(12000) === "฿12,000", "Other market uses its own currency");
assert(lineDot("EW") === "", "No transit dot when market has no matching line");
assert(!card({ ...hostile, title: "thai room title ok", price: 12000 }).includes("undefined"), "Card renders without SG data");
MARKET = sgMarket; LINES = { EW: { name: "East West", color: "#009645" } };
assert(/enforce_active_market/.test(require("fs").readFileSync(require("path").join(__dirname, "multi_market.sql"), "utf8")),
       "DB refuses posts into switched-off markets");

// C6: phone sanitization pattern exists in reveal flow
assert(/replace\(\/\[\^0-9\+ \]\/g/.test(app), "C6 phone sanitized before tel/wa render");

// C16: double-submit guard present
assert(app.includes("btn.disabled = true"), "C16 double-submit guard present");

// C10: error state distinct from empty marketplace
assert(app.includes("Couldn't load listings"), "C10 fetch-error state exists");

// C29: real language toggle wired, alert stub gone
assert(html.includes('id="langBtn"') && !html.includes("Prototype: full Burmese UI"), "C29 real language toggle");
assert(/toggleLang/.test(app), "C29 toggleLang implemented");

// C23: no unverified 'Verified posters' marketing claim in static HTML
assert(!/Verified posters/.test(html), "C23 hero claim honest");

// Found listings: source link guarded + outclick tracked
assert(app.includes("safeUrl(r.src)") && app.includes("/ev/out/"), "Found-listing URL guard + outclick event");
