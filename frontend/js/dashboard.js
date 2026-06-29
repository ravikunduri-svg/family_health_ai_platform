(async () => {
  const session = await requireAuth();
  if (!session) return;
  setNavActive();
  showUserEmail();

  let memberMap = {};

  async function loadDashboard() {
    try {
      const [members, alerts, docs, meds] = await Promise.all([
        api.getMembers(),
        api.getAlerts(),
        api.getDocuments({ limit: 10 }),
        api.getMedicines({ is_active: true }),
      ]);

      memberMap = Object.fromEntries((members || []).map(m => [m.id, m.name]));

      document.getElementById("stat-members").textContent = (members || []).length;
      document.getElementById("stat-alerts").textContent = (alerts || []).length;
      document.getElementById("stat-docs").textContent = (docs || []).length;
      document.getElementById("stat-meds").textContent = (meds || []).length;

      renderMemberCards(members || []);
      renderAlerts(alerts || []);
      renderDocs(docs || []);
    } catch (err) {
      showError(err.message);
    }
  }

  function renderMemberCards(members) {
    const el = document.getElementById("member-cards");
    if (!members.length) return;
    el.innerHTML = members.map(m => `
      <div class="member-card" onclick="window.location='timeline.html?member=${m.id}'" style="margin-bottom:12px">
        <div style="display:flex;align-items:center;gap:12px">
          <div class="member-avatar">${m.name[0].toUpperCase()}</div>
          <div>
            <div class="member-name">${m.name}</div>
            <div class="member-meta">${m.relationship || ""} ${m.blood_type ? "· " + m.blood_type : ""}</div>
          </div>
        </div>
      </div>
    `).join("");
  }

  function renderAlerts(alerts) {
    const el = document.getElementById("alerts-list");
    if (!alerts.length) return;
    el.innerHTML = alerts.slice(0, 5).map(a => `
      <div class="alert-item">
        <div class="alert-dot ${a.alert_type === 'abnormal_value' ? 'danger' : 'warning'}"></div>
        <div>
          <h4>${a.title}</h4>
          <p>${a.description || ""}</p>
        </div>
        <button class="btn btn-sm btn-secondary" style="margin-left:auto;flex-shrink:0" onclick="dismissAlert('${a.id}',this)">Dismiss</button>
      </div>
    `).join("");
  }

  function renderDocs(docs) {
    const tbody = document.getElementById("docs-body");
    if (!docs.length) {
      tbody.innerHTML = `<tr><td colspan="5" style="text-align:center;color:var(--text-muted);padding:30px">No documents yet. <a href="upload.html">Upload one.</a></td></tr>`;
      return;
    }
    const statusBadge = (s) => {
      const map = { pending: "muted", processing: "info", done: "success", failed: "danger", done_no_ai: "warning" };
      return `<span class="badge badge-${map[s] || 'muted'}">${s}</span>`;
    };
    tbody.innerHTML = docs.map(d => `
      <tr>
        <td><a href="document.html?id=${d.id}">${d.title}</a></td>
        <td>${memberMap[d.member_id] || "—"}</td>
        <td>${d.document_type || "—"}</td>
        <td>${formatDate(d.report_date)}</td>
        <td>${statusBadge(d.ocr_status)}</td>
      </tr>
    `).join("");
  }

  window.dismissAlert = async (id, btn) => {
    btn.disabled = true;
    try {
      await api.dismissAlert(id);
      btn.closest(".alert-item").remove();
    } catch (err) {
      showError(err.message);
      btn.disabled = false;
    }
  };

  loadDashboard();
})();
