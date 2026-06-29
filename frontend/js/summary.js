(async () => {
  const session = await requireAuth();
  if (!session) return;
  setNavActive();
  showUserEmail();

  try {
    const members = await api.getMembers() || [];
    const sel = document.getElementById("f-member");
    sel.innerHTML = `<option value="">Select member</option>` +
      members.map(m => `<option value="${m.id}">${m.name}</option>`).join("");
    const param = new URLSearchParams(window.location.search).get("member");
    if (param) { sel.value = param; loadSummary(); }
  } catch (err) {
    showError(err.message);
  }

  window.loadSummary = async () => {
    const memberId = document.getElementById("f-member").value;
    if (!memberId) return;

    document.getElementById("summary-content").style.display = "none";
    document.getElementById("empty-state").style.display = "block";
    try {
      const s = await api.getSummary(memberId);
      renderSummary(s);
    } catch (err) {
      showError(err.message);
    }
  };

  function renderSummary(s) {
    document.getElementById("empty-state").style.display = "none";
    document.getElementById("summary-content").style.display = "block";
    document.getElementById("ph-generated").textContent = `Generated: ${new Date(s.generated_at).toLocaleString("en-IN")}`;

    // Member
    const m = s.member;
    document.getElementById("s-member").innerHTML = `
      <div class="form-row">
        <div><span class="form-label">Name</span><p style="font-size:16px;font-weight:600">${m.name}</p></div>
        <div><span class="form-label">Date of Birth</span><p>${formatDate(m.dob)}</p></div>
      </div>
      <div class="form-row" style="margin-top:8px">
        <div><span class="form-label">Blood Type</span><p>${m.blood_type || "—"}</p></div>
        <div><span class="form-label">Relationship</span><p>${m.relationship || "—"}</p></div>
      </div>
    `;

    // Allergies
    const allergyEl = document.getElementById("s-allergies");
    allergyEl.innerHTML = s.allergies.length
      ? s.allergies.map(a => `<span class="tag allergy">${a}</span>`).join(" ")
      : `<span style="color:var(--text-muted)">None recorded</span>`;

    // Conditions
    const condEl = document.getElementById("s-conditions");
    condEl.innerHTML = s.conditions.length
      ? s.conditions.map(c => `<span class="tag">${c}</span>`).join(" ")
      : `<span style="color:var(--text-muted)">None recorded</span>`;

    // Medicines
    const medTbody = document.getElementById("s-medicines");
    medTbody.innerHTML = s.active_medicines.length
      ? s.active_medicines.map(med => `
          <tr>
            <td style="font-weight:500">${med.brand_name || "—"}</td>
            <td>${med.generic_name || "—"}</td>
            <td>${med.dosage || "—"}</td>
            <td>${med.frequency || "—"}</td>
            <td>${formatDate(med.prescribed_date)}</td>
          </tr>
        `).join("")
      : `<tr><td colspan="5" style="color:var(--text-muted);padding:16px">None recorded</td></tr>`;

    // Abnormal labs
    const labTbody = document.getElementById("s-labs");
    labTbody.innerHTML = s.recent_lab_abnormals.length
      ? s.recent_lab_abnormals.map(l => `
          <tr>
            <td style="font-weight:500">${l.test_name}</td>
            <td class="lab-value-abnormal">${l.value}</td>
            <td>${l.unit || "—"}</td>
            <td>${l.reference_low != null && l.reference_high != null ? l.reference_low + " – " + l.reference_high : "—"}</td>
            <td>${formatDate(l.report_date)}</td>
          </tr>
        `).join("")
      : `<tr><td colspan="5" style="color:var(--success);padding:16px">All values normal in last 90 days</td></tr>`;

    // All recent labs
    const allLabsTbody = document.getElementById("s-labs-all");
    allLabsTbody.innerHTML = s.recent_labs_all && s.recent_labs_all.length
      ? s.recent_labs_all.map(l => `
          <tr>
            <td style="font-weight:500">${l.test_name}</td>
            <td class="${l.is_abnormal ? 'lab-value-abnormal' : ''}">${l.value}</td>
            <td>${l.unit || "—"}</td>
            <td>${l.reference_low != null && l.reference_high != null ? l.reference_low + " – " + l.reference_high : "—"}</td>
            <td>${formatDate(l.report_date)}</td>
            <td>${l.is_abnormal ? '<span class="badge badge-danger">Abnormal</span>' : '<span style="color:var(--success);font-size:12px">Normal</span>'}</td>
          </tr>
        `).join("")
      : `<tr><td colspan="6" style="color:var(--text-muted);padding:16px">No lab results in last 90 days</td></tr>`;

    // Health history events
    const eventsEl = document.getElementById("s-events");
    eventsEl.innerHTML = s.recent_events && s.recent_events.length
      ? s.recent_events.map(e => `
          <div style="display:flex;gap:16px;padding:10px 20px;border-bottom:1px solid var(--border);align-items:flex-start">
            <div style="min-width:90px;font-size:12px;color:var(--text-muted);padding-top:2px">${formatDate(e.event_date)}</div>
            <div>
              <div style="font-weight:500">${e.title}</div>
              <div style="font-size:12px;color:var(--text-muted)">${e.event_type || ""}${e.doctor_name ? " · " + e.doctor_name : ""}${e.facility_name ? " · " + e.facility_name : ""}</div>
            </div>
          </div>
        `).join("")
      : `<div style="padding:16px;color:var(--text-muted)">No health events recorded</div>`;

    // Active alerts
    const alertEl = document.getElementById("s-alerts");
    alertEl.innerHTML = s.active_alerts.length
      ? s.active_alerts.map(a => `
          <div style="padding:10px 20px;border-bottom:1px solid var(--border)">
            <strong>${a.title}</strong>
            <p style="font-size:12px;color:var(--text-muted);margin-top:2px">${a.description || ""}</p>
          </div>
        `).join("")
      : `<div style="padding:16px;color:var(--text-muted)">No active alerts</div>`;
  }
})();
