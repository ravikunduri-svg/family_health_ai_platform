/**
 * Shared API client. Loaded on every page after config.js.
 * Uses Supabase JS for auth; forwards Bearer token to FastAPI backend.
 */

const { API_BASE, SUPABASE_URL, SUPABASE_ANON_KEY } = window.APP_CONFIG;

// Supabase client (auth only — data goes through our FastAPI)
const _supa = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

// ── Auth helpers ──────────────────────────────────────────────────

async function getSession() {
  const { data } = await _supa.auth.getSession();
  return data.session;
}

async function requireAuth() {
  const session = await getSession();
  if (!session) {
    window.location.href = "/login.html";
    return null;
  }
  return session;
}

async function signOut() {
  await _supa.auth.signOut();
  window.location.href = "/login.html";
}

async function sendMagicLink(email) {
  const { error } = await _supa.auth.signInWithOtp({
    email,
    options: { emailRedirectTo: window.location.origin },
  });
  if (error) throw error;
}

// Handle magic link redirect (call on every page load)
async function handleAuthRedirect() {
  const { data, error } = await _supa.auth.getSession();
  if (error) console.error("Auth redirect error:", error.message);
  return data.session;
}

// ── API fetch wrapper ─────────────────────────────────────────────

async function apiFetch(path, options = {}) {
  const session = await requireAuth();
  if (!session) return null;

  const url = `${API_BASE}${path}`;
  const headers = {
    Authorization: `Bearer ${session.access_token}`,
    ...(options.headers || {}),
  };

  const resp = await fetch(url, { ...options, headers });

  if (resp.status === 401) {
    // Token expired — send back to login
    window.location.href = "/login.html";
    return null;
  }

  if (!resp.ok) {
    let detail = `HTTP ${resp.status}`;
    try {
      const body = await resp.json();
      detail = body.detail || detail;
    } catch (_) {}
    throw new Error(detail);
  }

  if (resp.status === 204) return null;
  return resp.json();
}

// ── Convenience wrappers ──────────────────────────────────────────

const api = {
  // Members
  getMembers: () => apiFetch("/api/members"),
  getMember: (id) => apiFetch(`/api/members/${id}`),
  createMember: (data) => apiFetch("/api/members", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(data) }),
  updateMember: (id, data) => apiFetch(`/api/members/${id}`, { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify(data) }),
  deleteMember: (id) => apiFetch(`/api/members/${id}`, { method: "DELETE" }),

  // Documents
  uploadDocument: (formData) => apiFetch("/api/documents/upload", { method: "POST", body: formData }),
  getDocuments: (params) => apiFetch("/api/documents?" + new URLSearchParams(params || {}).toString()),
  getDocument: (id) => apiFetch(`/api/documents/${id}`),
  deleteDocument: (id) => apiFetch(`/api/documents/${id}`, { method: "DELETE" }),
  reprocessDocument: (id) => apiFetch(`/api/documents/${id}/reprocess`, { method: "POST" }),

  // Lab values
  getLabValues: (params) => apiFetch("/api/lab-values?" + new URLSearchParams(params || {}).toString()),
  updateLabValue: (id, data) => apiFetch(`/api/lab-values/${id}`, { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify(data) }),
  deleteLabValue: (id) => apiFetch(`/api/lab-values/${id}`, { method: "DELETE" }),

  // Trends
  getTrend: (memberId, testName, params) => apiFetch("/api/trends?" + new URLSearchParams({ member_id: memberId, test_name: testName, ...params }).toString()),

  // Medicines
  getMedicines: (params) => apiFetch("/api/medicines?" + new URLSearchParams(params || {}).toString()),
  createMedicine: (data) => apiFetch("/api/medicines", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(data) }),
  updateMedicine: (id, data) => apiFetch(`/api/medicines/${id}`, { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify(data) }),
  deleteMedicine: (id) => apiFetch(`/api/medicines/${id}`, { method: "DELETE" }),

  // Events
  getEvents: (params) => apiFetch("/api/events?" + new URLSearchParams(params || {}).toString()),
  createEvent: (data) => apiFetch("/api/events", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(data) }),
  updateEvent: (id, data) => apiFetch(`/api/events/${id}`, { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify(data) }),
  deleteEvent: (id) => apiFetch(`/api/events/${id}`, { method: "DELETE" }),

  // Alerts
  getAlerts: (params) => apiFetch("/api/alerts?" + new URLSearchParams(params || {}).toString()),
  dismissAlert: (id) => apiFetch(`/api/alerts/${id}/dismiss`, { method: "POST" }),

  // Summary
  getSummary: (memberId) => apiFetch(`/api/summary/${memberId}`),

  // Search
  search: (q, memberId) => apiFetch("/api/search?" + new URLSearchParams({ q, ...(memberId ? { member_id: memberId } : {}) }).toString()),

  // Ask
  ask: (memberId, q) => apiFetch("/api/ask?" + new URLSearchParams({ member_id: memberId, q }).toString()),
};

// ── UI helpers ────────────────────────────────────────────────────

function showError(msg) {
  const el = document.getElementById("error-banner");
  if (el) { el.textContent = msg; el.style.display = "flex"; }
  else console.error(msg);
}

function hideError() {
  const el = document.getElementById("error-banner");
  if (el) el.style.display = "none";
}

function showToast(msg, type = "success") {
  const t = document.createElement("div");
  t.className = `alert-banner ${type}`;
  t.style.cssText = "position:fixed;bottom:20px;right:20px;z-index:9999;max-width:320px;";
  t.textContent = msg;
  document.body.appendChild(t);
  setTimeout(() => t.remove(), 3500);
}

function formatDate(str) {
  if (!str) return "—";
  return new Date(str).toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" });
}

function setNavActive() {
  const path = window.location.pathname.split("/").pop() || "index.html";
  document.querySelectorAll(".sidebar-nav a").forEach((a) => {
    const href = a.getAttribute("href").split("/").pop();
    a.classList.toggle("active", href === path);
  });
}

async function showUserEmail() {
  const session = await getSession();
  const el = document.querySelector(".user-email");
  if (el && session) el.textContent = session.user.email;
}
