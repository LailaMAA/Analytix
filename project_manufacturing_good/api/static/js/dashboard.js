document.addEventListener('DOMContentLoaded', function () {

    // 0. System Defaults
    Chart.defaults.color = '#94a3b8';
    Chart.defaults.font.family = "'Outfit', sans-serif";

    // 1. Initialisation des KPIs
    function loadProKPIs() {
        // Core KPIs
        fetch('/api/kpi/stats')
            .then(res => res.json())
            .then(data => {
                const critEl = document.getElementById('kpi-critical-value');
                if (critEl) critEl.textContent = data.critical_fleet || '0';

                const stockEl = document.getElementById('kpi-stock-value');
                if (stockEl) stockEl.textContent = data.parts_availability + '%';
            });

        // Financial KPIs
        fetch('/api/kpi/financial')
            .then(res => res.json())
            .then(data => {
                const roiEl = document.getElementById('kpi-roi-value');
                if (roiEl) roiEl.textContent = data.avg_roi + '%';
                // Trigger financial chart with real data
                renderFinancialIntelligence(data);
            });

        // HR KPIs
        fetch('/api/kpi/resources')
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
        fetch('/api/kpi/costs-by-region')
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

    // 4. Live Predictions Table
    function loadRecentPredictions() {
        fetch('/predictions?limit=6')
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
                pageTitle.textContent = "Gestion des Ressources Humaines";
                loadHRData();
            }
        });
    });

    function loadFullHistory() {
        const tbody = document.getElementById('allPredictionsBody');
        if (!tbody) return;

        fetch('/predictions?limit=50')
            .then(res => res.json())
            .then(data => {
                tbody.innerHTML = '';
                data.forEach(p => {
                    const tr = document.createElement('tr');
                    tr.innerHTML = `
                        <td>${new Date(p.prediction_date).toLocaleDateString()}</td>
                        <td style="color: var(--electric-blue);">${p.vehicle_id}</td>
                        <td>${p.engine_model}</td>
                        <td>${p.region || 'Global'}</td>
                        <td>${p.failure_type}</td>
                        <td><span style="font-weight: 700;">${p.days_before_failure} j</span></td>
                        <td><span style="color: ${p.warranty === 'Oui' ? '#ef4444' : '#10b981'}">${p.warranty}</span></td>
                        <td>${(p.failure_probability * 100).toFixed(0)}%</td>
                    `;
                    tbody.appendChild(tr);
                });
            });
    }

    // 5b. RH Data Logic
    let hrChartInstance = null;

    function loadHRData() {
        fetch('/api/kpi/hr/regional_stats')
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

            fetch('/predict/csv', { method: 'POST', body: formData })
                .then(res => res.json())
                .then(data => {
                    if (data.status === 'success') {
                        loadProKPIs();
                        loadRecentPredictions();
                        // Add message to chat
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
            const res = await fetch('/ask', {
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
        btnSaveProfile.addEventListener('click', () => {
            const name = document.getElementById('input-name').value;
            const role = document.getElementById('input-role').value;
            const email = document.getElementById('input-email').value;
            const phone = document.getElementById('input-phone').value;

            // Save
            const profile = { name, role, email, phone };
            localStorage.setItem('user_profile', JSON.stringify(profile));

            // Update Visuals immediately
            document.getElementById('profile-name-display').textContent = name;
            document.getElementById('profile-role-display').textContent = role;

            // Update Sidebar
            const sidebarName = document.querySelector('.user-pill div[style*="font-weight: 600"]');
            const sidebarRole = document.querySelector('.user-pill div[style*="var(--text-muted)"]');
            if (sidebarName) sidebarName.textContent = name;
            if (sidebarRole) sidebarRole.textContent = role;

            alert("Modifications enregistrées !");
        });
    }

    // Load Profile
    const savedProfileStr = localStorage.getItem('user_profile');
    if (savedProfileStr) {
        const p = JSON.parse(savedProfileStr);
        if (p.name) {
            document.getElementById('input-name').value = p.name;
            document.getElementById('profile-name-display').textContent = p.name;
            const sidebarName = document.querySelector('.user-pill div[style*="font-weight: 600"]');
            if (sidebarName) sidebarName.textContent = p.name;
        }
        if (p.role) {
            document.getElementById('input-role').value = p.role;
            document.getElementById('profile-role-display').textContent = p.role;
            const sidebarRole = document.querySelector('.user-pill div[style*="var(--text-muted)"]');
            if (sidebarRole) sidebarRole.textContent = p.role;
        }
        if (p.email) document.getElementById('input-email').value = p.email;
        if (p.phone) document.getElementById('input-phone').value = p.phone;
    }

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

            // Simulate API Call
            btnChangePwd.textContent = "Traitement...";
            setTimeout(() => {
                alert("Mot de passe mis à jour avec succès !");
                btnChangePwd.textContent = "Mettre à jour le mot de passe";
                // Clear fields
                document.getElementById('current-pwd').value = '';
                document.getElementById('new-pwd').value = '';
                document.getElementById('confirm-pwd').value = '';
            }, 1000);
        });
    }

    // 9. Report Downloads Logic
    function downloadReport(url, filename) {
        fetch(url)
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
                window.location.href = '/login';
            }
        });
    }

});
