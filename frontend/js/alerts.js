(async () => {
  const session = await requireAuth();
  if (!session) return;
  setNavActive();
  showUserEmail();

  const ALERT_ICONS = { abnormal_value: "⚠️", trend_warning: "📈", medicine_renewal: "💊", followup: "📅", overdue_test: "🔬" };

  try {
    const members = await api.getMembers() || [];
    const sel = document.getElementById("f-member");
    sel.innerHTML = `<option value="">All Members</option>` +
      members.map(m => `<option value="${m.id}">${m.name}</option>`).join("");
  } catch (err) {
    showError(err.message);
  }

  window.loadAlerts = async () => {
    const params = {};
    const member = document.getElementById("f-member").value;
    const showDismissed = document.getElementById("f-dismissed").checked;
    if (member) params.member_id = member;
    if (showDismissed) params.include_dismissed = true;

    const list = document.getElementById("alerts-list");
    list.innerHTML = `<div style="padding:20px;color:var(--text-muted)">Loading...</div>`;
    try {
      const alerts = await api.getAlerts(params) || [];
      renderAlerts(alerts);
    } catch (err) {
      showError(err.message);
    }
  };

  function renderAlerts(alerts) {
    const list = document.getElementById("alerts-list");
    if (!alerts.length) {
      list.innerHTML = `<div class="empty-state" style="padding:40px"><div class="empty-icon">✅</div><h3>No active alerts</h3><p>Alerts are generated when lab values exceed reference thresholds or prescriptions need renewal.</p></div>`;
      return;
    }
    list.innerHTML = alerts.map(a => `
      <div class="alert-item" id="alert-${a.id}" style="${a.is_dismissed ? 'opacity:0.5' : ''}">
        <div class="alert-dot ${a.alert_type === 'abnormal_value' ? 'danger' : 'warning'}"></div>
        <div style="flex:1">
          <h4>${ALERT_ICONS[a.alert_type] || "🔔"} ${a.title}</h4>
          <p>${a.description || ""}</p>
          ${a.due_date ? `<p style="margin-top:2px;font-size:11px;color:var(--text-muted)">Due: ${formatDate(a.due_date)}</p>` : ""}
          ${a.source_doc_id ? `<a href="document.html?id=${a.source_doc_id}" style="font-size:11px">View source document →</a>` : ""}
        </div>
        ${!a.is_dismissed ? `<button class="btn btn-sm btn-secondary" onclick="dismiss('${a.id}')">Dismiss</button>` : `<span class="badge badge-muted">Dismissed</span>`}
      </div>
    `).join("");
  }

  window.dismiss = async (id) => {
    try {
      await api.dismissAlert(id);
      const el = document.getElementById(`alert-${id}`);
      if (el) el.style.opacity = "0.4";
      showToast("Alert dismissed");
    } catch (err) {
      showError(err.message);
    }
  };

  loadAlerts();
})();
