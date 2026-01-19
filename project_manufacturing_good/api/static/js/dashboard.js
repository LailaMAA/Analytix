document.addEventListener('DOMContentLoaded', async function () {

    // --- AUTH CHECK ---
    const token = localStorage.getItem('access_token');
    if (!token && !window.location.pathname.includes('/login')) {
        window.location.href = '/login';
        return;
    }

    // Helper for fetch with Auth
    async function fetchAuth(url, options = {}) {
        const headers = options.headers || {};
        headers['Authorization'] = `Bearer ${token}`;

        const res = await fetch(url, { ...options, headers });
        if (res.status === 401) {
            localStorage.removeItem('access_token');
            window.location.href = '/login';
        }
        return res;
    }

    // 0. System Defaults
    Chart.defaults.color = '#94a3b8';
    Chart.defaults.font.family = "'Outfit', sans-serif";

    // Toast Container
    const toastContainer = document.createElement('div');
    toastContainer.className = 'toast-container';
    document.body.appendChild(toastContainer);

    function showToast(message, level = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast toast-${level.toLowerCase()}`;

        let icon = 'information-circle-outline';
        if (level === 'Critical') icon = 'alert-circle-outline';
        if (level === 'Success') icon = 'checkmark-circle-outline';

        toast.innerHTML = `
            <ion-icon name="${icon}" style="font-size: 1.4rem; color: ${level === 'Critical' ? '#ef4444' : (level === 'Success' ? '#10b981' : '#3b82f6')};"></ion-icon>
            <div style="flex: 1;">
                <div style="font-weight: 700; font-size: 0.85rem; margin-bottom: 2px;">${level === 'Critical' ? 'Alerte IA' : 'Notification'}</div>
                <div style="font-size: 0.75rem; color: #cbd5e1; line-height: 1.3;">${message}</div>
            </div>
        `;

        toastContainer.appendChild(toast);
        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(100%)';
            setTimeout(() => toast.remove(), 300);
        }, 5000);
    }

    // 1. Initialisation des KPIs
    function loadProKPIs() {
        // Core KPIs
        fetchAuth('/api/kpi/stats')
            .then(res => res.json())
            .then(data => {
                const critEl = document.getElementById('kpi-critical-value');
                if (critEl) critEl.textContent = data.critical_fleet || '0';

                const stockEl = document.getElementById('kpi-stock-value');
                if (stockEl) stockEl.textContent = data.parts_availability + '%';
            });

        // Financial KPIs
        fetchAuth('/api/kpi/financial')
            .then(res => res.json())
            .then(data => {
                // Fetch HR and Stock for integrated calculation
                Promise.all([
                    fetchAuth('/api/kpi/resources').then(r => r.json()),
                    fetchAuth('/api/kpi/inventory').then(r => r.json())
                ]).then(([hrData, invData]) => {
                    const roiEl = document.getElementById('kpi-roi-value');
                    if (roiEl) {
                        const integratedROI = calculateIntegratedROI(data.avg_roi, hrData.availability_rate, invData.supply_chain_health);
                        roiEl.textContent = integratedROI + '%';
                    }
                });

                // Trigger financial chart with real data
                renderFinancialIntelligence(data);
            });

        // HR KPIs
        fetchAuth('/api/kpi/resources')
            .then(res => res.json())
            .then(data => {
                const hrEl = document.getElementById('kpi-hr-value');
                if (hrEl) hrEl.textContent = data.availability_rate + '%';
            });
    }

    // 2. Advanced Financial Chart (ApexCharts)
    let financialChartInstance = null;
    let cachedFinancialData = null; // Store data for re-rendering

    function renderFinancialIntelligence(finData) {
        if (!finData.chart) return;
        cachedFinancialData = finData; // Cache it

        // Get current accent color
        const accentColor = getComputedStyle(document.documentElement).getPropertyValue('--electric-blue').trim();

        const options = {
            series: [{
                name: 'ROI Prédit (%)',
                data: finData.chart.roi_series
            }, {
                name: 'Coût Investissement (kDH)',
                data: finData.chart.cost_series.map(v => v / 1000)
            }],
            chart: {
                height: 350,
                type: 'area',
                background: 'transparent',
                toolbar: { show: false }
            },
            colors: [accentColor, '#fbbf24'], // Use dynamic color
            dataLabels: { enabled: false },
            stroke: { curve: 'smooth', width: 3 },
            fill: {
                type: 'gradient',
                gradient: {
                    shadeIntensity: 1,
                    opacityFrom: 0.4,
                    opacityTo: 0.05,
                    stops: [0, 90, 100]
                }
            },
            xaxis: {
                categories: finData.chart.labels,
                axisBorder: { show: false },
                axisTicks: { show: false },
                labels: { style: { colors: '#64748b' } }
            },
            yaxis: { show: false },
            grid: { borderColor: 'rgba(255,255,255,0.05)', strokeDashArray: 4 },
            legend: {
                position: 'top',
                horizontalAlign: 'right',
                labels: { colors: '#f8fafc' }
            },
            tooltip: { theme: 'dark' }
        };

        if (financialChartInstance) {
            financialChartInstance.updateOptions(options);
        } else {
            financialChartInstance = new ApexCharts(document.querySelector("#financialChart"), options);
            financialChartInstance.render();
        }
    }

    // 3. Regional Risk Chart (Chart.js)
    let regionChartInstance = null; // Store instance

    function loadRegionChart() {
        const ctxRegion = document.getElementById('regionChart').getContext('2d');
        fetchAuth('/api/kpi/costs-by-region')
            .then(res => res.json())
            .then(data => {
                const accentColor = getComputedStyle(document.documentElement).getPropertyValue('--electric-blue').trim();

                // Destroy existing if re-creating (though we prefer updating content)
                if (regionChartInstance) regionChartInstance.destroy();

                regionChartInstance = new Chart(ctxRegion, {
                    type: 'bar',
                    data: {
                        labels: data.labels,
                        datasets: [{
                            label: 'Risque Budgétaire (kDH)',
                            data: data.data,
                            backgroundColor: accentColor, // Use dynamic color (solid)
                            borderColor: accentColor,
                            borderWidth: 1,
                            borderRadius: 12,
                            barThickness: 20
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: { legend: { display: false } },
                        scales: {
                            y: { grid: { color: 'rgba(255,255,255,0.05)' }, border: { display: false } },
                            x: { grid: { display: false }, border: { display: false } }
                        }
                    }
                });
            });
    }

    // Helper to update all charts
    function updateAllChartsColors() {
        const newColor = getComputedStyle(document.documentElement).getPropertyValue('--electric-blue').trim();

        // Update ApexChart
        if (financialChartInstance && cachedFinancialData) {
            financialChartInstance.updateOptions({
                colors: [newColor, '#fbbf24']
            });
        }

        // Update Chart.js (Region Risk)
        if (regionChartInstance) {
            regionChartInstance.data.datasets[0].backgroundColor = newColor;
            regionChartInstance.data.datasets[0].borderColor = newColor;

            // Update axis colors for visibility
            const isLight = document.documentElement.getAttribute('data-theme') === 'light';
            const tickColor = isLight ? '#64748b' : '#94a3b8';
            const gridColor = isLight ? 'rgba(0,0,0,0.05)' : 'rgba(255,255,255,0.05)';

            regionChartInstance.options.scales.x.ticks.color = tickColor;
            regionChartInstance.options.scales.y.ticks.color = tickColor;
            regionChartInstance.options.scales.y.grid.color = gridColor;

            regionChartInstance.update();
        }

        // Update Chart.js (HR Region)
        if (hrChartInstance) {
            hrChartInstance.data.datasets[0].backgroundColor = newColor;
            hrChartInstance.update();
        }
    }

    // --- Accent Color Logic ---
    const colorOptions = document.querySelectorAll('.color-option');
    colorOptions.forEach(opt => {
        opt.addEventListener('click', () => {
            colorOptions.forEach(o => {
                o.classList.remove('active');
                o.style.border = '2px solid transparent';
            });
            opt.classList.add('active');
            opt.style.border = '2px solid white'; // Visual feedback

            // Read color from inline style or data attrib
            const newColor = opt.getAttribute('data-color') || window.getComputedStyle(opt).backgroundColor;
            document.documentElement.style.setProperty('--electric-blue', newColor);
            localStorage.setItem('accent_color', newColor);

            // Trigger chart update
            updateAllChartsColors();
        });
    });

    // --- Theme Toggle Logic ---
    const toggleCtx = document.getElementById('toggle-darkmode');

    // 1. Check Saved Theme
    const currentTheme = localStorage.getItem('theme') || 'dark'; // Default dark
    if (currentTheme === 'light') {
        document.documentElement.setAttribute('data-theme', 'light');
        if (toggleCtx) toggleCtx.checked = false; // "Unchecked" = Light Mode
    } else {
        document.documentElement.removeAttribute('data-theme');
        if (toggleCtx) toggleCtx.checked = true; // "Checked" = Dark Mode
    }

    // 2. Event Listener
    if (toggleCtx) {
        toggleCtx.addEventListener('change', function () {
            if (this.checked) {
                // Swith to Dark
                document.documentElement.removeAttribute('data-theme');
                localStorage.setItem('theme', 'dark');
            } else {
                // Switch to Light
                document.documentElement.setAttribute('data-theme', 'light');
                localStorage.setItem('theme', 'light');
            }
        });
    }

    // --- Column Visibility Logic ---
    const btnToggleCols = document.getElementById('btn-toggle-cols');
    const colDropdown = document.getElementById('col-dropdown-content');

    if (btnToggleCols && colDropdown) {
        btnToggleCols.addEventListener('click', (e) => {
            e.stopPropagation();
            colDropdown.classList.toggle('hidden');
        });

        document.addEventListener('click', (e) => {
            if (!colDropdown.contains(e.target) && e.target !== btnToggleCols) {
                colDropdown.classList.add('hidden');
            }
        });

        const colCheckboxes = colDropdown.querySelectorAll('input[type="checkbox"]');
        colCheckboxes.forEach(cb => {
            cb.addEventListener('change', () => {
                const colIdx = parseInt(cb.getAttribute('data-col'));
                const table = document.getElementById('allPredictionsTable');
                if (!table) return;

                // Toggle header
                const th = table.querySelectorAll('thead th')[colIdx - 1];
                if (th) th.style.display = cb.checked ? '' : 'none';

                // Toggle body cells
                const rows = table.querySelectorAll('tbody tr');
                rows.forEach(tr => {
                    const td = tr.querySelectorAll('td')[colIdx - 1];
                    if (td) td.style.display = cb.checked ? '' : 'none';
                });
            });
        });
    }

    // --- Main Filter Logic (Search) ---
    const searchInput = document.getElementById('prediction-main-filter');
    if (searchInput) {
        searchInput.addEventListener('keyup', applySearchFilter);
    }

    // --- Integrated ROI Logic ---
    function calculateIntegratedROI(baseROI, hrAvailability, stockHealth) {
        // Simple logic: HR efficiency and Stock availability boost or penalize ROI
        // Factor 1: HR. If availability < 70%, penalize ROI by 10%
        let factorHR = 1.0;
        if (hrAvailability < 70) factorHR = 0.9;
        else if (hrAvailability > 90) factorHR = 1.05;

        // Factor 2: Stock. If stock health < 80%, penalize ROI by 5%
        let factorStock = 1.0;
        if (stockHealth < 80) factorStock = 0.95;

        return (baseROI * factorHR * factorStock).toFixed(1);
    }

    // 4. Live Predictions Table
    function loadRecentPredictions() {
        fetchAuth('/predictions?limit=6')
            .then(res => res.json())
            .then(data => {
                const tbody = document.querySelector('#predictionsTable tbody');
                if (!tbody) return;
                tbody.innerHTML = '';

                data.forEach(pred => {
                    const tr = document.createElement('tr');

                    let badgeClass = 'badge-success';
                    let statusText = 'Sous Surveillance';

                    const fType = (pred.failure_type || '').toLowerCase();
                    const days = pred.days_before_failure || 0;
                    const prob = pred.failure_probability || 0;

                    // Logic Refinement
                    if (fType.includes('aucune') || fType === 'nan' || fType === '') {
                        badgeClass = 'badge-success';
                        statusText = 'Normal';
                    } else {
                        // If probability is high AND imminent (less than 2 weeks)
                        if (prob > 0.75 && days < 14) {
                            badgeClass = 'badge-danger';
                            statusText = 'Action Immédiate';
                        }
                        // If probability is significant AND somewhat soon (less than 2 months)
                        else if (prob > 0.5 && days < 60) {
                            badgeClass = 'badge-warning';
                            statusText = 'Planifier';
                        }
                        // Otherwise (High days or low probability) -> Sous Surveillance (Default)
                    }

                    tr.innerHTML = `
                        <td style="color: var(--electric-blue); font-weight: 600;">${pred.vehicle_id}</td>
                        <td style="color: white;">${pred.failure_type || 'Aucune'}</td>
                        <td><span style="font-weight: 700;">${days} j</span></td>
                        <td>${(prob * 100).toFixed(1)}%</td>
                        <td><span class="badge-pro ${badgeClass}">${statusText}</span></td>
                    `;
                    tbody.appendChild(tr);
                });
            });
    }

    // 5. Navigation Logic
    const navLinks = document.querySelectorAll('.nav-link');
    const sections = document.querySelectorAll('.view-section');
    const pageTitle = document.getElementById('pageTitle');

    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const view = link.getAttribute('data-view');

            navLinks.forEach(l => l.classList.remove('active'));
            link.classList.add('active');

            sections.forEach(s => {
                s.classList.add('hidden');
                if (s.id === view) s.classList.remove('hidden');
            });

            if (view === 'view-dashboard') pageTitle.textContent = "Vue d'ensemble";
            if (view === 'view-reports') pageTitle.textContent = "Intelligence Financière & Rapports";
            if (view === 'view-predictions') {
                pageTitle.textContent = "Intelligence Industrielle";
                loadFullHistory();
            }
            if (view === 'view-rh') {
                pageTitle.textContent = "Croissance du site";
                loadHRData();
            }
            if (view === 'view-parts') {
                pageTitle.textContent = "Gestion des Pièces de Rechange";
                loadPartsForecast();
            }
        });
    });

    function loadFullHistory() {
        const tbody = document.getElementById('allPredictionsBody');
        if (!tbody) return;

        fetchAuth('/predictions?limit=50')
            .then(res => res.json())
            .then(data => {
                tbody.innerHTML = '';
                data.forEach(p => {
                    const tr = document.createElement('tr');
                    const prob = p.failure_probability * 100;
                    const isCritical = prob > 80;

                    if (isCritical) {
                        tr.style.backgroundColor = 'rgba(239, 68, 68, 0.05)';
                        tr.style.borderLeft = '3px solid #ef4444';
                    }

                    tr.innerHTML = `
                        <td style="opacity: 0.8; font-size: 0.8rem;">${new Date(p.prediction_date).toLocaleDateString()}</td>
                        <td style="color: var(--electric-blue); font-weight: 700; letter-spacing: 0.5px;">${p.vehicle_id}</td>
                        <td>${p.engine_model}</td>
                        <td>${p.vehicle_age || '0'} ans</td>
                        <td>${p.total_mileage || '0'} km</td>
                        <td><span class="badge" style="background: ${p.warranty === 'Oui' ? 'rgba(239, 68, 68, 0.1)' : 'rgba(16, 185, 129, 0.1)'}; color: ${p.warranty === 'Oui' ? '#ef4444' : '#10b981'}; padding: 4px 8px; border-radius: 6px; font-size: 0.75rem; font-weight: 600;">${p.warranty}</span></td>
                        <td>${p.service_start_date || '-'}</td>
                        <td>${p.region || 'Global'}</td>
                        <td>${p.city || '-'}</td>
                        <td>${p.defective_part || '-'}</td>
                        <td style="color: var(--vibrant-purple); font-weight: 600;">${p.impacted_part || '-'}</td>
                        <td style="font-weight: 600;">${p.failure_type}</td>
                        <td>
                            <div style="display: flex; align-items: center; gap: 8px;">
                                <div style="width: 40px; height: 6px; background: rgba(255,255,255,0.1); border-radius: 10px; overflow: hidden;">
                                    <div style="width: ${prob}%; height: 100%; background: ${prob > 80 ? '#ef4444' : (prob > 50 ? '#f59e0b' : '#10b981')};"></div>
                                </div>
                                <span style="font-weight: 700; color: ${prob > 80 ? '#ef4444' : (prob > 50 ? '#f59e0b' : '#fff')}">${prob.toFixed(0)}%</span>
                            </div>
                        </td>
                        <td>
                            <span style="background: rgba(255,255,255,0.05); padding: 4px 10px; border-radius: 20px; font-weight: 700; border: 1px solid rgba(255,255,255,0.1);">
                                ${p.days_before_failure} j
                            </span>
                        </td>
                    `;
                    tbody.appendChild(tr);
                });

                // Apply initial visibility from checkboxes
                const colCheckboxes = document.querySelectorAll('#col-dropdown-content input[type="checkbox"]');
                colCheckboxes.forEach(cb => {
                    if (!cb.checked) {
                        const colIdx = parseInt(cb.getAttribute('data-col'));
                        // Hide header
                        const th = document.querySelectorAll('#allPredictionsTable thead th')[colIdx - 1];
                        if (th) th.style.display = 'none';
                        // Hide cells
                        const cells = document.querySelectorAll(`#allPredictionsTable tbody tr td:nth-child(${colIdx})`);
                        cells.forEach(td => td.style.display = 'none');
                    }
                });

                // Apply Search Filter if exists
                applySearchFilter();
            });
    }

    function applySearchFilter() {
        const input = document.getElementById('prediction-main-filter');
        if (!input) return;
        const filter = input.value.toLowerCase();
        const table = document.getElementById('allPredictionsTable');
        if (!table) return;

        const rows = table.querySelectorAll('tbody tr');
        rows.forEach(row => {
            const text = row.innerText.toLowerCase();
            row.style.display = text.includes(filter) ? '' : 'none';
        });
    }

    // 5b. RH Data Logic
    let hrChartInstance = null;

    function loadHRData() {
        fetchAuth('/api/kpi/hr/regional_stats')
            .then(res => res.json())
            .then(data => {
                // Update KPIs
                const totalCurrent = data.current_techs.reduce((a, b) => a + b, 0);
                const totalRequired = data.required_techs.reduce((a, b) => a + b, 0);
                const gap = totalCurrent - totalRequired;

                document.getElementById('rh-total-current').textContent = totalCurrent;
                document.getElementById('rh-total-required').textContent = totalRequired;

                const gapEl = document.getElementById('rh-gap');
                if (gapEl) {
                    gapEl.textContent = (gap >= 0 ? '+' : '') + gap;
                    gapEl.style.color = gap < 0 ? '#ef4444' : '#10b981';
                }

                // Render Chart
                renderHRRegionChart(data);
            })
            .catch(err => console.error("Error loading HR data", err));
    }

    function renderHRRegionChart(data) {
        const ctx = document.getElementById('hrRegionChart').getContext('2d');
        const accentColor = getComputedStyle(document.documentElement).getPropertyValue('--electric-blue').trim();

        if (hrChartInstance) hrChartInstance.destroy();

        hrChartInstance = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.labels,
                datasets: [
                    {
                        label: 'Techniciens Actuels',
                        data: data.current_techs,
                        backgroundColor: accentColor,
                        borderRadius: 8
                    },
                    {
                        label: 'Besoin Requis',
                        data: data.required_techs,
                        backgroundColor: 'rgba(251, 191, 36, 0.8)', // Amber/Warning color
                        borderRadius: 8
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { labels: { color: '#94a3b8' } },
                    tooltip: { mode: 'index', intersect: false }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: { color: 'rgba(255,255,255,0.05)' },
                        ticks: { color: '#94a3b8' }
                    },
                    x: {
                        grid: { display: false },
                        ticks: { color: '#94a3b8' }
                    }
                }
            }
        });
    }

    // 6. CSV Upload & Chat Integration
    const importBtn = document.getElementById('btn-import-csv');
    const csvInput = document.getElementById('csvFileInput');

    if (importBtn && csvInput) {
        importBtn.addEventListener('click', () => csvInput.click());
        csvInput.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (!file) return;

            const formData = new FormData();
            formData.append('file', file);

            // Show animation or chat feedback
            const win = document.getElementById('chatWindow');
            win.style.opacity = '1';
            win.style.transform = 'scale(1)';
            win.style.pointerEvents = 'all';

            fetchAuth('/predict/csv', { method: 'POST', body: formData })
                .then(res => res.json())
                .then(data => {
                    if (data.status === 'success') {
                        loadProKPIs();
                        loadRecentPredictions();
                        loadFullHistory();

                        showToast(`Importation réussie : ${data.count} pannes détectées.`, 'Success');

                        // Add message to chat for deep analysis
                        const msg = document.createElement('div');
                        msg.className = 'glass';
                        msg.style.padding = '1rem';
                        msg.style.borderRadius = '16px';
                        msg.style.background = 'rgba(16, 185, 129, 0.1)';
                        msg.textContent = `Succès ! ${data.count} nouvelles données d'intelligence importées.`;
                        document.getElementById('chatMessages').appendChild(msg);
                    }
                });
        });
    }

    // 7. Chat Logic
    const chatInput = document.getElementById('chatInput');
    const sendBtn = document.getElementById('sendBtn');
    const msgContainer = document.getElementById('chatMessages');

    async function handleChat() {
        const text = chatInput.value.trim();
        if (!text) return;

        // User message
        const userMsg = document.createElement('div');
        userMsg.style.padding = '1rem';
        userMsg.style.borderRadius = '16px';
        userMsg.style.background = 'var(--electric-blue)';
        userMsg.style.alignSelf = 'flex-end';
        userMsg.style.fontSize = '0.9rem';
        userMsg.textContent = text;
        msgContainer.appendChild(userMsg);
        chatInput.value = '';

        try {
            const res = await fetchAuth('/ask', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ question: text })
            });
            const rawData = await res.json();

            // The backend now returns a JSON string in 'answer'
            let data;
            data = rawData.answer;
            if (typeof data === 'string') {
                try {
                    data = JSON.parse(data);
                } catch (e) {
                    data = { answer: rawData.answer, visualization: { type: 'none' } };
                }
            }

            // 1. Render text message
            const aiMsg = document.createElement('div');
            aiMsg.className = 'glass';
            aiMsg.style.padding = '1rem';
            aiMsg.style.borderRadius = '16px';
            aiMsg.style.maxWidth = '85%';
            aiMsg.style.fontSize = '0.9rem';
            aiMsg.innerHTML = data.answer.replace(/\n/g, '<br>');
            msgContainer.appendChild(aiMsg);

            // 2. Render Chart if available
            if (data.visualization && data.visualization.type !== 'none') {
                const chartContainer = document.createElement('div');
                chartContainer.className = 'glass';
                chartContainer.style.marginTop = '10px';
                chartContainer.style.padding = '15px';
                chartContainer.style.borderRadius = '20px';
                chartContainer.style.width = '100%';
                chartContainer.style.height = '280px';
                chartContainer.style.border = '1px solid rgba(59, 130, 246, 0.2)';

                const canvas = document.createElement('canvas');
                chartContainer.appendChild(canvas);
                msgContainer.appendChild(chartContainer);

                new Chart(canvas, {
                    type: data.visualization.type || 'bar',
                    data: {
                        labels: data.visualization.labels || [],
                        datasets: [{
                            label: data.visualization.title || 'Analyse',
                            data: data.visualization.values || [],
                            backgroundColor: data.visualization.type === 'pie' || data.visualization.type === 'doughnut'
                                ? ['#3b82f6', '#a855f7', '#10b981', '#fbbf24', '#ef4444', '#6366f1']
                                : 'rgba(59, 130, 246, 0.4)',
                            borderColor: '#3b82f6',
                            borderWidth: 2,
                            borderRadius: data.visualization.type === 'bar' ? 8 : 0,
                            tension: 0.4 // Smooth lines
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                display: data.visualization.type === 'pie' || data.visualization.type === 'doughnut',
                                position: 'bottom',
                                labels: { color: '#f8fafc', font: { size: 10, weight: '600' } }
                            },
                            title: {
                                display: true,
                                text: data.visualization.title || '',
                                color: '#fff',
                                font: { size: 14, weight: 'bold' }
                            }
                        },
                        scales: data.visualization.type === 'bar' || data.visualization.type === 'line' ? {
                            y: {
                                grid: { color: 'rgba(255,255,255,0.05)' },
                                ticks: { color: '#94a3b8', font: { size: 10 } },
                                border: { display: false }
                            },
                            x: {
                                grid: { display: false },
                                ticks: { color: '#94a3b8', font: { size: 10 } },
                                border: { display: false }
                            }
                        } : {}
                    }
                });
            }

            msgContainer.scrollTop = msgContainer.scrollHeight;
        } catch (e) {
            console.error("Chat error:", e);
            const errDiv = document.createElement('div');
            errDiv.style.color = '#ef4444';
            errDiv.textContent = "Désolé, une erreur technique s'est produite.";
            msgContainer.appendChild(errDiv);
        }
    }

    sendBtn.addEventListener('click', handleChat);
    chatInput.addEventListener('keypress', (e) => { if (e.key === 'Enter') handleChat(); });

    // Startup
    loadProKPIs();
    loadRegionChart();
    loadRecentPredictions();

    // Restore Accent Color
    const savedAccent = localStorage.getItem('accent_color');
    if (savedAccent) {
        document.documentElement.style.setProperty('--electric-blue', savedAccent);
    }

    // --- Profile Management ---
    const btnSaveProfile = document.getElementById('btn-save-profile');
    if (btnSaveProfile) {
        btnSaveProfile.addEventListener('click', async () => {
            const name = document.getElementById('input-name').value;
            const phone = document.getElementById('input-phone').value;

            try {
                const res = await fetchAuth('/api/auth/profile', {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ full_name: name, phone: phone })
                });

                if (res.ok) {
                    document.getElementById('profile-name-display').textContent = name;
                    const sidebarName = document.querySelector('.user-pill div[style*="font-weight: 600"]');
                    if (sidebarName) sidebarName.textContent = name;
                    alert("Modifications enregistrées !");
                }
            } catch (err) {
                alert("Erreur lors de la sauvegarde.");
            }
        });
    }

    // Load Profile from Backend
    async function loadUserProfile() {
        try {
            const res = await fetchAuth('/api/auth/me');
            if (res.ok) {
                const p = await res.json();
                document.getElementById('input-name').value = p.full_name;
                document.getElementById('profile-name-display').textContent = p.full_name;
                document.getElementById('profile-role-display').textContent = p.role;
                document.getElementById('input-role').value = p.role;
                document.getElementById('input-email').value = p.email;
                document.getElementById('input-phone').value = p.phone;

                const sidebarName = document.querySelector('.user-pill div[style*="font-weight: 600"]');
                const sidebarRole = document.querySelector('.user-pill div[style*="var(--text-muted)"]');
                if (sidebarName) sidebarName.textContent = p.full_name;
                if (sidebarRole) sidebarRole.textContent = p.role;
            }
        } catch (err) {
            console.error("Error loading profile", err);
        }
    }
    loadUserProfile();

    // --- Security (Password) ---
    const btnChangePwd = document.getElementById('btn-change-pwd');
    if (btnChangePwd) {
        btnChangePwd.addEventListener('click', () => {
            const current = document.getElementById('current-pwd').value;
            const newP = document.getElementById('new-pwd').value;
            const confirmP = document.getElementById('confirm-pwd').value;

            if (!current || !newP || !confirmP) {
                alert("Veuillez remplir tous les champs.");
                return;
            }
            if (newP !== confirmP) {
                alert("Les nouveaux mots de passe ne correspondent pas.");
                return;
            }

            // API Call
            btnChangePwd.textContent = "Traitement...";
            fetchAuth('/api/auth/change-password', {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ current_password: current, new_password: newP })
            }).then(res => {
                if (res.ok) {
                    alert("Mot de passe mis à jour avec succès !");
                    document.getElementById('current-pwd').value = '';
                    document.getElementById('new-pwd').value = '';
                    document.getElementById('confirm-pwd').value = '';
                } else {
                    alert("Erreur : Vérifiez votre ancien mot de passe.");
                }
                btnChangePwd.textContent = "Mettre à jour le mot de passe";
            });
        });
    }

    // 9. Report Downloads Logic
    function downloadReport(url, filename) {
        fetchAuth(url)
            .then(res => {
                if (res.status === 200) return res.blob();
                throw new Error("Erreur lors de la génération du rapport");
            })
            .then(blob => {
                const link = document.createElement('a');
                link.href = window.URL.createObjectURL(blob);
                link.download = filename;
                link.click();
            })
            .catch(err => {
                console.error(err);
                alert("Impossible de télécharger le rapport. Veuillez réessayer plus tard.");
            });
    }

    const btnExport = document.getElementById('btn-export-report');
    if (btnExport) {
        btnExport.addEventListener('click', () => {
            downloadReport('/api/reports/export_global', `Global_Report_${new Date().toISOString().split('T')[0]}.xlsx`);
        });
    }

    const btnWeekly = document.getElementById('btn-weekly-report');
    if (btnWeekly) {
        btnWeekly.addEventListener('click', () => {
            downloadReport('/api/reports/weekly', `Weekly_Report_${new Date().toISOString().split('T')[0]}.xlsx`);
        });
    }

    const btnAudit = document.getElementById('btn-monthly-audit');
    if (btnAudit) {
        btnAudit.addEventListener('click', () => {
            downloadReport('/api/reports/audit', `Audit_Mensuel_${new Date().toISOString().split('T')[0]}.xlsx`);
        });
    }

    // 10. Logout Logic
    const btnLogout = document.getElementById('btn-logout');
    if (btnLogout) {
        btnLogout.addEventListener('click', () => {
            if (confirm("Voulez-vous vraiment vous déconnecter ?")) {
                // Simulate logout
                // Real logout
                localStorage.removeItem('access_token');
                window.location.href = '/login';
            }
        });
    }

    // 5c. Parts / Inventory Forecast
    function loadPartsForecast() {
        const tbody = document.getElementById('partsForecastBody');
        if (!tbody) return;

        fetchAuth('/api/inventory/forecast')
            .then(res => res.json())
            .then(data => {
                tbody.innerHTML = '';
                document.getElementById('parts-total-needed').textContent = data.length;

                if (data.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="5" style="text-align: center; padding: 2rem;">Aucun besoin imminent détecté par l\'IA.</td></tr>';
                    return;
                }

                data.forEach(p => {
                    if (p.part_name === 'Inconnu') return; // Filter out unknown parts

                    const tr = document.createElement('tr');
                    let badgeClass = 'badge-success';
                    if (p.criticality === 'Élevée') badgeClass = 'badge-danger';
                    else if (p.criticality === 'Moyenne') badgeClass = 'badge-warning';

                    tr.innerHTML = `
                        <td style="font-weight: 600; color: var(--electric-blue);">${p.part_name}</td>
                        <td>${p.quantity_required}</td>
                        <td>${p.need_date}</td>
                        <td><span style="font-weight: 700;">${p.days_remaining} j</span></td>
                        <td><span class="badge-pro ${badgeClass}">${p.criticality}</span></td>
                    `;
                    tbody.appendChild(tr);
                });
            })
            .catch(err => console.error("Error loading parts forecast", err));
    }

    // 11. Automated Notifications (AI Agent)
    const btnNotif = document.getElementById('btn-notifications');
    const notifBadge = document.getElementById('notif-badge');
    const notifDropdown = document.getElementById('notif-dropdown');
    const notifList = document.getElementById('notif-list');

    if (btnNotif && notifDropdown) {
        // Toggle Dropdown
        btnNotif.addEventListener('click', (e) => {
            e.stopPropagation();
            notifDropdown.classList.toggle('hidden');
        });

        // Close when clicking outside
        document.addEventListener('click', (e) => {
            if (!btnNotif.contains(e.target) && !notifDropdown.contains(e.target)) {
                notifDropdown.classList.add('hidden');
            }
        });

        function checkNotifications() {
            fetchAuth('/api/notifications')
                .then(res => res.json())
                .then(data => {
                    if (Array.isArray(data)) {
                        renderNotifications(data);
                    } else {
                        console.warn("Notifications API returned non-array data:", data);
                    }
                })
                .catch(err => console.error("Error checking notifications", err));
        }

        function renderNotifications(data) {
            if (!Array.isArray(data)) return;

            // Check for NEW notifications to show toast
            const lastCount = parseInt(notifBadge.textContent || '0');
            if (data.length > lastCount) {
                // New alert!
                const newOne = data[0];
                showToast(newOne.message, newOne.level);
            }

            // Update Badge
            if (data.length > 0) {
                notifBadge.textContent = data.length;
                notifBadge.classList.remove('hidden');
            } else {
                notifBadge.textContent = '0';
                notifBadge.classList.add('hidden');
            }

            // Update List
            if (data.length === 0) {
                notifList.innerHTML = '<div style="padding: 2rem; text-align: center; color: var(--text-muted); font-size: 0.85rem;">Aucune nouvelle notification</div>';
                return;
            }

            notifList.innerHTML = '';
            data.forEach(n => {
                const item = document.createElement('div');
                item.className = 'glass';
                item.style.marginBottom = '8px';
                item.style.padding = '12px';
                item.style.borderRadius = '12px';
                item.style.cursor = 'pointer';
                item.style.borderLeft = n.level === 'Critical' ? '3px solid #ef4444' : '3px solid #3b82f6';

                item.innerHTML = `
                    <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                        <span style="font-weight: 600; font-size: 0.85rem; color: white;">${n.title}</span>
                        <span style="font-size: 0.7rem; color: var(--text-muted);">${n.time}</span>
                    </div>
                    <p style="font-size: 0.8rem; color: #cbd5e1; line-height: 1.4;">${n.message}</p>
                `;

                // Mark as read on click
                item.addEventListener('click', () => {
                    fetchAuth(`/api/notifications/${n.id}/read`, { method: 'PUT' })
                        .then(() => {
                            item.remove();
                            // Update badge locally
                            const count = parseInt(notifBadge.textContent || '0') - 1;
                            if (count <= 0) {
                                notifBadge.classList.add('hidden');
                                notifBadge.textContent = '0';
                                notifList.innerHTML = '<div style="padding: 2rem; text-align: center; color: var(--text-muted); font-size: 0.85rem;">Aucune nouvelle notification</div>';
                            } else {
                                notifBadge.textContent = count;
                            }
                        });
                });

                notifList.appendChild(item);
            });
        }

        // Initial Check & Polling
        checkNotifications();
        setInterval(checkNotifications, 30000); // Check every 30s
    }

    // 12. Daily AI Briefing Logic
    const btnDaily = document.getElementById('btn-daily-briefing');
    const briefingModal = document.getElementById('briefing-modal');
    const btnCloseBriefing = document.getElementById('btn-close-briefing');
    const briefingContent = document.getElementById('briefing-content');
    const btnPrintBriefing = document.getElementById('btn-print-briefing');

    if (btnDaily && briefingModal) {

        btnDaily.addEventListener('click', () => {
            // Open Modal
            briefingModal.classList.remove('hidden');

            // Show Loader
            briefingContent.innerHTML = `
                <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; color: var(--text-muted);">
                    <div class="loader" style="margin-bottom: 1rem;"></div>
                    <p>L'Agent IA analyse vos données et rédige le rapport...</p>
                </div>
            `;

            // Fetch Report
            fetchAuth('/api/reports/daily-briefing')
                .then(res => res.json())
                .then(data => {
                    // Render Markdown with Marked.js
                    if (window.marked) {
                        briefingContent.innerHTML = window.marked.parse(data.report);
                    } else {
                        briefingContent.innerText = data.report; // Fallback
                    }
                })
                .catch(err => {
                    console.error("Error generating briefing", err);
                    briefingContent.innerHTML = `
                        <div style="text-align: center; color: #ef4444; margin-top: 2rem;">
                            <h3>❌ Erreur</h3>
                            <p>Impossible de joindre l'Agent IA.</p>
                            <code style="background: rgba(0,0,0,0.3); padding: 4px; border-radius: 4px;">${err}</code>
                        </div>
                    `;
                });
        });

        // Close Modal
        btnCloseBriefing.addEventListener('click', () => {
            briefingModal.classList.add('hidden');
        });

        // Close modal when clicking outside of its card
        briefingModal.addEventListener('click', (e) => {
            if (e.target === briefingModal) {
                briefingModal.classList.add('hidden');
            }
        });

        // Print
        if (btnPrintBriefing) {
            btnPrintBriefing.addEventListener('click', () => {
                const printWindow = window.open('', '_blank');
                if (!printWindow) {
                    alert("Le bloqueur de fenêtres empêche l'impression. Veuillez l'autoriser.");
                    return;
                }
                printWindow.document.write(`
                    <html>
                    <head>
                        <title>Rapport Quotidien IA - AnalytixCare</title>
                        <style>
                            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; padding: 3rem; line-height: 1.6; color: #333; }
                            h1 { color: #1e3a8a; border-bottom: 2px solid #1e3a8a; padding-bottom: 10px; }
                            h2 { color: #1e40af; margin-top: 2rem; }
                            table { width: 100%; border-collapse: collapse; margin: 1.5rem 0; }
                            th, td { border: 1px solid #e2e8f0; padding: 12px; text-align: left; }
                            th { background: #f8fafc; font-weight: 600; }
                            blockquote { background: #eff6ff; border-left: 4px solid #3b82f6; padding: 1rem; margin: 1rem 0; font-style: italic; }
                            .footer { margin-top: 3rem; font-size: 0.8rem; color: #64748b; text-align: center; border-top: 1px solid #e2e8f0; padding-top: 1rem; }
                        </style>
                    </head>
                    <body>
                        <div style="text-align: right; color: #64748b; font-size: 0.9rem;">${new Date().toLocaleDateString()}</div>
                        ${briefingContent.innerHTML}
                        <div class="footer">Généré par AnalytixCare AI Agent - Rapport Confidentiel</div>
                        <script>window.print();</script>
                    </body>
                    </html>
                `);
                printWindow.document.close();
            });
        }
    }

});
