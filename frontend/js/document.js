(async () => {
  const session = await requireAuth();
  if (!session) return;
  setNavActive();
  showUserEmail();

  const docId = new URLSearchParams(window.location.search).get("id");
  if (!docId) { showError("No document ID provided"); return; }

  async function loadDoc() {
    try {
      const doc = await api.getDocument(docId);
      if (!doc) return;

      document.title = doc.title + " — Family Health Record";
      document.getElementById("doc-title").textContent = doc.title;

      const viewBtn = document.getElementById("view-file-btn");
      viewBtn.href = doc.file_url;

      // Meta info
      const meta = document.getElementById("doc-meta");
      meta.innerHTML = `
        <div class="form-row">
          <div><span class="form-label">Type</span><p>${doc.document_type || "—"}</p></div>
          <div><span class="form-label">Date</span><p>${formatDate(doc.report_date)}</p></div>
        </div>
        <div class="form-row" style="margin-top:8px">
          <div><span class="form-label">Facility</span><p>${doc.facility_name || "—"}</p></div>
          <div><span class="form-label">Doctor</span><p>${doc.doctor_name || "—"}</p></div>
        </div>
        ${doc.notes ? `<div style="margin-top:8px"><span class="form-label">Notes</span><p>${doc.notes}</p></div>` : ""}
      `;

      // File preview
      const preview = document.getElementById("file-preview-area");
      if (doc.file_type === "pdf") {
        preview.innerHTML = `<iframe src="${doc.file_url}" style="width:100%;height:400px;border:none;border-radius:4px"></iframe>`;
      } else if (doc.file_url) {
        preview.innerHTML = `<img src="${doc.file_url}" style="max-width:100%;border-radius:4px">`;
      } else {
        preview.innerHTML = `<div style="color:var(--text-muted);text-align:center;padding:40px">No preview available</div>`;
      }

      // OCR status
      const statusMap = { pending: ["muted", "Queued"], processing: ["info", "Extracting..."], done: ["success", "Extraction complete"], failed: ["danger", "Extraction failed"], done_no_ai: ["warning", "Lab values extracted (AI skipped)"] };
      const [cls, label] = statusMap[doc.ocr_status] || ["muted", doc.ocr_status];
      document.getElementById("ocr-status-badge").innerHTML = `<span class="badge badge-${cls}" style="font-size:13px;padding:4px 12px">${label}</span>`;

      // Lab values
      renderLabValues(doc.lab_values || []);

      // Medicines
      renderMedicines(doc.medicines || []);

      // Events
      renderEvents(doc.events || []);
    } catch (err) {
      showError(err.message);
    }
  }

  function renderLabValues(labs) {
    const tbody = document.getElementById("lab-body");
    document.getElementById("lab-count").textContent = labs.length;
    if (!labs.length) {
      tbody.innerHTML = `<tr><td colspan="6" style="text-align:center;padding:20px;color:var(--text-muted)">No lab values extracted</td></tr>`;
      return;
    }
    tbody.innerHTML = labs.map(l => `
      <tr>
        <td style="font-weight:500">${l.test_name}</td>
        <td class="${l.is_abnormal ? 'lab-value-abnormal' : 'lab-value-normal'}">${l.value ?? "—"}</td>
        <td>${l.unit || "—"}</td>
        <td>${l.reference_low != null && l.reference_high != null ? l.reference_low + " – " + l.reference_high : "—"}</td>
        <td>${l.is_abnormal === true ? '<span class="badge badge-danger">Abnormal</span>' : l.is_abnormal === false ? '<span class="badge badge-success">Normal</span>' : "—"}</td>
        <td><button class="btn btn-sm btn-danger" onclick="deleteLabValue('${l.id}',this)">✕</button></td>
      </tr>
    `).join("");
  }

  function renderMedicines(meds) {
    const tbody = document.getElementById("med-body");
    document.getElementById("med-count").textContent = meds.length;
    if (!meds.length) return;
    tbody.innerHTML = meds.map(m => `
      <tr>
        <td>${m.brand_name || "—"}</td>
        <td>${m.generic_name || "—"}</td>
        <td>${m.dosage || "—"}</td>
        <td>${m.frequency || "—"}</td>
        <td>${m.is_active ? '<span class="badge badge-success">Active</span>' : '<span class="badge badge-muted">Stopped</span>'}</td>
      </tr>
    `).join("");
  }

  function renderEvents(events) {
    const el = document.getElementById("events-list");
    document.getElementById("evt-count").textContent = events.length;
    if (!events.length) return;
    el.innerHTML = events.map(e => `
      <div style="padding:10px 20px;border-bottom:1px solid var(--border)">
        <span class="badge badge-info" style="margin-right:6px">${e.event_type}</span>
        <span style="font-weight:500">${e.title}</span>
        ${e.event_date ? `<span style="color:var(--text-muted);font-size:12px;margin-left:8px">${formatDate(e.event_date)}</span>` : ""}
        ${e.doctor_name ? `<span style="color:var(--text-muted);font-size:12px"> · ${e.doctor_name}</span>` : ""}
      </div>
    `).join("");
  }

  window.deleteLabValue = async (id, btn) => {
    btn.disabled = true;
    try {
      await api.deleteLabValue(id);
      btn.closest("tr").remove();
      showToast("Lab value removed");
    } catch (err) {
      showError(err.message);
      btn.disabled = false;
    }
  };

  window.reprocess = async () => {
    if (!confirm("Re-run extraction? This will replace all extracted lab values and medicines.")) return;
    try {
      await api.reprocessDocument(docId);
      showToast("Reprocessing started — refresh in a moment");
    } catch (err) {
      showError(err.message);
    }
  };

  window.deleteDoc = async () => {
    if (!confirm("Delete this document and all extracted data permanently?")) return;
    try {
      await api.deleteDocument(docId);
      window.location.href = "documents.html";
    } catch (err) {
      showError(err.message);
    }
  };

  loadDoc();
})();
