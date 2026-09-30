/**
 * Crawl Progress Tracker
 *
 * Handles async crawl job progress tracking with real-time polling.
 * Shows progress bar, status and reason for each URL, a grouped summary of
 * what went wrong, and allows cancellation. The panel stays until the admin
 * dismisses it.
 */

class CrawlProgressTracker {
    constructor(jobIds, container, apiUrl) {
        this.jobIds = jobIds;
        this.container = container;
        this.apiUrl = apiUrl;
        this.pollInterval = null;
        this.pollFrequency = 2000; // 2 seconds
        this.stopped = false;   // no more rendering (replaced or dismissed)
        this.completed = false; // onComplete has run
    }

    // Elements are looked up inside this tracker's own root, never by
    // global id: a replaced tracker whose last request is still in flight
    // then writes into its detached root instead of the new panel
    $(id) {
        return this.root ? this.root.querySelector(`[data-part="${id}"]`) : null;
    }

    start() {
        // Clear container
        this.container.innerHTML = '';

        // Show progress UI
        const progressHtml = `
            <div class="crawl-progress mt-2 mb-4 p-4 rounded-lg border border-border bg-background">
                <div class="progress-header flex items-start justify-between gap-4 mb-3">
                    <div>
                        <h3 data-part="progress-title" class="text-lg font-semibold text-gray-900">Crawl Progress</h3>
                        <p class="text-sm text-gray-500 mt-1">
                            <span data-part="progress-count">0 of ${this.jobIds.length} done</span>
                        </p>
                    </div>
                    <div class="flex gap-2 flex-shrink-0">
                        <button data-part="cancel-crawl" class="px-3 py-1.5 text-sm font-medium text-white bg-red-600 hover:bg-red-700 rounded-md transition-colors disabled:opacity-50" type="button">
                            Cancel All
                        </button>
                        <button data-part="dismiss-crawl" class="px-3 py-1.5 text-sm font-medium border border-border rounded-md hover:bg-muted transition-colors" type="button" title="Hide this panel. Crawls keep running in the background.">
                            Dismiss
                        </button>
                    </div>
                </div>

                <div class="progress-bar-container h-2 bg-gray-200 rounded-full overflow-hidden mb-4">
                    <div data-part="progress-bar" class="progress-bar h-full bg-blue-600 transition-all duration-300" style="width: 0%"></div>
                </div>

                <div data-part="progress-summary" class="progress-summary hidden">
                    <!-- Summary shown on completion -->
                </div>

                <div class="progress-items-container max-h-96 overflow-y-auto mt-4">
                    <ul data-part="progress-items" class="list-none p-0 m-0 space-y-2"></ul>
                </div>
            </div>
        `;

        this.container.innerHTML = progressHtml;
        this.root = this.container.firstElementChild;

        this.$('cancel-crawl').onclick = () => this.cancel();
        this.$('dismiss-crawl').onclick = () => this.dismiss();

        this.startPolling();
    }

    startPolling() {
        this.updateProgress(); // Initial update
        this.pollInterval = setInterval(() => this.updateProgress(), this.pollFrequency);
    }

    stop() {
        this.stopped = true;
        clearInterval(this.pollInterval);
        this.pollInterval = null;
    }

    dismiss() {
        this.stop();
        this.container.innerHTML = '';
        if (window.activeCrawlTracker === this) {
            window.activeCrawlTracker = null;
        }
    }

    async updateProgress() {
        try {
            // crawl-status is admin-only now, so the poll has to carry the
            // session token or every tick comes back 403.
            // POST: a long job list (Refresh All) overflows the server's
            // request-line limit as a query string
            const response = await fetch(`${this.apiUrl}/admin/crawl-status`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...(window.Auth ? window.Auth.headers() : {})
                },
                body: JSON.stringify({ job_ids: this.jobIds })
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const data = await response.json();

            if (!data.jobs || !data.summary) {
                console.error('Invalid response:', data);
                return;
            }

            // Replaced or dismissed while this request was in flight, or an
            // earlier poll already rendered the final state
            if (this.stopped || this.completed) return;

            const { total, completed, failed } = data.summary;
            const cancelled = data.summary.cancelled || 0;
            const done = completed + failed + cancelled;

            // Update progress bar
            const progressBar = this.$('progress-bar');
            if (progressBar) {
                progressBar.style.width = `${total ? (done / total) * 100 : 100}%`;
            }

            // Update count. Failures are counted as done (they're finished),
            // but always named, so "done" never reads as "succeeded".
            const progressCount = this.$('progress-count');
            if (progressCount) {
                let text = `${done} of ${total} done · ${completed} succeeded`;
                if (failed > 0) text += ` · ${failed} failed`;
                const retrying = data.jobs.filter(j => j.status === 'pending' && j.error_kind).length;
                if (retrying > 0) text += ` · ${retrying} waiting to retry`;
                progressCount.textContent = text;
            }

            // Update item list
            this.renderJobItems(data.jobs);

            // Check if complete
            if (data.summary.is_complete) {
                this.completed = true;
                clearInterval(this.pollInterval);
                this.pollInterval = null;
                this.onComplete(data.summary, data.jobs);
            }

        } catch (error) {
            console.error('Failed to update progress:', error);
            // Continue polling even on error (network might be temporarily down)
        }
    }

    renderJobItems(jobs) {
        const itemsList = this.$('progress-items');
        if (!itemsList) return;

        const statusIcons = {
            'completed': '✓',
            'failed': '✗',
            'processing': '⏳',
            'pending': '⌛',
            'cancelled': '🚫'
        };

        // Tailwind utilities, not styles.css: that file is linked as plain
        // CSS, so its @apply rules never compile under the Tailwind CDN
        const statusColors = {
            'completed': 'bg-green-50 text-green-800 border-green-200',
            'failed': 'bg-red-50 text-red-800 border-red-200',
            'processing': 'bg-blue-50 text-blue-800 border-blue-200 animate-pulse',
            'pending': 'bg-slate-50 text-slate-700 border-slate-200',
            'cancelled': 'bg-gray-100 text-gray-600 border-gray-300'
        };

        itemsList.innerHTML = jobs.map(job => {
            const savedCopy = CrawlProgressTracker.isSavedCopy(job);
            const icon = savedCopy ? '⚠' : (statusIcons[job.status] || '?');
            const colorClass = savedCopy
                ? 'bg-amber-50 text-amber-900 border-amber-200'
                : (statusColors[job.status] || '');
            const urlDisplay = this.truncateUrl(job.url, 80);

            // Red only for a real failure; a retry that's scheduled, or a
            // doc re-indexed from its saved copy, is shown as a note
            let detailHtml = '';
            if (job.detail) {
                const cls = job.status === 'failed' ? 'text-red-700' : 'text-amber-700';
                detailHtml = `<span class="block text-xs ${cls} mt-0.5">${this.escapeHtml(job.detail)}</span>`;
            }

            return `
                <li class="progress-item flex items-start gap-3 p-2 rounded-md text-sm border ${colorClass}">
                    <span class="item-icon font-bold flex-shrink-0">${icon}</span>
                    <span class="flex-1 min-w-0">
                        <span class="item-url block truncate" title="${this.escapeHtml(job.url)}">${this.escapeHtml(urlDisplay)}</span>
                        ${detailHtml}
                    </span>
                </li>
            `;
        }).join('');
    }

    async cancel() {
        if (!confirm('Cancel all pending crawls?')) return;

        try {
            // Disable cancel button
            const cancelBtn = this.$('cancel-crawl');
            if (cancelBtn) {
                cancelBtn.disabled = true;
                cancelBtn.textContent = 'Cancelling...';
            }

            const response = await fetch(`${this.apiUrl}/admin/crawl-cancel`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...(window.Auth ? window.Auth.headers() : {})
                },
                body: JSON.stringify({ job_ids: this.jobIds })
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            // Render the cancelled rows now; with every job finished this
            // also shows the summary (via onComplete). If this poll fails,
            // the regular polling carries on and completes it.
            await this.updateProgress();

        } catch (error) {
            alert('Failed to cancel: ' + error.message);

            const cancelBtn = this.$('cancel-crawl');
            if (cancelBtn) {
                cancelBtn.disabled = false;
                cancelBtn.textContent = 'Cancel All';
            }
        }
    }

    onComplete(summary, jobs) {
        // Nothing left to cancel; Dismiss stays until the admin closes it
        const cancelBtn = this.$('cancel-crawl');
        if (cancelBtn) cancelBtn.style.display = 'none';

        const failedCount = summary.failed;
        const cancelledCount = summary.cancelled || 0;
        // A web page we couldn't fetch is a problem even if an older copy
        // of it was re-indexed; a pasted doc can only ever be re-indexed
        const savedCopyCount = jobs.filter(CrawlProgressTracker.isSavedCopy).length;
        const hasProblems = failedCount > 0 || savedCopyCount > 0;

        const title = this.$('progress-title');
        if (title) {
            title.textContent = hasProblems ? 'Crawl finished with problems'
                : (cancelledCount > 0 ? 'Crawl cancelled' : 'Crawl finished');
        }

        this.showMessage(
            CrawlProgressTracker.summarize(jobs),
            failedCount > 0 ? 'error' : ((savedCopyCount > 0 || cancelledCount > 0) ? 'warning' : 'success')
        );

        // Refresh the link lists so their badges match. Safe to do right
        // away: the panel lives outside the containers these re-render.
        if (typeof loadESPManagement === 'function') loadESPManagement();
        if (typeof loadGlobalKnowledge === 'function') loadGlobalKnowledge();
    }

    /**
     * One line per outcome, failures grouped by reason, e.g.
     *   ✓ 5 crawled
     *   ✗ 44 — Rate-limited by develop.yotpo.com (HTTP 429) — gave up after 10 rate-limit waits
     *   ✗ 1 — Page not found (HTTP 404) — check the URL
     */
    static isSavedCopy(job) {
        return job.status === 'completed' && job.error_kind === 'backfilled'
            && !String(job.url || '').startsWith('local://');
    }

    static summarize(jobs) {
        const lines = [];
        const completed = jobs.filter(j => j.status === 'completed');
        const pasted = completed.filter(j => j.error_kind === 'backfilled' && !CrawlProgressTracker.isSavedCopy(j));
        const fromCopy = completed.filter(CrawlProgressTracker.isSavedCopy);
        const crawled = completed.length - pasted.length - fromCopy.length;

        if (crawled > 0) lines.push(`✓ ${crawled} crawled`);
        if (pasted.length > 0) lines.push(`✓ ${pasted.length} pasted doc(s) re-indexed`);
        if (fromCopy.length > 0) lines.push(`⚠ ${fromCopy.length} couldn't be crawled — re-indexed from the copy we already had`);

        const reasons = new Map();
        jobs.filter(j => j.status === 'failed').forEach(j => {
            const reason = j.detail || j.error_message || 'Unknown error';
            reasons.set(reason, (reasons.get(reason) || 0) + 1);
        });
        [...reasons.entries()]
            .sort((a, b) => b[1] - a[1])
            .forEach(([reason, count]) => lines.push(`✗ ${count} — ${reason}`));

        const cancelled = jobs.filter(j => j.status === 'cancelled').length;
        if (cancelled > 0) lines.push(`🚫 ${cancelled} cancelled`);

        if (reasons.size > 0 || fromCopy.length > 0) {
            lines.push('', 'Those links stay selected in the list below — fix or wait, then run Crawl Selected again.');
        }
        return lines.join('\n');
    }

    showMessage(message, type = 'info') {
        const summaryDiv = this.$('progress-summary');
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

        summaryDiv.className = `progress-summary border ${bgColors[type]} ${textColors[type]} p-4 rounded-lg mt-2`;
        summaryDiv.innerHTML = `<pre class="whitespace-pre-wrap text-sm font-medium">${this.escapeHtml(message)}</pre>`;
        summaryDiv.classList.remove('hidden');
    }

    // Helper functions
    truncateUrl(url, maxLength) {
        if (url.length <= maxLength) return url;

        // Try to keep protocol and domain visible
        let urlObj;
        try {
            urlObj = new URL(url);
        } catch (e) {
            return url.slice(0, maxLength - 3) + '...';
        }
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
        div.textContent = text == null ? '' : String(text);
        // textContent escaping leaves quotes alone; this is also used in
        // title="…" attributes
        return div.innerHTML.replace(/"/g, '&quot;').replace(/'/g, '&#39;');
    }
}

// Export for use in app.js
if (typeof module !== 'undefined' && module.exports) {
    module.exports = CrawlProgressTracker;
}
