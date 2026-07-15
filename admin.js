const $ = (s) => document.querySelector(s);
const ROOM = { common: "Common room", single: "Single room", master: "Master room",
               studio: "Studio", whole_unit: "Whole unit" };

async function load() {
  const user = await currentUser();
  if (!user) {
    $("#who").innerHTML = "";
    $("#list").innerHTML = `<div class="empty">Please <a href="./">log in</a> as the admin first.</div>`;
    return;
  }
  $("#who").innerHTML = `<span class="who">${(user.email || "").split("@")[0]}</span>
    <button class="lang" onclick="logout().then(()=>location.reload())">Log out</button>`;
  const res = await adminPending();
  if (res.error) {
    $("#list").innerHTML = `<div class="empty">${res.error.includes("not authorized")
      ? "This account isn't an admin." : "Couldn't load: " + res.error}</div>`;
    return;
  }
  render(res.rows);
}

function render(rows) {
  if (!rows.length) { $("#list").innerHTML = `<div class="empty">🎉 Nothing pending — all caught up.</div>`; return; }
  $("#list").innerHTML = rows.map((r) => `
    <div class="pend" id="pend-${r.id}">
      <h3>${esc(r.title)}</h3>
      <div class="row">${ROOM[r.room_type] || r.room_type} · <b>S$${r.price_month}/mo</b> ·
        ${esc(r.area || "")} · ${esc(r.station || "")} (${esc(r.transit_line || "")}) · ${esc(r.gender_pref)}</div>
      <div class="row">📞 ${esc(r.contact_phone)} · ${r.is_hdb ? "HDB" : "Condo"} ·
        ${r.listed_by_owner ? "owner" : "agent"} · posted ${new Date(r.created_at).toLocaleDateString()}</div>
      <div class="desc">${esc(r.description || "")}</div>
      <div class="acts">
        <button class="approve" onclick="act(${r.id},'live')">✓ Approve &amp; publish</button>
        <button class="reject" onclick="act(${r.id},'rejected')">Reject</button>
      </div>
    </div>`).join("");
}

async function act(id, status) {
  const card = $(`#pend-${id}`);
  card.style.opacity = ".5";
  const res = await adminModerate(id, status);
  if (res.error) { card.style.opacity = "1"; $("#msg").textContent = "Error: " + res.error; return; }
  card.remove();
  $("#msg").textContent = status === "live" ? "✓ Published." : "Rejected.";
  if (!document.querySelector(".pend")) $("#list").innerHTML = `<div class="empty">🎉 Nothing pending — all caught up.</div>`;
}

function esc(s) {
  return String(s == null ? "" : s).replace(/[&<>"]/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
}

document.addEventListener("DOMContentLoaded", load);
