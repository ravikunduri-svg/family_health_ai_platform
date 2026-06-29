(async () => {
  const session = await requireAuth();
  if (!session) return;
  setNavActive();
  showUserEmail();

  let memberMap = {};
  let debounceTimer;

  // Load members for filter
  try {
    const members = await api.getMembers() || [];
    memberMap = Object.fromEntries(members.map(m => [m.id, m.name]));
    const sel = document.getElementById("f-member");
    sel.innerHTML = `<option value="">All Members</option>` +
      members.map(m => `<option value="${m.id}">${m.name}</option>`).join("");
    // Pre-select from query param
    const p = new URLSearchParams(window.location.search).get("member");
    if (p) { sel.value = p; }
  } catch (err) {
    showError(err.message);
  }

  window.loadDocs = () => {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(_loadDocs, 300);
  };

  async function _loadDocs() {
    const params = {};
    const q = document.getElementById("f-search").value.trim();
    const member = document.getElementById("f-member").value;
    const type = document.getElementById("f-type").value;
    const from = document.getElementById("f-from").value;
    const to = document.getElementById("f-to").value;
    if (q) params.q = q;
    if (member) params.member_id = member;
    if (type) params.document_type = type;
    if (from) params.date_from = from;
    if (to) params.date_to = to;

    const tbody = document.getElementById("docs-body");
    tbody.innerHTML = `<tr><td colspan="7" style="text-align:center;padding:20px;color:var(--text-muted)">Loading...</td></tr>`;
    try {
      const docs = await api.getDocuments(params) || [];
      renderDocs(docs);
    } catch (err) {
      showError(err.message);
    }
  }

  function renderDocs(docs) {
    const tbody = document.getElementById("docs-body");
    if (!docs.length) {
      tbody.innerHTML = `<tr><td colspan="7" style="text-align:center;padding:30px;color:var(--text-muted)">No documents found.</td></tr>`;
      return;
    }
    const typeLabel = { blood_report: "Blood Report", prescription: "Prescription", imaging: "Imaging", vaccination: "Vaccination", other: "Other" };
    const statusBadge = (s) => {
      const map = { pending: "muted", processing: "info", done: "success", failed: "danger", done_no_ai: "warning" };
      return `<span class="badge badge-${map[s] || 'muted'}">${s.replace("_", " ")}</span>`;
    };
    tbody.innerHTML = docs.map(d => `
      <tr>
        <td><a href="document.html?id=${d.id}" style="font-weight:500">${d.title}</a></td>
        <td>${memberMap[d.member_id] || "—"}</td>
        <td>${typeLabel[d.document_type] || d.document_type}</td>
        <td>${formatDate(d.report_date)}</td>
        <td>${d.facility_name || "—"}</td>
        <td>${statusBadge(d.ocr_status)}</td>
        <td>
          <button class="btn btn-sm btn-danger" onclick="deleteDoc('${d.id}')">Delete</button>
        </td>
      </tr>
    `).join("");
  }

  window.deleteDoc = async (id) => {
    if (!confirm("Delete this document and all extracted data?")) return;
    try {
      await api.deleteDocument(id);
      showToast("Document deleted");
      _loadDocs();
    } catch (err) {
      showError(err.message);
    }
  };

  _loadDocs();
})();
