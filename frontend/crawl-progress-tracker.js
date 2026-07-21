/**
 * Crawl Progress Tracker
 *
 * Handles async crawl job progress tracking with real-time polling.
 * Shows progress bar, status for each URL, and allows cancellation.
 */

class CrawlProgressTracker {
    constructor(jobIds, container, apiUrl) {
        this.jobIds = jobIds;
        this.container = container;
        this.apiUrl = apiUrl;
        this.pollInterval = null;
        this.pollFrequency = 2000; // 2 seconds
    }

    start() {
        // Clear container
        this.container.innerHTML = '';

        // Show progress UI
        const progressHtml = `
            <div class="crawl-progress mt-6 mb-4">
                <div class="progress-header">
                    <div>
                        <h3 class="text-lg font-semibold text-gray-900">Crawl Progress</h3>
                        <p class="text-sm text-gray-500 mt-1">
                            <span id="progress-count">0/${this.jobIds.length}</span> URLs completed
                        </p>
                    </div>
                    <button id="cancel-crawl" class="btn-danger-sm" type="button">
                        Cancel All
                    </button>
                </div>

                <div class="progress-bar-container">
                    <div id="progress-bar" class="progress-bar" style="width: 0%"></div>
                </div>

                <div class="progress-items-container">
                    <ul id="progress-items"></ul>
                </div>

                <div id="progress-summary" class="progress-summary hidden">
                    <!-- Summary shown on completion -->
                </div>
            </div>
        `;

        this.container.innerHTML = progressHtml;

        // Add cancel handler
        document.getElementById('cancel-crawl').onclick = () => this.cancel();

        // Start polling
        this.updateProgress(); // Initial update
        this.pollInterval = setInterval(() => this.updateProgress(), this.pollFrequency);
    }

    async updateProgress() {
        try {
            const response = await fetch(
                `${this.apiUrl}/admin/crawl-status?job_ids=${this.jobIds.join(',')}`,
                { method: 'GET' }
            );

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const data = await response.json();

            if (!data.jobs || !data.summary) {
                console.error('Invalid response:', data);
                return;
            }

            // Update progress bar
            const progress = ((data.summary.completed + data.summary.failed + data.summary.cancelled) / data.summary.total) * 100;
            const progressBar = document.getElementById('progress-bar');
            if (progressBar) {
                progressBar.style.width = `${progress}%`;
            }

            // Update count
            const progressCount = document.getElementById('progress-count');
            if (progressCount) {
                const completed = data.summary.completed + data.summary.failed + data.summary.cancelled;
                progressCount.textContent = `${completed}/${data.summary.total}`;
            }

            // Update item list
            this.renderJobItems(data.jobs);

            // Check if complete
            if (data.summary.is_complete) {
                clearInterval(this.pollInterval);
                this.onComplete(data.summary, data.jobs);
            }

        } catch (error) {
            console.error('Failed to update progress:', error);
            // Continue polling even on error (network might be temporarily down)
        }
    }

    renderJobItems(jobs) {
        const itemsList = document.getElementById('progress-items');
        if (!itemsList) return;

        const statusIcons = {
            'completed': '✓',
            'failed': '✗',
            'processing': '⏳',
            'pending': '⌛',
            'cancelled': '🚫'
        };

        const statusColors = {
            'completed': 'status-completed',
            'failed': 'status-failed',
            'processing': 'status-processing',
            'pending': 'status-pending',
            'cancelled': 'status-cancelled'
        };

        itemsList.innerHTML = jobs.map(job => {
            const icon = statusIcons[job.status] || '?';
            const colorClass = statusColors[job.status] || '';
            const urlDisplay = this.truncateUrl(job.url, 80);

            let errorHtml = '';
            if (job.error_message) {
                errorHtml = `<span class="item-error">${this.escapeHtml(job.error_message)}</span>`;
            }

            return `
                <li class="progress-item ${colorClass}">
                    <span class="item-icon">${icon}</span>
                    <span class="item-url" title="${this.escapeHtml(job.url)}">${this.escapeHtml(urlDisplay)}</span>
                    ${errorHtml}
                </li>
            `;
        }).join('');
    }

    async cancel() {
        if (!confirm('Cancel all pending crawls?')) return;

        try {
            // Disable cancel button
            const cancelBtn = document.getElementById('cancel-crawl');
            if (cancelBtn) {
                cancelBtn.disabled = true;
                cancelBtn.textContent = 'Cancelling...';
            }

            const response = await fetch(`${this.apiUrl}/admin/crawl-cancel`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ job_ids: this.jobIds })
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            clearInterval(this.pollInterval);

            // Do one final update to show cancelled status
            await this.updateProgress();

            // Show cancelled message
            this.showMessage('Crawl cancelled by user', 'warning');

        } catch (error) {
            alert('Failed to cancel: ' + error.message);

            // Re-enable button
            const cancelBtn = document.getElementById('cancel-crawl');
            if (cancelBtn) {
                cancelBtn.disabled = false;
                cancelBtn.textContent = 'Cancel All';
            }
        }
    }

    onComplete(summary, jobs) {
        // Hide cancel button
        const cancelBtn = document.getElementById('cancel-crawl');
        if (cancelBtn) {
            cancelBtn.style.display = 'none';
        }

        // Show completion summary
        const successCount = summary.completed;
        const failedCount = summary.failed;
        const cancelledCount = summary.cancelled || 0;

        let message = `Crawling complete!\n`;
        if (successCount > 0) message += `✓ ${successCount} succeeded\n`;
        if (failedCount > 0) message += `✗ ${failedCount} failed\n`;
        if (cancelledCount > 0) message += `🚫 ${cancelledCount} cancelled`;

        // Show inline message
        this.showMessage(message.trim(), failedCount > 0 ? 'warning' : 'success');

        // Call global refresh function if it exists
        if (typeof loadESPManagement === 'function') {
            // Small delay to let user see the completion message
            setTimeout(() => {
                loadESPManagement();
            }, 1500);
        }
    }

    showMessage(message, type = 'info') {
        const summaryDiv = document.getElementById('progress-summary');
        if (!summaryDiv) return;

        const bgColors = {
            'success': 'bg-green-50 border-green-200',
            'warning': 'bg-yellow-50 border-yellow-200',
            'error': 'bg-red-50 border-red-200',
            'info': 'bg-blue-50 border-blue-200'
        };

        const textColors = {
            'success': 'text-green-800',
            'warning': 'text-yellow-800',
            'error': 'text-red-800',
            'info': 'text-blue-800'
        };

        summaryDiv.className = `progress-summary border ${bgColors[type]} ${textColors[type]} p-4 rounded-lg mt-4`;
        summaryDiv.innerHTML = `<pre class="whitespace-pre-wrap text-sm font-medium">${this.escapeHtml(message)}</pre>`;
        summaryDiv.classList.remove('hidden');
    }

    // Helper functions
    truncateUrl(url, maxLength) {
        if (url.length <= maxLength) return url;

        // Try to keep protocol and domain visible
        const urlObj = new URL(url);
        const domain = urlObj.hostname;
        const path = urlObj.pathname;

        if (domain.length + 10 < maxLength) {
            const availableForPath = maxLength - domain.length - 10;
            const truncatedPath = path.length > availableForPath
                ? '...' + path.slice(-(availableForPath - 3))
                : path;
            return urlObj.protocol + '//' + domain + truncatedPath;
        }

        // Fallback: simple truncation
        return url.slice(0, maxLength - 3) + '...';
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Export for use in app.js
if (typeof module !== 'undefined' && module.exports) {
    module.exports = CrawlProgressTracker;
}
