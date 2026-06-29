(async () => {
  const session = await requireAuth();
  if (!session) return;
  setNavActive();
  showUserEmail();

  let selectedFile = null;

  // Load family members
  try {
    const members = await api.getMembers() || [];
    const sel = document.getElementById("f-member");
    sel.innerHTML = `<option value="">Select member</option>` +
      members.map(m => `<option value="${m.id}">${m.name}</option>`).join("");

    // Pre-select from query param
    const paramMember = new URLSearchParams(window.location.search).get("member");
    if (paramMember) sel.value = paramMember;
  } catch (err) {
    showError(err.message);
  }

  // Drop zone
  const zone = document.getElementById("drop-zone");
  const fileInput = document.getElementById("file-input");

  zone.addEventListener("dragover", (e) => { e.preventDefault(); zone.classList.add("dragover"); });
  zone.addEventListener("dragleave", () => zone.classList.remove("dragover"));
  zone.addEventListener("drop", (e) => {
    e.preventDefault();
    zone.classList.remove("dragover");
    const f = e.dataTransfer.files[0];
    if (f) setFile(f);
  });
  fileInput.addEventListener("change", () => {
    if (fileInput.files[0]) setFile(fileInput.files[0]);
  });

  function setFile(file) {
    selectedFile = file;
    document.getElementById("file-name").textContent = `${file.name} (${(file.size / 1024).toFixed(0)} KB)`;
    document.getElementById("file-preview").style.display = "block";
    // Auto-fill title if empty
    if (!document.getElementById("f-title").value) {
      document.getElementById("f-title").value = file.name.replace(/\.[^.]+$/, "");
    }
  }

  window.clearFile = () => {
    selectedFile = null;
    fileInput.value = "";
    document.getElementById("file-preview").style.display = "none";
  };

  window.clearForm = () => {
    clearFile();
    ["f-member","f-type","f-title","f-date","f-facility","f-doctor","f-notes"].forEach(id => {
      const el = document.getElementById(id);
      if (el) el.value = "";
    });
    hideError();
  };

  window.submitUpload = async () => {
    hideError();
    if (!selectedFile) { showError("Choose a file to upload"); return; }
    const memberId = document.getElementById("f-member").value;
    const docType = document.getElementById("f-type").value;
    const title = document.getElementById("f-title").value.trim();
    if (!memberId) { showError("Select a family member"); return; }
    if (!docType) { showError("Select a document type"); return; }
    if (!title) { showError("Enter a document title"); return; }

    const btn = document.getElementById("upload-btn");
    btn.disabled = true;
    const progressWrap = document.getElementById("progress-wrap");
    const progressFill = document.getElementById("progress-fill");
    const progressLabel = document.getElementById("progress-label");
    progressWrap.style.display = "block";
    progressLabel.textContent = "Uploading...";
    progressFill.style.width = "30%";

    const formData = new FormData();
    formData.append("file", selectedFile);
    formData.append("member_id", memberId);
    formData.append("document_type", docType);
    formData.append("title", title);
    const date = document.getElementById("f-date").value;
    const facility = document.getElementById("f-facility").value.trim();
    const doctor = document.getElementById("f-doctor").value.trim();
    const notes = document.getElementById("f-notes").value.trim();
    if (date) formData.append("report_date", date);
    if (facility) formData.append("facility_name", facility);
    if (doctor) formData.append("doctor_name", doctor);
    if (notes) formData.append("notes", notes);

    try {
      progressFill.style.width = "60%";
      progressLabel.textContent = "Processing...";
      const result = await api.uploadDocument(formData);
      progressFill.style.width = "100%";
      progressLabel.textContent = "Done!";

      const successBanner = document.getElementById("success-banner");
      successBanner.innerHTML = `File uploaded. Extraction running in background. <a href="document.html?id=${result.id}">View document →</a>`;
      successBanner.style.display = "flex";
      clearForm();
    } catch (err) {
      showError(err.message || "Upload failed");
    } finally {
      btn.disabled = false;
      setTimeout(() => { progressWrap.style.display = "none"; progressFill.style.width = "0"; }, 2000);
    }
  };
})();
