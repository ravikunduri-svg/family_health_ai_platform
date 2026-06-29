(async () => {
  const session = await requireAuth();
  if (!session) return;
  setNavActive();
  showUserEmail();

  let members = [];

  async function loadMembers() {
    try {
      members = await api.getMembers() || [];
      renderGrid();
    } catch (err) {
      showError(err.message);
    }
  }

  function renderGrid() {
    const grid = document.getElementById("member-grid");
    if (!members.length) {
      grid.innerHTML = `<div class="empty-state" style="grid-column:1/-1"><div class="empty-icon">👥</div><h3>No family members yet</h3><p>Add members to start tracking their health records.</p></div>`;
      return;
    }
    grid.innerHTML = members.map(m => `
      <div class="member-card">
        <div class="member-avatar">${m.name[0].toUpperCase()}</div>
        <div class="member-name">${m.name}</div>
        <div class="member-meta">${m.relationship || ""}${m.dob ? " · " + formatDate(m.dob) : ""}${m.blood_type ? " · " + m.blood_type : ""}</div>
        ${m.allergies?.length ? `<div style="margin-top:8px"><span class="badge badge-danger">Allergy: ${m.allergies.join(", ")}</span></div>` : ""}
        ${m.chronic_conditions?.length ? `<div style="margin-top:4px"><span class="badge badge-warning">${m.chronic_conditions.join(", ")}</span></div>` : ""}
        <div style="margin-top:12px;display:flex;gap:8px">
          <a href="timeline.html?member=${m.id}" class="btn btn-sm btn-ghost">Timeline</a>
          <button class="btn btn-sm btn-secondary" onclick="openEditModal('${m.id}')">Edit</button>
          <button class="btn btn-sm btn-danger" onclick="deleteMember('${m.id}')">Delete</button>
        </div>
      </div>
    `).join("");
  }

  window.openAddModal = () => {
    document.getElementById("modal-title").textContent = "Add Family Member";
    document.getElementById("edit-id").value = "";
    ["name","relation","dob","gender","blood","allergies","conditions","notes"].forEach(f => {
      const el = document.getElementById("f-" + f);
      if (el) el.value = "";
    });
    document.getElementById("member-modal").style.display = "flex";
  };

  window.openEditModal = (id) => {
    const m = members.find(x => x.id === id);
    if (!m) return;
    document.getElementById("modal-title").textContent = "Edit Family Member";
    document.getElementById("edit-id").value = id;
    document.getElementById("f-name").value = m.name || "";
    document.getElementById("f-relation").value = m.relationship || "";
    document.getElementById("f-dob").value = m.dob || "";
    document.getElementById("f-gender").value = m.gender || "";
    document.getElementById("f-blood").value = m.blood_type || "";
    document.getElementById("f-allergies").value = (m.allergies || []).join(", ");
    document.getElementById("f-conditions").value = (m.chronic_conditions || []).join(", ");
    document.getElementById("f-notes").value = m.notes || "";
    document.getElementById("member-modal").style.display = "flex";
  };

  window.closeModal = () => {
    document.getElementById("member-modal").style.display = "none";
  };

  window.saveMember = async () => {
    const id = document.getElementById("edit-id").value;
    const name = document.getElementById("f-name").value.trim();
    if (!name) { showError("Name is required"); return; }

    const payload = {
      name,
      relationship: document.getElementById("f-relation").value || null,
      dob: document.getElementById("f-dob").value || null,
      gender: document.getElementById("f-gender").value || null,
      blood_type: document.getElementById("f-blood").value || null,
      allergies: document.getElementById("f-allergies").value.split(",").map(s => s.trim()).filter(Boolean),
      chronic_conditions: document.getElementById("f-conditions").value.split(",").map(s => s.trim()).filter(Boolean),
      notes: document.getElementById("f-notes").value || null,
    };

    try {
      if (id) {
        await api.updateMember(id, payload);
        showToast("Member updated");
      } else {
        await api.createMember(payload);
        showToast("Member added");
      }
      closeModal();
      loadMembers();
    } catch (err) {
      showError(err.message);
    }
  };

  window.deleteMember = async (id) => {
    if (!confirm("Delete this family member and all their records? This cannot be undone.")) return;
    try {
      await api.deleteMember(id);
      showToast("Member deleted");
      loadMembers();
    } catch (err) {
      showError(err.message);
    }
  };

  loadMembers();
})();
