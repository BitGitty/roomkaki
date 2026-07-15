// RoomKaki ↔ Supabase: auth (email), live listings, posting, contact reveal, reports.
// Anon key is public/client-safe by design.
const SB_URL = "https://uumiwuvbxzmtxuwmutis.supabase.co";
const SB_ANON = "sb_publishable_E2ECaIgR-2fLWAEeDfVnMA_5_balO9b";
const sb = window.supabase.createClient(SB_URL, SB_ANON);

const ROOM_TYPE = { common: "Common room", single: "Single room", master: "Master room",
                    studio: "Studio", whole_unit: "Whole unit" };
const GENDER = { any: "Any", female: "Female only", male: "Male only" };
const GRADS = [["#0d9488", "#0a6f66"], ["#3b6ea5", "#274b73"], ["#8a5a44", "#5e3a2a"],
               ["#7a5ea7", "#4e3d70"], ["#b08948", "#7c5f27"], ["#4a8577", "#2f5a4f"]];

function daysAgo(iso) {
  const d = Math.floor((Date.now() - new Date(iso).getTime()) / 86400000);
  return Math.max(0, d);
}

// map a public_listings row to the shape cards/sheets already expect
function mapRow(r) {
  return {
    id: r.id, price: r.price_month, type: ROOM_TYPE[r.room_type] || r.room_type,
    title: r.title, my: (r.title_i18n && r.title_i18n.my) || "", desc: r.description,
    line: r.transit_line || "EW", station: r.station || "", walk: r.walk_minutes || 0,
    area: r.area, gender: GENDER[r.gender_pref] || "Any", owner: !!r.listed_by_owner,
    verified: false, cooking: !!r.cooking_ok, aircon: !!r.aircon, couple: !!r.couple_ok,
    wifi: r.wifi !== false, hdb: r.is_hdb !== false, minStay: r.is_hdb === false ? 3 : 6,
    lat: r.lat, lng: r.lng, days: daysAgo(r.created_at), grad: GRADS[r.id % GRADS.length],
    _real: true,
  };
}

async function fetchLiveListings() {
  const { data, error } = await sb.from("public_listings")
    .select("*").order("created_at", { ascending: false });
  if (error) { console.warn("listings:", error.message); return []; }
  return data.map(mapRow);
}

// ---- auth (email magic link / OTP) ----
async function currentUser() {
  const { data } = await sb.auth.getUser();
  return data.user || null;
}
async function sendLogin(email) {
  const { error } = await sb.auth.signInWithOtp({
    email, options: { emailRedirectTo: window.location.origin + window.location.pathname } });
  return error ? error.message : null;
}
async function logout() { await sb.auth.signOut(); }

// ---- posting ----
async function ensureProfile(user, displayName) {
  await sb.from("profiles").upsert(
    { id: user.id, display_name: displayName || (user.email || "member").split("@")[0] },
    { onConflict: "id" });
}
async function postListing(f) {
  const user = await currentUser();
  if (!user) return { error: "Please sign in first." };
  await ensureProfile(user, f.display_name);
  const { data, error } = await sb.from("listings").insert({
    poster_id: user.id, room_type: f.room_type, price_month: f.price_month,
    title: f.title, description: f.description, area: f.area,
    transit_line: f.transit_line, station: f.station, walk_minutes: f.walk_minutes,
    gender_pref: f.gender_pref, is_hdb: f.is_hdb, listed_by_owner: f.listed_by_owner,
    cooking_ok: f.cooking_ok, aircon: f.aircon, couple_ok: f.couple_ok,
    contact_phone: f.contact_phone,
  }).select("id").single();
  if (error) return { error: error.message };
  return { id: data.id };
}
async function reportListing(listingId, reason, detail) {
  const { error } = await sb.from("reports").insert({ listing_id: listingId, reason, detail });
  return error ? error.message : null;
}
async function revealContact(listingId) {
  const { data, error } = await sb.rpc("reveal_contact", { p_listing_id: listingId });
  return error ? { error: error.message } : { phone: data };
}
