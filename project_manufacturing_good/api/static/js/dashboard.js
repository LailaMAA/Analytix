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

    function renderFinancialIntelligence(finData) {
        if (!finData.chart) return;

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
            colors: ['#3b82f6', '#fbbf24'],
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
    function loadRegionChart() {
        const ctxRegion = document.getElementById('regionChart').getContext('2d');
        fetch('/api/kpi/costs-by-region')
            .then(res => res.json())
            .then(data => {
                new Chart(ctxRegion, {
                    type: 'bar',
                    data: {
                        labels: data.labels,
                        datasets: [{
                            label: 'Risque Budgétaire (kDH)',
                            data: data.data,
                            backgroundColor: 'rgba(168, 85, 247, 0.5)',
                            borderColor: '#a855f7',
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

    // 6. CSV Upload & Chat Integration (Keeping existing robust logic)
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
            // Smart Parsing: Handle both JSON string (Legacy) and Direct Object (Optimized)
            data = rawData.answer;
            if (typeof data === 'string') {
                try {
                    data = JSON.parse(data);
                } catch (e) {
                    // It's just a plain text answer
                    data = { answer: rawData.answer, visualization: { type: 'none' } };
                }
            }
            // If data is already an object, we use it directly.

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

    // 8. Theme Switcher
    const colorOptions = document.querySelectorAll('.color-option');
    colorOptions.forEach(opt => {
        opt.addEventListener('click', () => {
            colorOptions.forEach(o => o.classList.remove('active'));
            opt.classList.add('active');

            // Get the computed background color of the clicked option
            const newColor = window.getComputedStyle(opt).backgroundColor;

            // Update the primary theme variable
            document.documentElement.style.setProperty('--electric-blue', newColor);
        });
    });

});
