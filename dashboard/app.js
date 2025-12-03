/**
 * Email Warehouse Dashboard
 * Client-side application for browsing and searching emails
 */

class EmailDashboard {
    constructor() {
        this.currentDate = null;
        this.emails = [];
        this.threads = [];
        this.projects = {};
        this.currentFilter = 'all';
        this.currentView = 'daily';
        this.searchQuery = '';

        this.init();
    }

    async init() {
        console.log('Initializing Email Dashboard...');

        // Set up event listeners
        this.setupEventListeners();

        // Load available dates
        await this.loadAvailableDates();

        // Load today's data by default
        const today = new Date().toISOString().split('T')[0];
        await this.loadDate(today);
    }

    setupEventListeners() {
        // Date selector
        document.getElementById('dateSelector').addEventListener('change', (e) => {
            this.loadDate(e.target.value);
        });

        // Search box
        const searchBox = document.getElementById('searchBox');
        searchBox.addEventListener('input', (e) => {
            this.searchQuery = e.target.value.toLowerCase();
            this.performSearch();
        });

        // Tab buttons
        document.querySelectorAll('.tab-button').forEach(button => {
            button.addEventListener('click', (e) => {
                this.switchView(e.target.dataset.view);
            });
        });

        // Filter buttons
        document.querySelectorAll('.filter-btn').forEach(button => {
            button.addEventListener('click', (e) => {
                this.applyFilter(e.target.dataset.filter);
            });
        });

        // Modal close buttons
        document.querySelectorAll('.close').forEach(closeBtn => {
            closeBtn.addEventListener('click', () => {
                this.closeModals();
            });
        });

        // Close modal on outside click
        window.addEventListener('click', (e) => {
            if (e.target.classList.contains('modal')) {
                this.closeModals();
            }
        });
    }

    async loadAvailableDates() {
        // In a real implementation, we'd scan the warehouse/daily folder
        // For now, we'll populate with recent dates
        const dateSelector = document.getElementById('dateSelector');
        const dates = [];

        for (let i = 0; i < 30; i++) {
            const date = new Date();
            date.setDate(date.getDate() - i);
            dates.push(date.toISOString().split('T')[0]);
        }

        dateSelector.innerHTML = dates.map(date =>
            `<option value="${date}">${this.formatDate(date)}</option>`
        ).join('');

        dateSelector.value = dates[0];
    }

    async loadDate(date) {
        console.log(`Loading data for ${date}...`);
        this.currentDate = date;

        try {
            // Load daily emails
            const emailData = await this.loadJSON(`../warehouse/daily/${date}.json`);
            if (emailData) {
                this.emails = emailData.emails || [];
                console.log(`Loaded ${this.emails.length} emails`);
            } else {
                this.emails = [];
                console.log('No emails found for this date');
            }

            // Load threads
            const threadData = await this.loadJSON('../warehouse/threads/threads_current.json');
            if (threadData) {
                this.threads = threadData.threads || [];
                this.projects = threadData.projects || {};
                console.log(`Loaded ${this.threads.length} threads`);
            }

            // Render current view
            this.renderCurrentView();

        } catch (error) {
            console.error('Error loading data:', error);
            this.showError('Could not load data for this date. Make sure emails have been exported.');
        }
    }

    async loadJSON(path) {
        try {
            const response = await fetch(path);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.warn(`Could not load ${path}:`, error.message);
            return null;
        }
    }

    switchView(viewName) {
        this.currentView = viewName;

        // Update tab buttons
        document.querySelectorAll('.tab-button').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.view === viewName);
        });

        // Update view visibility
        document.querySelectorAll('.view').forEach(view => {
            view.classList.remove('active');
        });
        document.getElementById(`${viewName}View`).classList.add('active');

        this.renderCurrentView();
    }

    renderCurrentView() {
        switch (this.currentView) {
            case 'daily':
                this.renderDailyView();
                break;
            case 'projects':
                this.renderProjectsView();
                break;
            case 'contacts':
                this.renderContactsView();
                break;
            case 'threads':
                this.renderThreadsView();
                break;
            case 'search':
                this.performSearch();
                break;
        }
    }

    renderDailyView() {
        // Update stats
        const received = this.emails.filter(e => e.type === 'received').length;
        const sent = this.emails.filter(e => e.type === 'sent').length;
        const withAttachments = this.emails.filter(e => e.has_attachments).length;
        const uniqueThreads = new Set(this.emails.map(e => e.conversation_id).filter(Boolean)).size;

        document.getElementById('receivedCount').textContent = received;
        document.getElementById('sentCount').textContent = sent;
        document.getElementById('threadCount').textContent = uniqueThreads;
        document.getElementById('attachmentCount').textContent = withAttachments;

        // Render email list
        this.renderEmailList(this.getFilteredEmails());
    }

    getFilteredEmails() {
        let filtered = [...this.emails];

        switch (this.currentFilter) {
            case 'received':
                filtered = filtered.filter(e => e.type === 'received');
                break;
            case 'sent':
                filtered = filtered.filter(e => e.type === 'sent');
                break;
            case 'high':
                filtered = filtered.filter(e => e.importance === 'high');
                break;
            case 'attachments':
                filtered = filtered.filter(e => e.has_attachments);
                break;
        }

        return filtered;
    }

    applyFilter(filter) {
        this.currentFilter = filter;

        // Update filter button states
        const container = event.target.closest('.filters');
        if (container) {
            container.querySelectorAll('.filter-btn').forEach(btn => {
                btn.classList.toggle('active', btn.dataset.filter === filter);
            });
        }

        if (this.currentView === 'daily') {
            this.renderEmailList(this.getFilteredEmails());
        } else if (this.currentView === 'threads') {
            this.renderThreadsView(filter);
        }
    }

    renderEmailList(emails) {
        const emailList = document.getElementById('emailList');

        if (emails.length === 0) {
            emailList.innerHTML = '<div class="no-results">No emails found</div>';
            return;
        }

        emailList.innerHTML = emails.map(email => this.createEmailHTML(email)).join('');

        // Add click handlers
        emailList.querySelectorAll('.email-item').forEach((item, index) => {
            item.addEventListener('click', () => {
                this.showEmailDetail(emails[index]);
            });
        });
    }

    createEmailHTML(email) {
        const time = email.date ? email.date.split('T')[1]?.substring(0, 5) : '';
        const fromDisplay = email.type === 'received'
            ? (email.from?.name || email.from?.email || 'Unknown')
            : `To: ${email.to?.[0] || 'Unknown'}`;

        let badges = '';
        if (email.has_attachments) {
            badges += '<span class="badge attachment">📎 Attachment</span>';
        }
        if (email.importance === 'high') {
            badges += '<span class="badge high-priority">High Priority</span>';
        }
        if (email.categories && email.categories.length > 0) {
            email.categories.forEach(cat => {
                badges += `<span class="badge category">${cat}</span>`;
            });
        }

        const priorityClass = email.importance === 'high' ? 'high-priority' : '';

        return `
            <div class="email-item ${email.type} ${priorityClass}">
                <div class="email-header">
                    <span class="email-from">${fromDisplay}</span>
                    <span class="email-date">${time}</span>
                </div>
                <div class="email-subject">${email.subject || '(no subject)'}</div>
                <div class="email-preview">${email.body_preview || ''}</div>
                ${badges ? `<div class="email-badges">${badges}</div>` : ''}
            </div>
        `;
    }

    showEmailDetail(email) {
        const modal = document.getElementById('emailModal');
        const detail = document.getElementById('emailDetail');

        const attachmentsList = email.attachments && email.attachments.length > 0
            ? `<div class="detail-section">
                <div class="detail-label">Attachments:</div>
                <div class="detail-value">
                    ${email.attachments.map(a => `📎 ${a.filename} (${this.formatBytes(a.size_bytes)})`).join('<br>')}
                </div>
            </div>`
            : '';

        detail.innerHTML = `
            <h2>${email.subject || '(no subject)'}</h2>
            <div class="detail-section">
                <div class="detail-label">From:</div>
                <div class="detail-value">${email.from?.name || email.from?.email || 'Unknown'}</div>
            </div>
            <div class="detail-section">
                <div class="detail-label">To:</div>
                <div class="detail-value">${email.to?.join(', ') || 'Unknown'}</div>
            </div>
            ${email.cc && email.cc.length > 0 ? `
                <div class="detail-section">
                    <div class="detail-label">CC:</div>
                    <div class="detail-value">${email.cc.join(', ')}</div>
                </div>
            ` : ''}
            <div class="detail-section">
                <div class="detail-label">Date:</div>
                <div class="detail-value">${this.formatDateTime(email.date)}</div>
            </div>
            ${attachmentsList}
            <div class="detail-section">
                <div class="detail-label">Message:</div>
                <div class="email-body">${email.body_text || email.body_preview || 'No content'}</div>
            </div>
        `;

        modal.classList.add('active');
    }

    renderProjectsView() {
        const projectsList = document.getElementById('projectsList');

        if (!this.projects || Object.keys(this.projects).length === 0) {
            projectsList.innerHTML = '<div class="no-results">No projects detected</div>';
            return;
        }

        projectsList.innerHTML = Object.entries(this.projects).map(([projectName, threadIds]) => {
            const threadCount = threadIds.length;
            const activeCount = threadIds.filter(tid => {
                const thread = this.threads.find(t => t.thread_id === tid);
                return thread && thread.status === 'active';
            }).length;

            return `
                <div class="project-card">
                    <div class="project-name">${projectName}</div>
                    <div class="project-stats">
                        ${threadCount} thread${threadCount !== 1 ? 's' : ''} •
                        ${activeCount} active
                    </div>
                </div>
            `;
        }).join('');
    }

    renderContactsView() {
        const contactsList = document.getElementById('contactsList');

        // Group emails by contact
        const contacts = {};

        this.emails.forEach(email => {
            const contactEmail = email.type === 'received'
                ? email.from?.email
                : email.to?.[0];

            const contactName = email.type === 'received'
                ? (email.from?.name || contactEmail)
                : contactEmail;

            if (contactEmail) {
                if (!contacts[contactEmail]) {
                    contacts[contactEmail] = {
                        name: contactName,
                        email: contactEmail,
                        received: 0,
                        sent: 0
                    };
                }

                if (email.type === 'received') {
                    contacts[contactEmail].received++;
                } else {
                    contacts[contactEmail].sent++;
                }
            }
        });

        if (Object.keys(contacts).length === 0) {
            contactsList.innerHTML = '<div class="no-results">No contacts found</div>';
            return;
        }

        const sortedContacts = Object.values(contacts).sort((a, b) => {
            const aTotal = a.received + a.sent;
            const bTotal = b.received + b.sent;
            return bTotal - aTotal;
        });

        contactsList.innerHTML = sortedContacts.map(contact => `
            <div class="contact-card">
                <div class="contact-name">${contact.name}</div>
                <div class="contact-stats">
                    ${contact.received} received • ${contact.sent} sent
                </div>
            </div>
        `).join('');
    }

    renderThreadsView(statusFilter = 'all') {
        const threadsList = document.getElementById('threadsList');

        let filtered = [...this.threads];
        if (statusFilter !== 'all') {
            filtered = filtered.filter(t => t.status === statusFilter);
        }

        // Sort by last message date
        filtered.sort((a, b) => {
            return new Date(b.last_message_date) - new Date(a.last_message_date);
        });

        if (filtered.length === 0) {
            threadsList.innerHTML = '<div class="no-results">No threads found</div>';
            return;
        }

        threadsList.innerHTML = filtered.map(thread => {
            const participantsDisplay = thread.participants.slice(0, 3).join(', ') +
                (thread.participants.length > 3 ? ` +${thread.participants.length - 3} more` : '');

            return `
                <div class="thread-item ${thread.status}" data-thread-id="${thread.thread_id}">
                    <div class="thread-topic">${thread.topic || '(no subject)'}</div>
                    <div class="thread-info">
                        <span>${thread.message_count} messages</span>
                        <span>Last: ${this.formatDate(thread.last_message_date)}</span>
                        <span class="badge">${thread.status}</span>
                    </div>
                    <div class="thread-participants">${participantsDisplay}</div>
                </div>
            `;
        }).join('');

        // Add click handlers
        threadsList.querySelectorAll('.thread-item').forEach(item => {
            item.addEventListener('click', () => {
                const threadId = item.dataset.threadId;
                const thread = this.threads.find(t => t.thread_id === threadId);
                if (thread) {
                    this.showThreadDetail(thread);
                }
            });
        });
    }

    showThreadDetail(thread) {
        const modal = document.getElementById('threadModal');
        const detail = document.getElementById('threadDetail');

        const messagesHTML = thread.messages.map(msg => `
            <div class="thread-message ${msg.type}">
                <div class="email-header">
                    <span class="email-from">${msg.from_name || msg.from}</span>
                    <span class="email-date">${this.formatDateTime(msg.date)}</span>
                </div>
                <div class="email-subject">${msg.subject}</div>
                <div class="email-preview">${msg.preview}</div>
                ${msg.has_attachments ? '<span class="badge attachment">📎 Has attachment</span>' : ''}
            </div>
        `).join('');

        detail.innerHTML = `
            <h2>${thread.topic || '(no subject)'}</h2>
            <div class="detail-section">
                <div class="detail-label">Status:</div>
                <div class="detail-value"><span class="badge">${thread.status}</span></div>
            </div>
            <div class="detail-section">
                <div class="detail-label">Messages:</div>
                <div class="detail-value">${thread.message_count}</div>
            </div>
            <div class="detail-section">
                <div class="detail-label">Date Range:</div>
                <div class="detail-value">
                    ${this.formatDate(thread.first_message_date)} to ${this.formatDate(thread.last_message_date)}
                </div>
            </div>
            <div class="detail-section">
                <div class="detail-label">Participants:</div>
                <div class="detail-value">${thread.participants.join(', ')}</div>
            </div>
            ${thread.projects_detected && thread.projects_detected.length > 0 ? `
                <div class="detail-section">
                    <div class="detail-label">Projects:</div>
                    <div class="detail-value">${thread.projects_detected.join(', ')}</div>
                </div>
            ` : ''}
            <div class="detail-section">
                <div class="detail-label">Messages:</div>
                <div class="thread-messages">${messagesHTML}</div>
            </div>
        `;

        modal.classList.add('active');
    }

    performSearch() {
        const resultsDiv = document.getElementById('searchResults');

        if (!this.searchQuery) {
            resultsDiv.innerHTML = '<div class="no-results">Enter a search term...</div>';
            return;
        }

        const results = this.emails.filter(email => {
            const searchableText = `
                ${email.subject || ''}
                ${email.body_text || email.body_preview || ''}
                ${email.from?.name || ''}
                ${email.from?.email || ''}
            `.toLowerCase();

            return searchableText.includes(this.searchQuery);
        });

        if (results.length === 0) {
            resultsDiv.innerHTML = `<div class="no-results">No results found for "${this.searchQuery}"</div>`;
            return;
        }

        resultsDiv.innerHTML = `
            <p><strong>${results.length}</strong> result(s) found for "<strong>${this.searchQuery}</strong>"</p>
            <div class="email-list">
                ${results.map(email => this.createEmailHTML(email)).join('')}
            </div>
        `;

        // Add click handlers
        resultsDiv.querySelectorAll('.email-item').forEach((item, index) => {
            item.addEventListener('click', () => {
                this.showEmailDetail(results[index]);
            });
        });
    }

    closeModals() {
        document.querySelectorAll('.modal').forEach(modal => {
            modal.classList.remove('active');
        });
    }

    formatDate(dateStr) {
        if (!dateStr) return '';
        const date = new Date(dateStr);
        return date.toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric',
            year: 'numeric'
        });
    }

    formatDateTime(dateStr) {
        if (!dateStr) return '';
        const date = new Date(dateStr);
        return date.toLocaleString('en-US', {
            month: 'short',
            day: 'numeric',
            year: 'numeric',
            hour: 'numeric',
            minute: '2-digit'
        });
    }

    formatBytes(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
    }

    showError(message) {
        const emailList = document.getElementById('emailList');
        emailList.innerHTML = `<div class="no-results">${message}</div>`;
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new EmailDashboard();
});
