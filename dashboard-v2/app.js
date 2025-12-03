/**
 * Email Warehouse Dashboard v2.0
 * Interactive dashboard with Gemini RAG integration
 */

class EmailWarehouseDashboard {
    constructor() {
        this.emails = [];
        this.charts = {};
        this.currentView = 'overview';
        this.queryHistory = [];

        // Configuration
        this.config = {
            warehousePath: 'warehouse/daily',  // Server runs from project root
            apiKey: null,
            ragEnabled: true,
            ragApiUrl: 'http://localhost:5000/api'
        };

        this.init();
    }

    async init() {
        console.log('Initializing Email Warehouse Dashboard...');

        // Load data
        await this.loadEmails();

        // Setup event listeners
        this.setupEventListeners();

        // Render initial view
        this.renderOverview();

        // Check for RAG API key
        this.checkRAGStatus();

        console.log(`Dashboard loaded: ${this.emails.length} emails`);
    }

    async loadEmails() {
        try {
            // Load daily JSON files
            const files = await this.getAvailableFiles();

            for (const file of files) {
                try {
                    const response = await fetch(`${this.config.warehousePath}/${file}`);
                    const data = await response.json();

                    if (data.emails && Array.isArray(data.emails)) {
                        this.emails.push(...data.emails);
                    }
                } catch (error) {
                    console.warn(`Failed to load ${file}:`, error);
                }
            }

            // Update header stats
            this.updateHeaderStats();

        } catch (error) {
            console.error('Failed to load emails:', error);
            this.showError('Failed to load email data');
        }
    }

    async getAvailableFiles() {
        // Generate file list for 2025
        const files = [];
        const startDate = new Date('2025-06-01');
        const endDate = new Date('2025-12-03');

        for (let d = new Date(startDate); d <= endDate; d.setDate(d.getDate() + 1)) {
            const filename = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}.json`;
            files.push(filename);
        }

        return files;
    }

    updateHeaderStats() {
        document.getElementById('totalEmails').textContent = this.emails.length.toLocaleString();

        if (this.emails.length > 0) {
            const dates = this.emails.map(e => new Date(e.date)).sort();
            const start = dates[0].toLocaleDateString();
            const end = dates[dates.length - 1].toLocaleDateString();
            document.getElementById('dateRange').textContent = `${start} - ${end}`;

            const uniqueSenders = new Set(this.emails.map(e => e.from?.email || e.from)).size;
            document.getElementById('uniqueSenders').textContent = uniqueSenders;
        }
    }

    setupEventListeners() {
        // Navigation
        document.querySelectorAll('.nav-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const view = e.target.dataset.view;
                this.switchView(view);
            });
        });

        // Search
        document.getElementById('searchBtn')?.addEventListener('click', () => {
            this.performSearch();
        });

        document.getElementById('searchInput')?.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.performSearch();
            }
        });

        // RAG Query
        document.getElementById('ragQueryBtn')?.addEventListener('click', () => {
            this.performRAGQuery();
        });

        document.getElementById('ragQueryInput')?.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.performRAGQuery();
            }
        });

        // Example questions
        document.querySelectorAll('.example-question').forEach(btn => {
            btn.addEventListener('click', (e) => {
                document.getElementById('ragQueryInput').value = e.target.textContent;
                this.performRAGQuery();
            });
        });

        // Modal
        document.getElementById('closeModal')?.addEventListener('click', () => {
            this.closeModal();
        });

        // Refresh
        document.getElementById('refreshBtn')?.addEventListener('click', () => {
            this.renderOverview();
        });

        // Timeline granularity
        document.getElementById('timelineGranularity')?.addEventListener('change', () => {
            this.renderTimeline();
        });
    }

    switchView(viewName) {
        // Update navigation
        document.querySelectorAll('.nav-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.view === viewName);
        });

        // Hide all views
        document.querySelectorAll('.view').forEach(view => {
            view.classList.add('hidden');
        });

        // Show selected view
        document.getElementById(`view-${viewName}`)?.classList.remove('hidden');

        this.currentView = viewName;

        // Render view-specific content
        switch (viewName) {
            case 'overview':
                this.renderOverview();
                break;
            case 'analytics':
                this.renderAnalytics();
                break;
            case 'timeline':
                this.renderTimeline();
                break;
            case 'search':
                // Search is interactive, don't pre-render
                break;
            case 'rag':
                this.renderRAG();
                break;
        }
    }

    renderOverview() {
        // Update stats
        const received = this.emails.filter(e => e.type === 'received').length;
        const sent = this.emails.filter(e => e.type === 'sent').length;

        document.getElementById('stat-total').textContent = this.emails.length.toLocaleString();
        document.getElementById('stat-received').textContent = received.toLocaleString();
        document.getElementById('stat-sent').textContent = sent.toLocaleString();

        // Render charts
        this.renderVolumeChart();
        this.renderTypeChart();

        // Render recent emails
        this.renderRecentEmails();
    }

    renderVolumeChart() {
        const ctx = document.getElementById('volumeChart');
        if (!ctx) return;

        // Destroy existing chart
        if (this.charts.volume) {
            this.charts.volume.destroy();
        }

        // Group emails by week
        const weeklyData = this.groupByWeek(this.emails);

        this.charts.volume = new Chart(ctx, {
            type: 'line',
            data: {
                labels: weeklyData.labels,
                datasets: [{
                    label: 'Emails',
                    data: weeklyData.values,
                    borderColor: '#2563eb',
                    backgroundColor: 'rgba(37, 99, 235, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }

    renderTypeChart() {
        const ctx = document.getElementById('typeChart');
        if (!ctx) return;

        if (this.charts.type) {
            this.charts.type.destroy();
        }

        const received = this.emails.filter(e => e.type === 'received').length;
        const sent = this.emails.filter(e => e.type === 'sent').length;

        this.charts.type = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Received', 'Sent'],
                datasets: [{
                    data: [received, sent],
                    backgroundColor: ['#2563eb', '#10b981'],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }

    renderRecentEmails() {
        const container = document.getElementById('recentEmails');
        if (!container) return;

        // Get last 10 emails
        const recentEmails = this.emails
            .sort((a, b) => new Date(b.date) - new Date(a.date))
            .slice(0, 10);

        container.innerHTML = recentEmails.map(email => this.createEmailCard(email)).join('');

        // Add click handlers
        container.querySelectorAll('.email-item').forEach((item, index) => {
            item.addEventListener('click', () => {
                this.showEmailDetail(recentEmails[index]);
            });
        });
    }

    createEmailCard(email) {
        const date = new Date(email.date).toLocaleDateString();
        const sender = typeof email.from === 'string' ? email.from : (email.from?.name || email.from?.email || 'Unknown');
        const subject = email.subject || '(No Subject)';
        const preview = email.body_preview || email.body?.substring(0, 100) || '';

        return `
            <div class="email-item">
                <div class="email-header">
                    <div class="email-sender">${this.escapeHtml(sender)}</div>
                    <div class="email-date">${date}</div>
                </div>
                <div class="email-subject">${this.escapeHtml(subject)}</div>
                <div class="email-preview">${this.escapeHtml(preview)}</div>
                <div class="email-badges">
                    <span class="badge ${email.type === 'received' ? 'badge-primary' : 'badge-secondary'}">
                        ${email.type}
                    </span>
                    ${email.importance === 'high' ? '<span class="badge badge-warning">Important</span>' : ''}
                </div>
            </div>
        `;
    }

    renderAnalytics() {
        this.renderTopSenders();
        this.renderTopRecipients();
        this.renderVendorAnalysis();
        this.renderPropertyAnalysis();
    }

    renderTopSenders() {
        const tbody = document.getElementById('topSendersTable');
        if (!tbody) return;

        const senderCounts = {};
        this.emails.forEach(email => {
            const sender = typeof email.from === 'string' ? email.from : (email.from?.email || 'Unknown');
            senderCounts[sender] = (senderCounts[sender] || 0) + 1;
        });

        const sorted = Object.entries(senderCounts)
            .sort((a, b) => b[1] - a[1])
            .slice(0, 10);

        const total = this.emails.length;

        tbody.innerHTML = sorted.map(([sender, count]) => `
            <tr>
                <td>${this.escapeHtml(sender)}</td>
                <td>${count}</td>
                <td>${((count / total) * 100).toFixed(1)}%</td>
            </tr>
        `).join('');
    }

    renderTopRecipients() {
        const tbody = document.getElementById('topRecipientsTable');
        if (!tbody) return;

        const recipientCounts = {};
        this.emails.forEach(email => {
            if (Array.isArray(email.to)) {
                email.to.forEach(recipient => {
                    const addr = typeof recipient === 'string' ? recipient : recipient.email;
                    recipientCounts[addr] = (recipientCounts[addr] || 0) + 1;
                });
            }
        });

        const sorted = Object.entries(recipientCounts)
            .sort((a, b) => b[1] - a[1])
            .slice(0, 10);

        const total = this.emails.length;

        tbody.innerHTML = sorted.map(([recipient, count]) => `
            <tr>
                <td>${this.escapeHtml(recipient)}</td>
                <td>${count}</td>
                <td>${((count / total) * 100).toFixed(1)}%</td>
            </tr>
        `).join('');
    }

    renderVendorAnalysis() {
        const container = document.getElementById('vendorAnalysis');
        if (!container) return;

        const vendors = ['Waste Management', 'Republic Services', 'Ally Waste', 'DSQ'];
        const vendorEmails = {};

        vendors.forEach(vendor => {
            vendorEmails[vendor] = this.emails.filter(email => {
                const text = `${email.subject} ${email.body || ''}`.toLowerCase();
                return text.includes(vendor.toLowerCase());
            }).length;
        });

        container.innerHTML = `
            <div class="grid grid-4">
                ${vendors.map(vendor => `
                    <div class="stat-card">
                        <div class="stat-card-value">${vendorEmails[vendor]}</div>
                        <div class="stat-card-label">${vendor}</div>
                    </div>
                `).join('')}
            </div>
        `;
    }

    renderPropertyAnalysis() {
        const container = document.getElementById('propertyAnalysis');
        if (!container) return;

        const properties = ['Jones Grant', 'Columbia Square', 'Boardwalk', 'Station 21'];
        const propertyEmails = {};

        properties.forEach(property => {
            propertyEmails[property] = this.emails.filter(email => {
                const text = `${email.subject} ${email.body || ''}`.toLowerCase();
                return text.includes(property.toLowerCase());
            }).length;
        });

        container.innerHTML = `
            <div class="grid grid-4">
                ${properties.map(property => `
                    <div class="stat-card">
                        <div class="stat-card-value">${propertyEmails[property]}</div>
                        <div class="stat-card-label">${property}</div>
                    </div>
                `).join('')}
            </div>
        `;
    }

    renderTimeline() {
        const ctx = document.getElementById('timelineChart');
        if (!ctx) return;

        if (this.charts.timeline) {
            this.charts.timeline.destroy();
        }

        const granularity = document.getElementById('timelineGranularity').value;
        const data = this.groupByGranularity(this.emails, granularity);

        this.charts.timeline = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.labels,
                datasets: [{
                    label: 'Emails',
                    data: data.values,
                    backgroundColor: '#2563eb'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                }
            }
        });

        // Day of week chart
        this.renderDayOfWeekChart();
    }

    renderDayOfWeekChart() {
        const ctx = document.getElementById('dayOfWeekChart');
        if (!ctx) return;

        if (this.charts.dayOfWeek) {
            this.charts.dayOfWeek.destroy();
        }

        const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
        const dayCounts = new Array(7).fill(0);

        this.emails.forEach(email => {
            const day = new Date(email.date).getDay();
            dayCounts[day]++;
        });

        this.charts.dayOfWeek = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: days,
                datasets: [{
                    label: 'Emails',
                    data: dayCounts,
                    backgroundColor: '#10b981'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                }
            }
        });
    }

    renderRAG() {
        // Just update the query history
        this.updateQueryHistory();
    }

    performSearch() {
        const query = document.getElementById('searchInput').value.toLowerCase();
        const resultsContainer = document.getElementById('searchResults');
        const countContainer = document.getElementById('searchCount');

        if (!query) {
            resultsContainer.innerHTML = '<div class="loading">Enter a search query to begin</div>';
            return;
        }

        const results = this.emails.filter(email => {
            const searchText = `${email.subject} ${email.body || ''} ${email.from}`.toLowerCase();
            return searchText.includes(query);
        });

        countContainer.textContent = `${results.length} results found`;
        resultsContainer.innerHTML = results.slice(0, 50).map(email => this.createEmailCard(email)).join('');

        // Add click handlers
        resultsContainer.querySelectorAll('.email-item').forEach((item, index) => {
            item.addEventListener('click', () => {
                this.showEmailDetail(results[index]);
            });
        });
    }

    async performRAGQuery() {
        const query = document.getElementById('ragQueryInput').value;
        if (!query) return;

        const loadingEl = document.getElementById('ragLoading');
        const resultsEl = document.getElementById('ragResults');
        const answerEl = document.getElementById('ragAnswer');

        loadingEl.classList.remove('hidden');
        resultsEl.classList.add('hidden');

        try {
            // Call the Flask backend API
            const response = await fetch(`${this.config.ragApiUrl}/query`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    question: query,
                    max_chunks: 10
                })
            });

            if (!response.ok) {
                throw new Error(`API returned ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();

            if (data.status === 'error') {
                throw new Error(data.error);
            }

            // Display the answer
            answerEl.innerHTML = `
                <div class="success">
                    <strong>Question:</strong> ${this.escapeHtml(query)}
                    <div style="margin-top: 1rem; padding: 1rem; background: #f0f9ff; border-left: 4px solid #2563eb; border-radius: 0.25rem;">
                        ${this.formatAnswer(data.answer)}
                    </div>
                    <div style="margin-top: 0.5rem; font-size: 0.875rem; color: #6b7280;">
                        Found ${data.chunks_found} relevant email sections
                    </div>
                </div>
            `;

            // Add to history
            this.queryHistory.unshift({
                query,
                timestamp: new Date(),
                answered: true,
                answer: data.answer
            });

            loadingEl.classList.add('hidden');
            resultsEl.classList.remove('hidden');

            this.updateQueryHistory();

        } catch (error) {
            console.error('RAG query failed:', error);
            answerEl.innerHTML = `
                <div class="error" style="padding: 1rem; background: #fef2f2; border-left: 4px solid #ef4444; border-radius: 0.25rem;">
                    <strong>Error:</strong> ${this.escapeHtml(error.message)}
                    <p style="margin-top: 0.5rem; font-size: 0.875rem;">
                        Make sure the Flask API server is running:
                    </p>
                    <pre style="background: #1f2937; color: #f9fafb; padding: 0.5rem; border-radius: 0.25rem; margin-top: 0.5rem; font-size: 0.75rem;">cd api
python rag_api.py</pre>
                </div>
            `;
            loadingEl.classList.add('hidden');
            resultsEl.classList.remove('hidden');
        }
    }

    formatAnswer(answer) {
        // Convert markdown-style formatting to HTML
        return answer
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/\n\n/g, '</p><p style="margin-top: 0.75rem;">')
            .replace(/\n/g, '<br>')
            .replace(/^(.*)$/, '<p>$1</p>');
    }

    updateQueryHistory() {
        const container = document.getElementById('queryHistory');
        if (!container || this.queryHistory.length === 0) return;

        container.innerHTML = this.queryHistory.slice(0, 5).map(item => `
            <div class="timeline-item">
                <div class="timeline-date">${item.timestamp.toLocaleString()}</div>
                <div class="timeline-content">
                    <strong>Q:</strong> ${this.escapeHtml(item.query)}
                </div>
            </div>
        `).join('');
    }

    checkRAGStatus() {
        // Check if RAG is available
        // For now, always show as available but with instructions
        console.log('RAG interface available - configure API key for live queries');
    }

    showEmailDetail(email) {
        const modal = document.getElementById('emailModal');
        const detail = document.getElementById('emailDetail');

        const date = new Date(email.date).toLocaleString();
        const sender = typeof email.from === 'string' ? email.from : (email.from?.name || email.from?.email || 'Unknown');

        detail.innerHTML = `
            <div style="margin-bottom: 1rem;">
                <strong>From:</strong> ${this.escapeHtml(sender)}<br>
                <strong>Date:</strong> ${date}<br>
                <strong>Subject:</strong> ${this.escapeHtml(email.subject || '(No Subject)')}<br>
                <strong>Type:</strong> <span class="badge ${email.type === 'received' ? 'badge-primary' : 'badge-secondary'}">${email.type}</span>
            </div>
            <div style="border-top: 1px solid #e5e7eb; padding-top: 1rem;">
                <strong>Body:</strong>
                <div style="margin-top: 0.5rem; white-space: pre-wrap;">
                    ${this.escapeHtml(email.body || email.body_preview || '(No content)')}
                </div>
            </div>
        `;

        modal.classList.add('active');
    }

    closeModal() {
        document.getElementById('emailModal').classList.remove('active');
    }

    // Utility functions
    groupByWeek(emails) {
        const weeks = {};

        emails.forEach(email => {
            const date = new Date(email.date);
            const weekStart = new Date(date);
            weekStart.setDate(date.getDate() - date.getDay());
            const weekKey = weekStart.toISOString().split('T')[0];

            weeks[weekKey] = (weeks[weekKey] || 0) + 1;
        });

        const sorted = Object.entries(weeks).sort((a, b) => a[0].localeCompare(b[0]));

        return {
            labels: sorted.map(([date]) => new Date(date).toLocaleDateString()),
            values: sorted.map(([, count]) => count)
        };
    }

    groupByGranularity(emails, granularity) {
        const groups = {};

        emails.forEach(email => {
            const date = new Date(email.date);
            let key;

            if (granularity === 'day') {
                key = date.toISOString().split('T')[0];
            } else if (granularity === 'week') {
                const weekStart = new Date(date);
                weekStart.setDate(date.getDate() - date.getDay());
                key = weekStart.toISOString().split('T')[0];
            } else {
                key = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
            }

            groups[key] = (groups[key] || 0) + 1;
        });

        const sorted = Object.entries(groups).sort((a, b) => a[0].localeCompare(b[0]));

        return {
            labels: sorted.map(([date]) => {
                if (granularity === 'month') {
                    return new Date(date + '-01').toLocaleDateString('en-US', { year: 'numeric', month: 'short' });
                }
                return new Date(date).toLocaleDateString();
            }),
            values: sorted.map(([, count]) => count)
        };
    }

    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    showError(message) {
        console.error(message);
        // Could show a toast notification here
    }
}

// Initialize dashboard when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new EmailWarehouseDashboard();
});
