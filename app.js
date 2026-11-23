let state = { kind: "offer", type: "All", line: "All", gender: "All", ownerOnly: false, maxPrice: 3000, q: "", view: "grid" };
let map, markers = [];
// Demo rooms only for design review (?demo=1) — the live site never shows fake listings.
const DEMO = new URLSearchParams(location.search).has("demo");
let rooms = (DEMO && typeof LISTINGS !== "undefined") ? LISTINGS.slice() : [];

const $ = (s) => document.querySelector(s);

// ---------- market (country) config — only active markets are offered; SG is the default ----------
let MARKET = { id: "sg", name: "Singapore", active: true, ui: {
  symbol: "S$", center: [1.3521, 103.8198], zoom: 11, transit_word: "MRT",
  property_types: [["true", "HDB"], ["false", "Condo"]],
  stay_note_true: "HDB rules: minimum {n}-month stay applies.", stay_note_false: "Condo listing — minimum {n} months.",
  min_stay_true: 6, min_stay_false: 3, price_max: 3000, price_step: 50 } };
let MARKETS = [MARKET];
let PREVIEW = false;
const money = (n) => `${MARKET.ui.symbol}${(+n || 0).toLocaleString("en")}`;
const hasTransit = () => typeof LINES !== "undefined" && Object.keys(LINES).length > 0;
const norm = (s) => String(s || "").normalize("NFC").toLowerCase();  // Burmese must match via NFC

// ---------- i18n (EN / Burmese) ----------
const I18N = {
  heroTitle: { en: "Find a room you can <em>trust</em>", my: "ယုံကြည်လို့ရတဲ့ <em>အခန်း</em> ရှာပါ" },
  heroSub: {
    en: "Moderated listings · owner-direct rooms · MRT-smart search. Built for Singapore's communities, in your language.",
    my: "စိစစ်ပြီးမှတင်သော ကြော်ငြာများ · ပိုင်ရှင်တိုက်ရိုက် အခန်းများ · MRT ဖြင့်ရှာဖွေမှု။ စင်ကာပူရှိ မိမိအသိုင်းအဝိုင်းအတွက် တည်ဆောက်ထားသည်။",
  },
  searchBtn: { en: "Search", my: "ရှာမယ်" },
  postRoom: { en: "Post a room", my: "အခန်းတင်မယ်" },
  cards: { en: "Cards", my: "ကတ်များ" },
  mapBtn: { en: "Map", my: "မြေပုံ" },
  safetyFoot: {
    en: "Safety first: never transfer money before viewing · HDB minimum-stay rules shown on every listing",
    my: "ဘေးကင်းရေးအရင် — အခန်းကို ကိုယ်တိုင်မကြည့်ရသေးခင် ငွေမလွှဲပါနှင့် · HDB အနည်းဆုံးနေထိုင်ရမည့်ကာလကို ကြော်ငြာတိုင်းတွင် ဖော်ပြထားသည်",
  },
  searchPh: { en: "Search area or MRT station… e.g. Boon Lay", my: "နေရာ သို့မဟုတ် MRT ဘူတာ ရှာပါ… ဥပမာ Boon Lay" },
};
let lang = "en";
try { lang = localStorage.getItem("rk_lang") === "my" ? "my" : "en"; } catch (e) {}

function applyLang() {
  document.documentElement.lang = lang;
  document.querySelectorAll("[data-i18n]").forEach((el) => {
    const t = I18N[el.dataset.i18n];
    if (t) el.innerHTML = t[lang];
  });
  const q = $("#q");
  if (q) q.placeholder = I18N.searchPh[lang];
  const btn = $("#langBtn");
  if (btn) btn.textContent = lang === "en" ? "မြန်မာ" : "English";
}

function toggleLang() {
  lang = lang === "en" ? "my" : "en";
  try { localStorage.setItem("rk_lang", lang); } catch (e) {}
  applyLang();
}

function lineDot(l) {
  if (!hasTransit() || !LINES[l]) return "";
  return `<span class="dot" style="background:${LINES[l].color}">${escId(l)}</span>`;
}

function phBg(r) {
  return (r.photos && r.photos.length)
    ? `background-image:url('${r.photos[0]}');background-size:cover;background-position:center`
    : `background:linear-gradient(135deg,${r.grad[0]},${r.grad[1]})`;
}

function filtered() {
  return rooms.filter((r) =>
    (r.kind || "offer") === state.kind &&
    (state.type === "All" || r.type === state.type) &&
    (state.line === "All" || r.line === state.line) &&
    (state.gender === "All" || r.gender === state.gender || r.gender === "Any") &&
    (!state.ownerOnly || r.owner) &&
    (state.maxPrice >= (MARKET.ui.price_max || 3000) || r.price <= state.maxPrice) &&
    (state.q === "" || norm(`${r.title} ${r.my || ""} ${r.area} ${r.station} ${r.desc || ""}`).includes(norm(state.q)))
  );
}

function wantedCard(r) {
  return `<article class="card wanted" tabindex="0" role="button" aria-label="${escId(r.title)}"
    onclick="openSheet(${r.id})" onkeydown="if(event.key==='Enter')openSheet(${r.id})">
    <div class="body">
      <div><span class="badge want">Looking for a room</span> <span class="tag">${escId(r.type)}</span></div>
      <div class="price" style="margin-top:8px">Budget ${money(r.price)}<small>/month</small></div>
      <h3>${escId(r.title)}</h3>
      <div class="mrt">Prefers: ${escId(r.area)}${r.station ? ` · near ${escId(r.station)} MRT` : ""}</div>
      <div class="tags">
        <span class="tag">${escId(String(r.gender).replace(" only", ""))}</span>
        ${r.cooking ? '<span class="tag">Needs cooking</span>' : ""}
        ${r.couple ? '<span class="tag">Couple</span>' : ""}
      </div>
      <div class="meta">${r.days === 0 ? "Posted today" : `Posted ${r.days}d ago`}</div>
    </div>
  </article>`;
}

function card(r) {
  if (r.kind === "wanted") return wantedCard(r);
  return `<article class="card" tabindex="0" role="button" aria-label="${escId(r.title)}"
    onclick="openSheet(${r.id})" onkeydown="if(event.key==='Enter')openSheet(${r.id})">
    <div class="ph" style="${phBg(r)}">
      <span class="badge ${r.src ? "" : r.owner ? "owner" : "agent"}">${r.src ? "Found" : r.owner ? "Owner direct" : "Agent"}</span>
      <span class="badge">${escId(r.type)}</span>
    </div>
    <div class="body">
      <div class="price">${money(r.price)}<small>/month</small></div>
      <h3>${escId(r.title)}</h3>
      <div class="mrt">${lineDot(r.line)} ${escId(r.station)} · ${+r.walk || 0} min walk</div>
      <div class="tags">
        ${r.verified ? '<span class="tag v">✓ Verified poster</span>' : ""}
        ${r.src ? '<span class="tag">Found listing</span>' : ""}
        <span class="tag">${escId(r.gender)}</span>
        ${r.cooking ? '<span class="tag">Cooking OK</span>' : ""}
        ${r.aircon ? '<span class="tag">Aircon</span>' : ""}
        ${r.couple ? '<span class="tag">Couple OK</span>' : ""}
      </div>
      <div class="meta">${r.src ? `Found ${r.days}d ago` : r.days === 0 ? "Posted today" : `Posted ${r.days}d ago`} · ${escId(r.area)}</div>
    </div>
  </article>`;
}

function render() {
  const list = filtered();
  const wanted = state.kind === "wanted";
  $("#count").textContent = wanted ? `${list.length} ${list.length === 1 ? "person" : "people"} looking` : `${list.length} rooms`;
  document.querySelectorAll("[data-kind]").forEach((b) => b.classList.toggle("on", b.dataset.kind === state.kind));
  if (wanted && !list.length) {
    $("#grid").innerHTML = `<div style="grid-column:1/-1;text-align:center;padding:48px 20px">
        <h3 style="margin:0 0 8px">No room-wanted posts yet</h3>
        <p style="color:var(--mut);margin:0 0 18px">Looking for a room? Post what you need — landlords with a matching room can contact you.</p>
        <button class="cta" onclick="openPost(null, 'wanted')">Post what you're looking for — free</button>
      </div>`;
    if (state.view === "map") renderMap(list);
    return;
  }
  $("#grid").innerHTML = list.map(card).join("") || (rooms.filter((r) => (r.kind || "offer") === "offer").length === 0
    ? `<div style="grid-column:1/-1;text-align:center;padding:48px 20px">
        <h3 style="margin:0 0 8px">We just opened — no rooms yet</h3>
        <p style="color:var(--mut);margin:0 0 6px">Have a room to rent out? Post it free and be one of our founding listings.</p>
        <p style="color:var(--mut);margin:0 0 18px">အခန်းငှားစရာရှိပါသလား? အခမဲ့တင်နိုင်ပါပြီ — ပထမဆုံးတင်သူများထဲက တစ်ယောက်ဖြစ်လိုက်ပါ။</p>
        <button class="cta" onclick="openPost()">Post a room — free</button>
      </div>`
    : '<p style="grid-column:1/-1;text-align:center;color:var(--mut);padding:40px">No rooms match — try widening the filters.</p>');
  if (state.view === "map") renderMap(list);
}

function renderMap(list) {
  if (!map) {
    map = L.map("map").setView(MARKET.ui.center || [1.3521, 103.8198], MARKET.ui.zoom || 11);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
      { attribution: "© OpenStreetMap" }).addTo(map);
  }
  markers.forEach((m) => m.remove());
  const pts = list.filter((r) => r.lat != null && r.lng != null);
  markers = pts.map((r) =>
    L.marker([r.lat, r.lng]).addTo(map)
      .bindPopup(`<b>${money(r.price)}</b> · ${escId(r.type)}<br>${escId(r.station)} ${+r.walk || 0}min<br>
        <a href="#" onclick="openSheet(${r.id});return false">View room →</a>`));
  if (pts.length) map.fitBounds(pts.map((r) => [r.lat, r.lng]), { padding: [40, 40], maxZoom: 14 });
}

function setKind(k) {
  state.kind = k;
  render();
}

function setView(v) {
  state.view = v;
  $("#grid").style.display = v === "grid" ? "grid" : "none";
  $("#map").style.display = v === "map" ? "block" : "none";
  document.querySelectorAll(".toggle button").forEach((b) => b.classList.toggle("on", b.dataset.v === v));
  if (v === "map") { render(); setTimeout(() => map.invalidateSize(), 60); }
}

function safeUrl(u) {
  return /^https:\/\/[^"'<>\s]+$/.test(String(u || "")) ? u : "";
}

function openSheet(id) {
  const r = rooms.find((x) => x.id === id);
  if (!r) return;
  track(`/ev/open/${id}`);
  try { history.replaceState(null, "", `#room-${id}`); } catch (e) {}
  if (r.kind === "wanted") {
    $("#sheet").innerHTML = `
      <button class="close" onclick="closeSheet()" aria-label="Close">✕</button>
      <div class="inner" style="padding-top:56px">
        <span class="badge want">Looking for a room</span>
        <div class="price" style="margin-top:10px">Budget ${money(r.price)}<small>/month</small></div>
        <h2>${escId(r.title)}</h2>
        <div class="safety">🛡️ <b>Landlords:</b> never ask for money before the person has viewed your room.</div>
        <p>${escId(r.desc)}</p>
        <div class="facts">
          <div><b>Wants</b>${escId(r.type)}</div>
          <div><b>Preferred area</b>${escId(r.area)}${r.station ? ` · ${escId(r.station)} MRT` : ""}</div>
          <div><b>Who</b>${escId(String(r.gender).replace(" only", ""))}${r.couple ? " · couple" : ""}</div>
          <div><b>Cooking</b>${r.cooking ? "Needs to cook" : "Not needed"}</div>
        </div>
        <div class="contact" id="contactBox">
          <button class="cta" onclick="doReveal(${r.id})">Show contact</button>
          <button class="ghost" onclick="doReport(${r.id})">Report</button>
          <button class="ghost" onclick="shareRoom(${r.id})" aria-label="Share">Share</button>
        </div>
      </div>`;
    $("#panel").classList.add("open");
    return;
  }
  $("#sheet").innerHTML = `
    <button class="close" onclick="closeSheet()" aria-label="Close">✕</button>
    <div class="ph" style="${phBg(r)}"></div>
    ${r.photos && r.photos.length > 1
      ? `<div class="photostrip">${r.photos.slice(1).map((u) => `<img src="${u}" loading="lazy" alt="room photo">`).join("")}</div>`
      : ""}
    <div class="inner">
      <div class="price">${money(r.price)}<small>/month</small></div>
      <h2>${escId(r.title)}</h2>
      <div class="my">${escId(r.my)}</div>
      <div class="mrt">${hasTransit() && LINES[r.line] ? `${lineDot(r.line)} ${escId(LINES[r.line].name)} line · ` : ""}${escId(r.station)}${r.walk ? ` · ${+r.walk} min walk` : ""}</div>
      <div class="safety">🛡️ <b>Stay safe:</b> never transfer a deposit before viewing the room in person.
        ${(MARKET.ui[r.hdb ? "stay_note_true" : "stay_note_false"] || "").replace("{n}", r.minStay)}</div>
      <p>${escId(r.desc)}</p>
      <div class="facts">
        <div><b>Room type</b>${escId(r.type)}</div>
        <div><b>Preference</b>${escId(r.gender)}${r.couple ? " · couples OK" : ""}</div>
        <div><b>Cooking</b>${r.cooking ? "Allowed" : "Not allowed"}</div>
        <div><b>Comfort</b>${[r.aircon ? "Aircon" : "Fan", r.wifi ? "WiFi" : null].filter(Boolean).join(" · ")}</div>
        <div><b>Listed by</b>${r.src ? "Found listing" : r.owner ? "Owner (no commission)" : "Agent"}</div>
        <div><b>Poster</b>${r.src ? "Found on a public post — not yet verified" : (r.verified ? "✓ Phone-verified" : "Unverified")}</div>
      </div>
      <div class="contact" id="contactBox">
        ${r.src
          ? `<a class="cta" href="${safeUrl(r.src)}" target="_blank" rel="noopener" onclick="track('/ev/out/${r.id}')">View original post ↗</a>
             <button class="ghost" onclick="doReport(${r.id})">Report</button>`
          : r._real
          ? `<button class="cta" onclick="doReveal(${r.id})">Show contact</button>
             <button class="ghost" onclick="doReport(${r.id})">Report</button>`
          : `<button class="cta" onclick="alert('Demo listing — real contact reveal works on live posts.')">Show contact</button>
             <button class="ghost" onclick="alert('Demo listing — reporting works on live posts.')">Report</button>`}
        <button class="ghost" onclick="shareRoom(${r.id})" aria-label="Share">Share</button>
      </div>
    </div>`;
  $("#panel").classList.add("open");
}

function shareRoom(id) {
  const url = `https://roomkaki.com/#room-${id}`;
  const r = rooms.find((x) => x.id === id);
  if (navigator.share) { navigator.share({ title: r ? r.title : "RoomKaki", url }).catch(() => {}); return; }
  navigator.clipboard.writeText(url).then(() => alert("Link copied — share it anywhere."), () => prompt("Copy this link:", url));
}

async function doReveal(id) {
  if (!(await currentUser())) { openLogin("Log in to see the poster's contact — it's free."); return; }
  const box = $("#contactBox");
  box.innerHTML = "<span class='mut'>Revealing…</span>";
  const res = await revealContact(id);
  if (res.error) { box.innerHTML = `<span class='mut'>Couldn't reveal: ${escId(res.error)}</span>`; return; }
  const phone = String(res.phone || "").replace(/[^0-9+ ]/g, "").slice(0, 20);
  const wa = phone.replace(/[^0-9]/g, "");
  box.innerHTML = `<a class="cta" href="https://wa.me/${wa}" target="_blank" rel="noopener">WhatsApp ${escId(phone)}</a>
    <a class="ghost" href="tel:${phone.replace(/ /g, "")}">Call ${escId(phone)}</a>`;
}

const REPORT_REASONS = ["scam", "fake_photos", "already_rented", "wrong_info", "abusive", "other"];
async function doReport(id) {
  if (!(await currentUser())) { openLogin("Log in to report a listing — helps us stop scams fast."); return; }
  const pick = prompt("Report this listing — reply with a number:\n" +
    "1  Scam or fake\n2  Fake photos\n3  Already rented\n4  Wrong info\n5  Abusive\n6  Other");
  if (!pick) return;
  const reason = REPORT_REASONS[(parseInt(pick, 10) || 6) - 1] || "other";
  const detail = prompt("Any details? (optional)") || null;
  const err = await reportListing(id, reason, detail);
  alert(err ? "Couldn't send report: " + err : "Thanks — our team will review it within 48 hours.");
}
function closeSheet() {
  $("#panel").classList.remove("open");
  try { history.replaceState(null, "", location.pathname + location.search); } catch (e) {}
}

// lightweight event beacon (same RPC as pageviews; pseudo-paths /ev/open/<id>, /ev/out/<id>)
function track(path) {
  try {
    fetch(SB_URL + "/rest/v1/rpc/track_view", {
      method: "POST",
      headers: { apikey: SB_ANON, Authorization: "Bearer " + SB_ANON, "Content-Type": "application/json" },
      body: JSON.stringify({ p_site: "roomkaki", p_path: path, p_ref: null }),
      keepalive: true,
    }).catch(() => {});
  } catch (e) {}
}

// ---------- modals (login + post a room) ----------
function closeModal() { $("#modal").classList.remove("open"); }

function openModal(html) {
  $("#modalbox").innerHTML = `<button class="close" onclick="closeModal()">✕</button>${html}`;
  $("#modal").classList.add("open");
}

async function refreshAuth() {
  const user = await currentUser();
  const slot = $("#authSlot");
  if (user) {
    slot.innerHTML = `<button class="lang" onclick="openMyRooms()">My rooms</button>
      <span class="who">${(user.email || "member").split("@")[0]}</span>
      <button class="lang" onclick="doLogout()">Log out</button>`;
  } else {
    slot.innerHTML = `<button class="lang" onclick="openLogin()">Log in</button>`;
  }
  return user;
}

async function doLogout() { await logout(); await refreshAuth(); }

function openLogin(afterMsg) {
  openModal(`<h2>Log in to RoomKaki</h2>
    <p class="mut">We'll email you a one-tap sign-in link — no password.</p>
    ${afterMsg ? `<p class="mut">${afterMsg}</p>` : ""}
    <input id="loginEmail" type="email" placeholder="you@email.com" autocomplete="email">
    <button class="cta wide" onclick="submitLogin()">Email me a link</button>
    <div id="loginMsg" class="mut"></div>`);
}

async function submitLogin() {
  const email = $("#loginEmail").value.trim();
  if (!email) return;
  $("#loginMsg").textContent = "Sending…";
  const err = await sendLogin(email);
  $("#loginMsg").innerHTML = err
    ? `Couldn't send: ${escId(err)}`
    : `✓ Check <b>${escId(email)}</b> for your sign-in link, then come back to this tab.`;
}

async function openPost(existing, kind) {
  const user = await refreshAuth();
  if (!user) { openLogin("Log in first — it's free."); return; }
  const ed = (existing && existing.id) ? existing : null;
  const k = ed ? (ed.listing_kind || "offer") : (kind || "offer");
  const W = k === "wanted";
  if (PREVIEW) { alert(`${MARKET.name} is not open on RoomKaki yet — preview only.`); return; }
  const T = hasTransit();
  const tw = MARKET.ui.transit_word || "transport";
  const sym = MARKET.ui.symbol;
  const lineOpts = T ? Object.entries(LINES).map(([c, v]) => `<option value="${escId(c)}">${escId(v.name)}</option>`).join("") : "";
  const propOpts = (MARKET.ui.property_types || []).map(([v, l]) => `<option value="${escId(v)}">${escId(l)}</option>`).join("");
  const typeOpts = `<option value="common">Common room</option><option value="single">Single room</option>
        <option value="master">Master room</option><option value="studio">Studio</option>
        <option value="whole_unit">Whole unit</option>`;
  openModal(`<h2>${ed ? "Edit post" : W ? "Looking for a room" : "Post a room"}</h2>
    ${ed ? "" : `<div class="toggle" style="margin:10px 0 6px;display:inline-flex">
      <button class="${W ? "" : "on"}" onclick="openPost(null,'offer')">I have a room</button>
      <button class="${W ? "on" : ""}" onclick="openPost(null,'wanted')">I'm looking for a room</button></div>`}
    <p class="mut">${ed ? "Edited posts go back to review before they're live again." : "Free. Reviewed before it goes live — usually same day."}</p>
    <input id="f_kind" type="hidden" value="${k}">
    <div class="form2">
      <label>${W ? "Room you want" : "Room type"}<select id="f_type">${typeOpts}</select></label>
      <label>${W ? `Budget ${sym}/month` : `Rent ${sym}/month`}<input id="f_price" type="number" min="1" placeholder="${W ? "700" : "850"}"></label>
      ${T ? `<label>${W ? `Preferred ${tw} line` : `${tw} line`}<select id="f_line">${lineOpts}</select></label>
      <label>${W ? `Near which ${tw}` : `Nearest ${tw}`}<input id="f_station" placeholder="Boon Lay"></label>
      ${W ? "" : `<label>Walk (min)<input id="f_walk" type="number" min="1" max="30" placeholder="6"></label>`}` : ""}
      <label>${W ? "Preferred area" : "Area"}<input id="f_area" placeholder="Jurong West"></label>
      <label>${W ? "Who is moving in" : "Preference"}<select id="f_gender">
        <option value="any">${W ? "Prefer not to say" : "Anyone"}</option><option value="female">${W ? "Female" : "Female only"}</option>
        <option value="male">${W ? "Male" : "Male only"}</option></select></label>
      ${W || !propOpts ? "" : `<label>Property<select id="f_hdb">${propOpts}</select></label>`}
    </div>
    <label class="full">Title<input id="f_title" maxlength="80" placeholder="${W ? "Working lady looking for common room near Jurong East" : "Bright common room, 6 min to Boon Lay MRT"}"></label>
    <label class="full">Description<textarea id="f_desc" rows="3" placeholder="${W ? "When you need it, how long you'll stay, your job, any needs…" : "Furnished, aircon, cooking allowed, available now…"}"></textarea></label>
    <label class="full">Your WhatsApp / phone<input id="f_phone" placeholder="+65 9xxx xxxx"></label>
    ${W ? "" : `<label class="full">Photos (up to 6 — first is the cover)<input id="f_photos" type="file" accept="image/*" multiple></label>`}
    <div class="checks">
      ${W ? "" : `<label class="ck"><input id="f_owner" type="checkbox" checked> I'm the owner (not an agent)</label>`}
      <label class="ck"><input id="f_cook" type="checkbox" ${W ? "" : "checked"}> ${W ? "I need to cook" : "Cooking OK"}</label>
      ${W ? "" : `<label class="ck"><input id="f_air" type="checkbox" checked> Aircon</label>`}
      <label class="ck"><input id="f_couple" type="checkbox"> ${W ? "We are a couple" : "Couple OK"}</label>
    </div>
    <button class="cta wide" id="postBtn" onclick="submitPost(${ed ? ed.id : ""})">${ed ? "Save changes" : W ? "Post what I'm looking for" : "Post my room"}</button>
    <div id="postMsg" class="mut"></div>`);
  if (ed) {
    const set = (id, v) => { const el = $("#" + id); if (el) el.value = v; };
    const chk = (id, v) => { const el = $("#" + id); if (el) el.checked = v; };
    set("f_type", ed.room_type); set("f_price", ed.price_month);
    set("f_line", ed.transit_line || "EW"); set("f_station", ed.station || "");
    set("f_walk", ed.walk_minutes || ""); set("f_area", ed.area || "");
    set("f_gender", ed.gender_pref || "any"); set("f_hdb", String(!!ed.is_hdb));
    set("f_title", ed.title || ""); set("f_desc", ed.description || "");
    set("f_phone", ed.contact_phone || "");
    chk("f_owner", !!ed.listed_by_owner); chk("f_cook", !!ed.cooking_ok);
    chk("f_air", !!ed.aircon); chk("f_couple", !!ed.couple_ok);
  }
}

// ---------- feedback (on-page, no GitHub account needed) ----------
function openFeedback() {
  const my = lang === "my";
  openModal(`<h2>${my ? "အကြံပြုချက် ပေးပါ" : "Tell us what to add or fix"}</h2>
    <p class="mut">${my ? "RoomKaki ကို ပိုကောင်းအောင် ဘာလုပ်ပေးရမလဲ? ရိုးရိုးလေး ရေးပို့လိုက်ပါ။" : "What should RoomKaki add, change or fix? Anything helps."}</p>
    <textarea id="fbMsg" rows="4" maxlength="2000" placeholder="${my ? "ဒီမှာ ရေးပါ…" : "Write here…"}"></textarea>
    <label>${my ? "ဆက်သွယ်ရန် (မဖြည့်လည်းရပါ)" : "Contact (optional)"}<input id="fbContact" maxlength="200" placeholder="email / phone / Telegram"></label>
    <input id="fbHp" style="display:none" tabindex="-1" autocomplete="off" aria-hidden="true">
    <button class="cta wide" id="fbBtn" onclick="sendFeedback()">${my ? "ပို့မယ်" : "Send"}</button>
    <div id="fbOut" class="mut"></div>`);
}

async function sendFeedback() {
  const msg = $("#fbMsg").value.trim();
  const my = lang === "my";
  if (msg.length < 3) { $("#fbOut").textContent = my ? "စာလေး အရင်ရေးပေးပါ" : "Please write a little first."; return; }
  const btn = $("#fbBtn");
  if (btn.disabled) return;
  btn.disabled = true;
  $("#fbOut").textContent = my ? "ပို့နေသည်…" : "Sending…";
  try {
    const r = await fetch(SB_URL + "/rest/v1/rpc/submit_suggestion", {
      method: "POST",
      headers: { apikey: SB_ANON, Authorization: "Bearer " + SB_ANON, "Content-Type": "application/json" },
      body: JSON.stringify({ p_site: "roomkaki", p_kind: "idea", p_message: msg,
        p_email: $("#fbContact").value.trim() || null, p_page: location.pathname, p_hp: $("#fbHp").value || null }),
    });
    const out = await r.json();
    if (out === "ok") {
      $("#modalbox").innerHTML = `<button class="close" onclick="closeModal()">✕</button>
        <h2>${my ? "✓ ရပါပြီ၊ ကျေးဇူးပါ" : "✓ Got it — thank you"}</h2>
        <p class="mut">${my ? "သေချာဖတ်ပြီး ဆောင်ရွက်ပေးပါမယ်။" : "We read every message and act on it."}</p>
        <button class="cta wide" onclick="closeModal()">${my ? "ပိတ်မယ်" : "Done"}</button>`;
    } else {
      $("#fbOut").textContent = my ? "ခဏနေ ပြန်ကြိုးစားပေးပါ" : "Please try again in a while.";
      btn.disabled = false;
    }
  } catch (e) {
    $("#fbOut").textContent = my ? "ဆက်သွယ်မှု ပြဿနာရှိနေသည် — ပြန်ကြိုးစားပါ" : "Connection problem — try again.";
    btn.disabled = false;
  }
}

// ---------- my rooms (poster's own listings) ----------
const STATUS_LABEL = { pending: "In review", live: "Live", removed: "Removed",
                       rejected: "Rejected", paused: "Paused", expired: "Expired" };

async function openMyRooms() {
  const user = await refreshAuth();
  if (!user) { openLogin("Log in to see your rooms."); return; }
  openModal(`<h2>My rooms</h2><div id="myrooms" class="mut">Loading…</div>`);
  const res = await myListings();
  const box = $("#myrooms");
  if (res.error) { box.textContent = res.error; return; }
  if (!res.rows.length) {
    box.innerHTML = `<p>You haven't posted a room yet.</p><button class="cta wide" onclick="openPost()">Post a room</button>`;
    return;
  }
  window._myRooms = {};
  box.innerHTML = res.rows.map((r) => {
    window._myRooms[r.id] = r;
    return `<div class="myroom">
      <div class="mr-main"><b>${escId(r.title)}</b><br>
        <span class="mut">${money(r.price_month)}/mo ·${escId(r.station || r.area || "")}</span>
        <span class="st st-${r.status}">${STATUS_LABEL[r.status] || r.status}</span></div>
      <div class="myacts">
        <button class="ghost sm" onclick="editListing(${r.id})">Edit</button>
        ${r.status !== "removed" ? `<button class="ghost sm" onclick="removeMine(${r.id})">Remove</button>` : ""}
      </div></div>`;
  }).join("");
}

function editListing(id) { openPost(window._myRooms && window._myRooms[id]); }

async function removeMine(id) {
  if (!confirm("Remove this listing? It will no longer be shown.")) return;
  const err = await removeListing(id);
  if (err) { alert("Couldn't remove: " + err); return; }
  openMyRooms();
}

function escId(s) {
  return String(s == null ? "" : s).replace(/[&<>"]/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
}

async function submitPost(editId) {
  const g = (id) => { const el = $("#" + id); return el ? el.value.trim() : ""; };
  const ck = (id) => { const el = $("#" + id); return el ? el.checked : false; };
  const W = g("f_kind") === "wanted";
  if (!g("f_price") || !g("f_title") || !g("f_phone")) {
    $("#postMsg").textContent = W ? "Please fill in budget, title and your contact." : "Please fill in rent, title and your contact.";
    return;
  }
  if (g("f_title").length < 8) { $("#postMsg").textContent = "Title needs at least 8 characters."; return; }
  const btn = $("#postBtn");
  if (btn) { if (btn.disabled) return; btn.disabled = true; }   // double-submit guard (crucible C16)
  $("#postMsg").textContent = editId ? "Saving…" : "Posting…";
  const f = {
    room_type: $("#f_type").value, price_month: +g("f_price"), title: g("f_title"),
    description: g("f_desc") || g("f_title"), area: g("f_area") || g("f_station") || "Singapore",
    transit_line: g("f_line") || null,
    station: g("f_station"), walk_minutes: +g("f_walk") || 0, gender_pref: $("#f_gender").value,
    is_hdb: W ? true : g("f_hdb") === "true", listed_by_owner: ck("f_owner"), cooking_ok: ck("f_cook"),
    aircon: ck("f_air"), couple_ok: ck("f_couple"), contact_phone: g("f_phone"),
    listing_kind: W ? "wanted" : "offer",
  };
  const res = editId ? await updateListing(editId, f) : await postListing(f);
  if (res.error) { $("#postMsg").textContent = "Couldn't save: " + res.error; if (btn) btn.disabled = false; return; }
  const listingId = editId || res.id;
  const files = $("#f_photos") ? $("#f_photos").files : null;
  if (files && files.length) {
    $("#postMsg").textContent = `Uploading ${Math.min(files.length, 6)} photo(s)…`;
    await uploadPhotos(listingId, files);
  }
  $("#modalbox").innerHTML = `<button class="close" onclick="closeModal()">✕</button>
    <h2>✓ ${W ? "Post" : "Room"} ${editId ? "updated" : "submitted"}</h2>
    <p class="mut">Thanks! We review ${editId ? "edited" : "new"} listings before they go live —
    usually the same day. You'll see it in the feed once it's approved.</p>
    <button class="cta wide" onclick="closeModal()">Done</button>`;
}

// ---------- markets: load config, pick one, apply to the page ----------
async function initMarket() {
  const list = await fetchMarkets();
  if (!list || !list.length) return;
  MARKETS = list;
  const q = new URLSearchParams(location.search);
  let saved = null;
  try { saved = localStorage.getItem("rk_market"); } catch (e) {}
  const pick = list.find((m) => m.id === q.get("market") && (m.active || q.has("preview")))
    || list.find((m) => m.id === saved && m.active)
    || list.find((m) => m.id === "sg") || list.find((m) => m.active);
  if (!pick) return;
  MARKET = pick;
  PREVIEW = !pick.active;
  LINES = (pick.transit_lines && Object.keys(pick.transit_lines).length) ? pick.transit_lines : {};
  applyMarketUI();
}

function applyMarketUI() {
  const lf = $("#lineFilter");
  if (lf) {
    lf.innerHTML = `<option value="All">All ${escId(MARKET.ui.transit_word || "")} lines</option>` +
      Object.entries(LINES).map(([c, v]) => `<option value="${escId(c)}">${escId(v.name)}</option>`).join("");
    lf.hidden = !hasTransit();
  }
  const pr = $("#price");
  if (pr) {
    pr.max = MARKET.ui.price_max || 3000; pr.step = MARKET.ui.price_step || 50;
    pr.min = 0; pr.value = pr.max; state.maxPrice = +pr.max;
    $("#priceLabel").textContent = "Any price";
  }
  const open = MARKETS.filter((m) => m.active);
  const box = $("#marketBox");
  if (box) {
    box.hidden = open.length < 2 && !PREVIEW;
    box.innerHTML = `<select class="chip" id="marketSel" aria-label="Country">` +
      MARKETS.filter((m) => m.active || m.id === MARKET.id).map((m) =>
        `<option value="${escId(m.id)}" ${m.id === MARKET.id ? "selected" : ""}>${escId(m.name)}${m.active ? "" : " (preview)"}</option>`).join("") +
      `</select>`;
    $("#marketSel").onchange = (e) => {
      try { localStorage.setItem("rk_market", e.target.value); } catch (err) {}
      location.href = `/?market=${encodeURIComponent(e.target.value)}`;
    };
  }
  if (PREVIEW) {
    const b = document.createElement("div");
    b.className = "previewbar";
    b.textContent = `Preview: ${MARKET.name} is not open on RoomKaki yet. Posting is switched off.`;
    document.body.prepend(b);
  }
}

// ---------- homepage guides strip ----------
async function loadGuides() {
  try {
    const r = await fetch("/blog/latest.json", { cache: "no-cache" });
    if (!r.ok) return;
    const posts = (await r.json()).slice(0, 3);
    if (!posts.length) return;
    $("#guidesGrid").innerHTML = posts.map((p) =>
      `<a class="gcard" href="/blog/${encodeURIComponent(p.slug)}.html"><b>${escId(p.title_en)}</b>
        <span>${escId(p.summary_en)}</span></a>`).join("");
    $("#guides").hidden = false;
  } catch (e) {}
}

// ---------- live data ----------
async function loadLive() {
  const live = await fetchLiveListings();
  if (live === null) {
    // backend error ≠ empty marketplace — say so and offer retry (crucible C10)
    $("#grid").innerHTML = `<div style="grid-column:1/-1;text-align:center;padding:40px">
      <p style="color:var(--mut);margin:0 0 14px">Couldn't load listings — please check your connection.</p>
      <button class="cta" onclick="loadLive()">Try again</button></div>`;
    return;
  }
  if (live.length) {
    rooms = live;
    $("#footNote").innerHTML = `<b>RoomKaki</b> — ${live.length} live listing${live.length > 1 ? "s" : ""} from our community`;
    render();
  }
  const m = location.hash.match(/^#room-(\d+)$/);
  if (m && rooms.some((r) => r.id === +m[1])) openSheet(+m[1]);
}

document.addEventListener("DOMContentLoaded", () => {
  $("#q").addEventListener("input", (e) => { state.q = e.target.value; render(); });
  $("#price").addEventListener("input", (e) => {
    state.maxPrice = +e.target.value;
    $("#priceLabel").textContent = state.maxPrice >= (MARKET.ui.price_max || 3000) ? "Any price" : `≤ ${money(e.target.value)}`;
    render();
  });
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") { closeSheet(); closeModal(); }
  });
  document.querySelectorAll("[data-filter]").forEach((el) =>
    el.addEventListener("change", () => { state[el.dataset.filter] = el.value; render(); }));
  $("#ownerOnly").addEventListener("click", (e) => {
    state.ownerOnly = !state.ownerOnly;
    e.target.classList.toggle("on", state.ownerOnly);
    render();
  });
  $("#panel").addEventListener("click", (e) => { if (e.target.id === "panel") closeSheet(); });
  $("#modal").addEventListener("click", (e) => { if (e.target.id === "modal") closeModal(); });
  applyLang();
  render();
  refreshAuth();
  initMarket().then(loadLive, loadLive);
  loadGuides();
});
