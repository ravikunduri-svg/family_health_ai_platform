(async () => {
  const session = await requireAuth();
  if (!session) return;
  setNavActive();
  showUserEmail();

  let memberMap = {};

  async function init() {
    try {
      const members = await api.getMembers() || [];
      memberMap = Object.fromEntries(members.map(m => [m.id, m.name]));
      const selectors = ["f-member", "m-member"];
      selectors.forEach(id => {
        const sel = document.getElementById(id);
        if (!sel) return;
        sel.innerHTML = (id === "f-member" ? `<option value="">All Members</option>` : `<option value="">Select</option>`) +
          members.map(m => `<option value="${m.id}">${m.name}</option>`).join("");
      });
      const paramMember = new URLSearchParams(window.location.search).get("member");
      if (paramMember) document.getElementById("f-member").value = paramMember;
      loadMeds();
    } catch (err) {
      showError(err.message);
    }
  }

  window.loadMeds = async () => {
    const params = {};
    const member = document.getElementById("f-member").value;
    const active = document.getElementById("f-active").value;
    if (member) params.member_id = member;
    if (active !== "") params.is_active = active;

    const tbody = document.getElementById("med-body");
    tbody.innerHTML = `<tr><td colspan="8" style="text-align:center;padding:20px;color:var(--text-muted)">Loading...</td></tr>`;
    try {
      const meds = await api.getMedicines(params) || [];
      renderMeds(meds);
    } catch (err) {
      showError(err.message);
    }
  };

  function renderMeds(meds) {
    const tbody = document.getElementById("med-body");
    if (!meds.length) {
      tbody.innerHTML = `<tr><td colspan="8" style="text-align:center;padding:30px;color:var(--text-muted)">No medicines found.</td></tr>`;
      return;
    }
    tbody.innerHTML = meds.map(m => `
      <tr>
        <td style="font-weight:500">${m.brand_name || "—"}</td>
        <td>${m.generic_name || "—"}</td>
        <td>${m.dosage || "—"}</td>
        <td>${m.frequency || "—"}</td>
        <td>${memberMap[m.member_id] || "—"}</td>
        <td>${formatDate(m.prescribed_date)}</td>
        <td>${m.is_active ? '<span class="badge badge-success">Active</span>' : '<span class="badge badge-muted">Stopped</span>'}</td>
        <td>
          ${m.is_active ? `<button class="btn btn-sm btn-secondary" onclick="toggleActive('${m.id}', false)">Mark stopped</button>` : `<button class="btn btn-sm btn-secondary" onclick="toggleActive('${m.id}', true)">Mark active</button>`}
          <button class="btn btn-sm btn-danger" onclick="deleteMed('${m.id}')">✕</button>
        </td>
      </tr>
    `).join("");
  }

  window.openAddModal = () => {
    document.getElementById("med-modal").style.display = "flex";
  };

  window.saveMed = async () => {
    const memberId = document.getElementById("m-member").value;
    if (!memberId) { showError("Select a family member"); return; }
    const payload = {
      member_id: memberId,
      brand_name: document.getElementById("m-brand").value.trim() || null,
      generic_name: document.getElementById("m-generic").value.trim() || null,
      dosage: document.getElementById("m-dose").value.trim() || null,
      frequency: document.getElementById("m-freq").value.trim() || null,
      prescribed_date: document.getElementById("m-date").value || null,
      duration_days: parseInt(document.getElementById("m-duration").value) || null,
      prescribed_by: document.getElementById("m-doctor").value.trim() || null,
      is_active: document.getElementById("m-active").value === "true",
    };
    try {
      await api.createMedicine(payload);
      document.getElementById("med-modal").style.display = "none";
      showToast("Medicine added");
      loadMeds();
    } catch (err) {
      showError(err.message);
    }
  };

  window.toggleActive = async (id, isActive) => {
    try {
      await api.updateMedicine(id, { is_active: isActive });
      showToast(isActive ? "Marked active" : "Marked stopped");
      loadMeds();
    } catch (err) {
      showError(err.message);
    }
  };

  window.deleteMed = async (id) => {
    if (!confirm("Remove this medicine record?")) return;
    try {
      await api.deleteMedicine(id);
      showToast("Medicine removed");
      loadMeds();
    } catch (err) {
      showError(err.message);
    }
  };

  init();
})();
