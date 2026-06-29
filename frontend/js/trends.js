(async () => {
  const session = await requireAuth();
  if (!session) return;
  setNavActive();
  showUserEmail();

  let chartInstance = null;
  const LAB_TESTS = [
    "HbA1c","Fasting Blood Glucose","Post-Prandial Blood Glucose","Random Blood Glucose",
    "Hemoglobin","WBC","RBC","Platelets","Hematocrit","MCV","MCH","MCHC","RDW",
    "Neutrophils","Lymphocytes","Eosinophils","Total Cholesterol","HDL Cholesterol",
    "LDL Cholesterol","VLDL Cholesterol","Triglycerides","TSH","T3 Total","T4 Total",
    "Free T3","Free T4","Creatinine","Urea","Uric Acid","eGFR","ALT","AST",
    "Alkaline Phosphatase","Total Bilirubin","Direct Bilirubin","Total Protein","Albumin","GGT",
    "Sodium","Potassium","Chloride","Calcium","Vitamin D","Vitamin B12","Iron","Ferritin",
    "TIBC","PSA","CRP","ESR"
  ];

  // Load members
  try {
    const members = await api.getMembers() || [];
    const sel = document.getElementById("f-member");
    sel.innerHTML = `<option value="">Select member</option>` +
      members.map(m => `<option value="${m.id}">${m.name}</option>`).join("");

    const paramMember = new URLSearchParams(window.location.search).get("member");
    if (paramMember) { sel.value = paramMember; onMemberChange(); }
  } catch (err) {
    showError(err.message);
  }

  // Populate test selector
  const testSel = document.getElementById("f-test");
  testSel.innerHTML = `<option value="">Select test</option>` +
    LAB_TESTS.map(t => `<option value="${t}">${t}</option>`).join("");

  const paramTest = new URLSearchParams(window.location.search).get("test");
  if (paramTest) { testSel.value = paramTest; }

  window.onMemberChange = () => {
    if (document.getElementById("f-member").value) loadTrend();
  };

  window.loadTrend = async () => {
    const memberId = document.getElementById("f-member").value;
    const testName = document.getElementById("f-test").value;
    if (!memberId || !testName) return;

    const params = {};
    const from = document.getElementById("f-from").value;
    const to = document.getElementById("f-to").value;
    if (from) params.date_from = from;
    if (to) params.date_to = to;

    try {
      const points = await api.getTrend(memberId, testName, params) || [];
      renderChart(testName, points);
    } catch (err) {
      showError(err.message);
    }
  };

  function renderChart(testName, points) {
    document.getElementById("empty-state").style.display = "none";
    document.getElementById("chart-card").style.display = "block";
    document.getElementById("chart-title").textContent = testName;

    const unit = points[0]?.unit || "";
    document.getElementById("chart-unit").textContent = unit;

    const labels = points.map(p => p.date);
    const values = points.map(p => p.value);
    const refLow = points[0]?.reference_low;
    const refHigh = points[0]?.reference_high;

    const pointColors = points.map(p =>
      p.is_abnormal ? "#E63946" : "#00A878"
    );

    if (chartInstance) chartInstance.destroy();
    const ctx = document.getElementById("trend-chart").getContext("2d");
    chartInstance = new Chart(ctx, {
      type: "line",
      data: {
        labels,
        datasets: [
          {
            label: testName,
            data: values,
            borderColor: "#0066CC",
            backgroundColor: "rgba(0,102,204,0.08)",
            pointBackgroundColor: pointColors,
            pointRadius: 6,
            pointHoverRadius: 8,
            tension: 0.3,
            fill: true,
          },
          refHigh != null && {
            label: "Upper limit",
            data: Array(labels.length).fill(refHigh),
            borderColor: "#E6394660",
            borderDash: [6, 4],
            borderWidth: 1.5,
            pointRadius: 0,
            fill: false,
          },
          refLow != null && {
            label: "Lower limit",
            data: Array(labels.length).fill(refLow),
            borderColor: "#00A87860",
            borderDash: [6, 4],
            borderWidth: 1.5,
            pointRadius: 0,
            fill: false,
          },
        ].filter(Boolean),
      },
      options: {
        responsive: true,
        plugins: {
          legend: { position: "top" },
          tooltip: {
            callbacks: {
              label: (ctx) => `${ctx.dataset.label}: ${ctx.parsed.y} ${unit}`,
            },
          },
        },
        scales: {
          y: { title: { display: true, text: unit } },
          x: { title: { display: true, text: "Date" } },
        },
      },
    });

    // Table
    const tbody = document.getElementById("trend-table-body");
    tbody.innerHTML = [...points].reverse().map(p => `
      <tr>
        <td>${formatDate(p.date)}</td>
        <td class="${p.is_abnormal ? 'lab-value-abnormal' : 'lab-value-normal'}">${p.value}</td>
        <td>${p.unit || "—"}</td>
        <td>${p.reference_low != null && p.reference_high != null ? p.reference_low + " – " + p.reference_high : "—"}</td>
        <td>${p.is_abnormal === true ? '<span class="badge badge-danger">Abnormal</span>' : p.is_abnormal === false ? '<span class="badge badge-success">Normal</span>' : "—"}</td>
      </tr>
    `).join("");
  }
})();
