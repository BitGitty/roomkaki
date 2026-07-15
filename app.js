let state = { type: "All", line: "All", gender: "All", ownerOnly: false, maxPrice: 1600, q: "", view: "grid" };
let map, markers = [];
let rooms = (typeof LISTINGS !== "undefined") ? LISTINGS.slice() : [];  // demo until live data arrives

const $ = (s) => document.querySelector(s);

function lineDot(l) {
  return `<span class="dot" style="background:${LINES[l].color}">${l}</span>`;
}

function phBg(r) {
  return (r.photos && r.photos.length)
    ? `background-image:url('${r.photos[0]}');background-size:cover;background-position:center`
    : `background:linear-gradient(135deg,${r.grad[0]},${r.grad[1]})`;
}

function filtered() {
  return rooms.filter((r) =>
    (state.type === "All" || r.type === state.type) &&
    (state.line === "All" || r.line === state.line) &&
    (state.gender === "All" || r.gender === state.gender || r.gender === "Any") &&
    (!state.ownerOnly || r.owner) &&
    r.price <= state.maxPrice &&
    (state.q === "" || (r.title + r.area + r.station).toLowerCase().includes(state.q.toLowerCase()))
  );
}

function card(r) {
  return `<article class="card" onclick="openSheet(${r.id})">
    <div class="ph" style="${phBg(r)}">
      <span class="badge ${r.owner ? "owner" : "agent"}">${r.owner ? "Owner direct" : "Agent"}</span>
      <span class="badge">${r.type}</span>
    </div>
    <div class="body">
      <div class="price">S$${r.price}<small>/month</small></div>
      <h3>${r.title}</h3>
      <div class="mrt">${lineDot(r.line)} ${r.station} · ${r.walk} min walk</div>
      <div class="tags">
        ${r.verified ? '<span class="tag v">✓ Verified poster</span>' : ""}
        <span class="tag">${r.gender}</span>
        ${r.cooking ? '<span class="tag">Cooking OK</span>' : ""}
        ${r.aircon ? '<span class="tag">Aircon</span>' : ""}
        ${r.couple ? '<span class="tag">Couple OK</span>' : ""}
      </div>
      <div class="meta">${r.days === 0 ? "Posted today" : `Posted ${r.days}d ago`} · ${r.area}</div>
    </div>
  </article>`;
}

function render() {
  const list = filtered();
  $("#count").textContent = `${list.length} rooms`;
  $("#grid").innerHTML = list.map(card).join("") ||
    '<p style="grid-column:1/-1;text-align:center;color:var(--mut);padding:40px">No rooms match — try widening the filters.</p>';
  if (state.view === "map") renderMap(list);
}

function renderMap(list) {
  if (!map) {
    map = L.map("map").setView([1.3521, 103.8198], 11);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
      { attribution: "© OpenStreetMap" }).addTo(map);
  }
  markers.forEach((m) => m.remove());
  markers = list.map((r) =>
    L.marker([r.lat, r.lng]).addTo(map)
      .bindPopup(`<b>S$${r.price}</b> · ${r.type}<br>${r.station} ${r.walk}min<br>
        <a href="#" onclick="openSheet(${r.id});return false">View room →</a>`));
}

function setView(v) {
  state.view = v;
  $("#grid").style.display = v === "grid" ? "grid" : "none";
  $("#map").style.display = v === "map" ? "block" : "none";
  document.querySelectorAll(".toggle button").forEach((b) => b.classList.toggle("on", b.dataset.v === v));
  if (v === "map") { render(); setTimeout(() => map.invalidateSize(), 60); }
}

function openSheet(id) {
  const r = rooms.find((x) => x.id === id);
  $("#sheet").innerHTML = `
    <button class="close" onclick="closeSheet()">✕</button>
    <div class="ph" style="${phBg(r)}"></div>
    ${r.photos && r.photos.length > 1
      ? `<div class="photostrip">${r.photos.slice(1).map((u) => `<img src="${u}" loading="lazy" alt="room photo">`).join("")}</div>`
      : ""}
    <div class="inner">
      <div class="price">S$${r.price}<small>/month</small></div>
      <h2>${r.title}</h2>
      <div class="my">${r.my}</div>
      <div class="mrt">${lineDot(r.line)} ${LINES[r.line].name} line · ${r.station} · ${r.walk} min walk</div>
      <div class="safety">🛡️ <b>Stay safe:</b> never transfer a deposit before viewing the room in person.
        ${r.hdb ? `HDB rules: minimum ${r.minStay}-month stay applies.` : `Condo listing — minimum ${r.minStay} months.`}</div>
      <p>${r.desc}</p>
      <div class="facts">
        <div><b>Room type</b>${r.type}</div>
        <div><b>Preference</b>${r.gender}${r.couple ? " · couples OK" : ""}</div>
        <div><b>Cooking</b>${r.cooking ? "Allowed" : "Not allowed"}</div>
        <div><b>Comfort</b>${[r.aircon ? "Aircon" : "Fan", r.wifi ? "WiFi" : null].filter(Boolean).join(" · ")}</div>
        <div><b>Listed by</b>${r.owner ? "Owner (no commission)" : "Agent"}</div>
        <div><b>Poster</b>${r.verified ? "✓ Phone-verified" : "Unverified"}</div>
      </div>
      <div class="contact" id="contactBox">
        ${r._real
          ? `<button class="cta" onclick="doReveal(${r.id})">Show contact</button>
             <button class="ghost" onclick="doReport(${r.id})">Report</button>`
          : `<button class="cta" onclick="alert('Demo listing — real contact reveal works on live posts.')">Show contact</button>
             <button class="ghost" onclick="alert('Demo listing — reporting works on live posts.')">Report</button>`}
      </div>
    </div>`;
  $("#panel").classList.add("open");
}

async function doReveal(id) {
  if (!(await currentUser())) { openLogin("Log in to see the poster's contact — it's free."); return; }
  const box = $("#contactBox");
  box.innerHTML = "<span class='mut'>Revealing…</span>";
  const res = await revealContact(id);
  if (res.error) { box.innerHTML = `<span class='mut'>Couldn't reveal: ${res.error}</span>`; return; }
  const phone = res.phone;
  const wa = (phone || "").replace(/[^0-9]/g, "");
  box.innerHTML = `<a class="cta" href="https://wa.me/${wa}" target="_blank" rel="noopener">WhatsApp ${phone}</a>
    <a class="ghost" href="tel:${phone}">Call ${phone}</a>`;
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
function closeSheet() { $("#panel").classList.remove("open"); }

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
    slot.innerHTML = `<span class="who">${(user.email || "member").split("@")[0]}</span>
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
    ? `Couldn't send: ${err}`
    : `✓ Check <b>${email}</b> for your sign-in link, then come back to this tab.`;
}

async function openPost() {
  const user = await refreshAuth();
  if (!user) { openLogin("Log in first, then post your room."); return; }
  openModal(`<h2>Post a room</h2>
    <p class="mut">Free. Reviewed before it goes live — usually same day.</p>
    <div class="form2">
      <label>Room type<select id="f_type">
        <option value="common">Common room</option><option value="single">Single room</option>
        <option value="master">Master room</option><option value="studio">Studio</option>
        <option value="whole_unit">Whole unit</option></select></label>
      <label>Rent S$/month<input id="f_price" type="number" min="200" max="6000" placeholder="850"></label>
      <label>MRT line<select id="f_line">
        <option value="EW">East West</option><option value="NS">North South</option>
        <option value="NE">North East</option><option value="CC">Circle</option>
        <option value="DT">Downtown</option><option value="TE">Thomson-East Coast</option></select></label>
      <label>Nearest MRT<input id="f_station" placeholder="Boon Lay"></label>
      <label>Walk (min)<input id="f_walk" type="number" min="1" max="30" placeholder="6"></label>
      <label>Area<input id="f_area" placeholder="Jurong West"></label>
      <label>Preference<select id="f_gender">
        <option value="any">Anyone</option><option value="female">Female only</option>
        <option value="male">Male only</option></select></label>
      <label>Property<select id="f_hdb"><option value="true">HDB</option><option value="false">Condo</option></select></label>
    </div>
    <label class="full">Title<input id="f_title" maxlength="80" placeholder="Bright common room, 6 min to Boon Lay MRT"></label>
    <label class="full">Description<textarea id="f_desc" rows="3" placeholder="Furnished, aircon, cooking allowed, available now…"></textarea></label>
    <label class="full">Your WhatsApp / phone<input id="f_phone" placeholder="+65 9xxx xxxx"></label>
    <label class="full">Photos (up to 6 — first is the cover)<input id="f_photos" type="file" accept="image/*" multiple></label>
    <div class="checks">
      <label class="ck"><input id="f_owner" type="checkbox" checked> I'm the owner (not an agent)</label>
      <label class="ck"><input id="f_cook" type="checkbox" checked> Cooking OK</label>
      <label class="ck"><input id="f_air" type="checkbox" checked> Aircon</label>
      <label class="ck"><input id="f_couple" type="checkbox"> Couple OK</label>
    </div>
    <button class="cta wide" onclick="submitPost()">Post my room</button>
    <div id="postMsg" class="mut"></div>`);
}

async function submitPost() {
  const g = (id) => $("#" + id).value.trim();
  const ck = (id) => $("#" + id).checked;
  if (!g("f_price") || !g("f_title") || !g("f_phone")) {
    $("#postMsg").textContent = "Please fill in rent, title and your contact.";
    return;
  }
  if (g("f_title").length < 8) { $("#postMsg").textContent = "Title needs at least 8 characters."; return; }
  $("#postMsg").textContent = "Posting…";
  const res = await postListing({
    room_type: $("#f_type").value, price_month: +g("f_price"), title: g("f_title"),
    description: g("f_desc") || g("f_title"), area: g("f_area") || g("f_station") || "Singapore",
    transit_line: $("#f_line").value,
    station: g("f_station"), walk_minutes: +g("f_walk") || 0, gender_pref: $("#f_gender").value,
    is_hdb: $("#f_hdb").value === "true", listed_by_owner: ck("f_owner"), cooking_ok: ck("f_cook"),
    aircon: ck("f_air"), couple_ok: ck("f_couple"), contact_phone: g("f_phone"),
  });
  if (res.error) { $("#postMsg").textContent = "Couldn't post: " + res.error; return; }
  const files = $("#f_photos").files;
  if (files && files.length) {
    $("#postMsg").textContent = `Uploading ${Math.min(files.length, 6)} photo(s)…`;
    await uploadPhotos(res.id, files);
  }
  $("#modalbox").innerHTML = `<button class="close" onclick="closeModal()">✕</button>
    <h2>✓ Room submitted</h2>
    <p class="mut">Thanks! We review new listings before they go live — usually the same day.
    You'll see it in the feed once it's approved.</p>
    <button class="cta wide" onclick="closeModal()">Done</button>`;
}

// ---------- live data ----------
async function loadLive() {
  const live = await fetchLiveListings();
  if (live.length) {
    rooms = live;
    $("#footNote").innerHTML = `<b>RoomKaki</b> — ${live.length} live listing${live.length > 1 ? "s" : ""} from our community`;
    render();
  }
}

document.addEventListener("DOMContentLoaded", () => {
  $("#q").addEventListener("input", (e) => { state.q = e.target.value; render(); });
  $("#price").addEventListener("input", (e) => {
    state.maxPrice = +e.target.value;
    $("#priceLabel").textContent = `≤ S$${e.target.value}`;
    render();
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
  render();
  refreshAuth();
  loadLive();
});
