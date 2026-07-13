let state = { type: "All", line: "All", gender: "All", ownerOnly: false, maxPrice: 1600, q: "", view: "grid" };
let map, markers = [];

const $ = (s) => document.querySelector(s);

function lineDot(l) {
  return `<span class="dot" style="background:${LINES[l].color}">${l}</span>`;
}

function filtered() {
  return LISTINGS.filter((r) =>
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
    <div class="ph" style="background:linear-gradient(135deg,${r.grad[0]},${r.grad[1]})">
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
  const r = LISTINGS.find((x) => x.id === id);
  $("#sheet").innerHTML = `
    <button class="close" onclick="closeSheet()">✕</button>
    <div class="ph" style="background:linear-gradient(135deg,${r.grad[0]},${r.grad[1]})"></div>
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
      <div class="contact">
        <button class="cta" onclick="alert('Prototype: contact reveal will show phone/WhatsApp after backend is live.')">Show contact</button>
        <button class="ghost" onclick="alert('Prototype: report flow coming with backend.')">Report</button>
      </div>
    </div>`;
  $("#panel").classList.add("open");
}
function closeSheet() { $("#panel").classList.remove("open"); }

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
  render();
});
