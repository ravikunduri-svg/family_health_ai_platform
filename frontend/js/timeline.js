(async () => {
  const session = await requireAuth();
  if (!session) return;
  setNavActive();
  showUserEmail();

  const EVENT_ICONS = { diagnosis: "🔬", procedure: "🏥", hospitalization: "🏨", vaccination: "💉", symptom: "🤒", followup: "📅" };

  try {
    const members = await api.getMembers() || [];
    const sel = document.getElementById("f-member");
    sel.innerHTML = `<option value="">Select member</option>` +
      members.map(m => `<option value="${m.id}">${m.name}</option>`).join("");
    const param = new URLSearchParams(window.location.search).get("member");
    if (param) { sel.value = param; loadTimeline(); }
  } catch (err) {
    showError(err.message);
  }

  window.loadTimeline = async () => {
    const memberId = document.getElementById("f-member").value;
    const type = document.getElementById("f-type").value;
    const wrap = document.getElementById("timeline-wrap");

    if (!memberId) {
      wrap.innerHTML = `<div class="empty-state"><div class="empty-icon">📅</div><h3>Select a family member</h3></div>`;
      return;
    }

    wrap.innerHTML = `<div style="color:var(--text-muted);padding:20px">Loading...</div>`;
    try {
      const params = { member_id: memberId };
      if (type) params.event_type = type;
      const events = await api.getEvents(params) || [];
      renderTimeline(events);
    } catch (err) {
      showError(err.message);
    }
  };

  function renderTimeline(events) {
    const wrap = document.getElementById("timeline-wrap");
    if (!events.length) {
      wrap.innerHTML = `<div class="empty-state"><div class="empty-icon">📅</div><h3>No events recorded</h3><p>Events are extracted from uploaded documents or can be added manually.</p><button class="btn btn-primary" onclick="openAddModal()" style="margin-top:12px">+ Add Event</button></div>`;
      return;
    }

    const addBtn = `<div style="margin-bottom:20px"><button class="btn btn-primary btn-sm" onclick="openAddModal()">+ Add Event</button></div>`;
    const timeline = `
      <div class="timeline">
        ${events.map(e => `
          <div class="timeline-item">
            <div class="timeline-date">${formatDate(e.event_date)}</div>
            <div class="timeline-title">${EVENT_ICONS[e.event_type] || "📌"} ${e.title}</div>
            <div class="timeline-sub">
              <span class="badge badge-info">${e.event_type}</span>
              ${e.doctor_name ? ` · ${e.doctor_name}` : ""}
              ${e.facility_name ? ` · ${e.facility_name}` : ""}
            </div>
            ${e.notes ? `<div style="font-size:12px;color:var(--text-muted);margin-top:4px">${e.notes}</div>` : ""}
          </div>
        `).join("")}
      </div>
    `;
    wrap.innerHTML = addBtn + timeline;
  }

  window.openAddModal = () => {
    const memberId = document.getElementById("f-member").value;
    if (!memberId) { showError("Select a member first"); return; }
    const title = prompt("Event title (e.g. 'Type 2 Diabetes diagnosed'):");
    if (!title) return;
    const date = prompt("Event date (YYYY-MM-DD):");
    const type = prompt("Event type (diagnosis/procedure/hospitalization/vaccination/symptom/followup):", "diagnosis");

    api.createEvent({ member_id: memberId, title, event_date: date || null, event_type: type || "diagnosis" })
      .then(() => { showToast("Event added"); loadTimeline(); })
      .catch(err => showError(err.message));
  };
})();
