// Admin: the Integrations and Proposals tabs (ALL_INTEGRATIONS_ROADMAP.md C1.4,
// design/integrations-redesign.html, Admin screen).
//
// Replaces ESP Management, which fetched every integration's links one
// request at a time. The list is one request (GET /api/admin/integrations),
// and an integration's documents load when it is opened.
//
// Built on app.js, loaded before this file: API_URL, adminHeaders,
// escapeHtml/escapeAttr, the crawl-state styles, the product picker and the
// link actions (addLink, crawlAllSelected, deleteAllSelected, openPasteModal),
// which act on the `.link-checkbox` rows rendered here. Every string from the
// database or the catalog goes through escapeHtml/escapeAttr (I7).

(function () {
    const PLATFORM_TYPES = ['messaging', 'storefront', 'service', 'data', 'content'];
    const TYPE_NAMES = { messaging: 'Messaging', storefront: 'Storefront', service: 'Service', data: 'Data', content: 'Content' };
    const STATUS_NAMES = { active: 'Active', listed: 'Listed', archived: 'Archived' };
    const TIER_NAMES = { basic: 'Basic', listed: 'Listed' };
    const PRODUCT_NAMES = { loyalty: 'Loyalty', reviews: 'Reviews' };
    const SOURCE_KIND = { yotpo_support: 'Yotpo guide', yotpo_developer: 'Yotpo developer docs', partner: 'Partner page', pasted: 'Pasted' };
    const SOURCE_NAMES = { catalog: 'Catalog', sitemap: 'Sitemap', manual: 'Manual', mechanics: 'Partner article' };
    const FLAG_NAMES = {
        unlabelled: 'Unlabelled documents',
        failed: 'Failed crawls',
        proposals: 'Open proposals',
        misses: 'Missing pages',
        mixed_types: 'Type to check'
    };
    const NEEDS_PERSON = {
        blocked: 'The help centre blocks automated reading',
        nothing_found: 'The model accepted none of the articles it read',
        no_help_centre: 'No help centre was found'
    };
    // States shown in the crawl strip, in this order, when non-zero
    const STRIP_STATES = ['crawling', 'queued', 'waiting', 'retrying', 'failed', 'saved_copy', 'pending'];
    const SUMMARY_POLL_MS = 5000;
    const MISS_LIMIT = 3;

    const inputCls = 'px-3 py-2 border border-input bg-background rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-ring';
    const card = 'bg-muted/50 rounded-lg p-4 border border-border';
    const th = 'py-2 px-3 font-medium text-muted-foreground';
    const btnPrimary = 'px-4 py-2 bg-primary text-primary-foreground rounded-lg font-medium text-sm hover:bg-primary/90 transition-colors whitespace-nowrap';
    const btnOutline = 'px-3 py-1 border border-input bg-background text-foreground rounded-lg font-medium text-sm hover:bg-muted transition-colors whitespace-nowrap disabled:opacity-50 disabled:cursor-not-allowed';

    const S = {
        filters: { q: '', category: '', type: '', status: '', tier: '', flag: '' },
        page: 1,
        open: null,            // the integration whose page is shown, or null for the list
        docPage: 1,
        facets: null,
        crawlDetails: false,
        summaryTimer: null,
        hadActiveJobs: false,
        listTicket: 0,
        prop: { state: 'open', source: '', esp: '', page: 1, sel: new Set(), labels: {}, touched: new Set(), rows: [], integrations: {} }
    };

    const $ = (id) => document.getElementById(id);
    const esc = escapeHtml;
    const attr = escapeAttr;

    function isOwner() {
        return window.adminRole === 'owner';
    }

    async function getJSON(path) {
        const response = await fetch(`${API_URL}${path}`, { headers: adminHeaders() });
        let data = {};
        try { data = await response.json(); } catch (e) { /* not JSON */ }
        if (!response.ok) throw new Error(data.error || `HTTP ${response.status}`);
        return data;
    }

    async function sendJSON(method, path, body) {
        const response = await fetch(`${API_URL}${path}`, { method, headers: adminHeaders(), body: JSON.stringify(body) });
        let data = {};
        try { data = await response.json(); } catch (e) { /* not JSON */ }
        if (!response.ok) throw new Error(data.error || `HTTP ${response.status}`);
        return data;
    }

    function qs(params) {
        return Object.entries(params).filter(([, v]) => v !== '' && v != null)
            .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(v)}`).join('&');
    }

    function stateBadge(state) {
        return `<span class="text-xs font-medium px-2 py-0.5 rounded ${crawlStateStyle(state).badge} uppercase tracking-wide whitespace-nowrap">${esc(statusLabel(state))}</span>`;
    }

    function statusPill(status) {
        const tone = status === 'active' ? 'bg-green-100 text-green-800' : 'bg-slate-100 text-slate-700';
        return `<span class="text-xs font-medium px-2 py-0.5 rounded ${tone}">${esc(STATUS_NAMES[status] || status)}</span>`;
    }

    function productsText(products) {
        return (products || []).map(p => PRODUCT_NAMES[p] || p).join(' · ') || '—';
    }

    function pager(total, page, perPage, kind) {
        if (total <= perPage) {
            return `<div class="mt-3 text-sm text-muted-foreground">${total ? `1–${total} of ${total}` : ''}</div>`;
        }
        const from = (page - 1) * perPage + 1;
        const to = Math.min(page * perPage, total);
        return `
            <div class="flex items-center justify-between mt-3 text-sm text-muted-foreground">
                <span>${from}–${to} of ${total}</span>
                <div class="flex gap-2">
                    <button type="button" class="${btnOutline}" data-page="${kind}" data-to="${page - 1}" ${page <= 1 ? 'disabled' : ''}>Previous</button>
                    <button type="button" class="${btnOutline}" data-page="${kind}" data-to="${page + 1}" ${to >= total ? 'disabled' : ''}>Next</button>
                </div>
            </div>`;
    }

    function setProposalsCount(n) {
        const el = $('proposalsTabCount');
        if (el) el.textContent = n ? `(${n})` : '';
    }

    // ==================== Crawl summary strip ====================

    async function loadCrawlSummary() {
        const box = $('crawlSummary');
        if (!box) return;
        let data;
        try {
            data = await getJSON('/admin/crawl-summary');
        } catch (error) {
            box.innerHTML = `<div class="${card} mb-6 text-sm text-red-700">Could not load the crawl summary: ${esc(error.message)}</div>`;
            return;
        }
        const counts = STRIP_STATES.filter(s => data.states[s]);
        box.innerHTML = `
            <div class="${card} mb-6">
                <div class="flex flex-wrap items-center gap-x-4 gap-y-2">
                    <span class="text-sm font-medium text-card-foreground">Crawls</span>
                    ${counts.length ? counts.map(s => `<span class="inline-flex items-center gap-1.5 text-sm">${stateBadge(s)}<span class="tabular-nums text-card-foreground">${data.states[s]}</span></span>`).join('')
                        : '<span class="text-sm text-muted-foreground">Nothing queued or failed</span>'}
                    <span class="text-sm text-muted-foreground">· ${data.states.crawled || 0} crawled</span>
                    <button type="button" class="ml-auto text-sm text-muted-foreground hover:text-foreground" data-crawl-details aria-expanded="${S.crawlDetails}">${S.crawlDetails ? 'Hide details' : 'Details'}</button>
                </div>
                ${S.crawlDetails ? crawlDetailsHTML(data) : ''}
            </div>`;
        box.querySelector('[data-crawl-details]').addEventListener('click', () => {
            S.crawlDetails = !S.crawlDetails;
            loadCrawlSummary();
        });
        watch(data.active_jobs > 0);
    }

    function crawlDetailsHTML(data) {
        const hosts = data.hosts.length ? data.hosts.map(h => `
            <tr class="border-b border-border last:border-0">
                <td class="py-2 font-mono text-xs">${esc(h.host)}</td>
                <td class="py-2 px-3 text-right tabular-nums">${h.queued}</td>
                <td class="py-2 px-3 text-right tabular-nums ${h.failed ? 'text-red-700 font-medium' : ''}">${h.failed}</td>
            </tr>`).join('') : `<tr><td colspan="3" class="py-3 text-sm text-muted-foreground">No site has queued or failed crawls.</td></tr>`;
        const jobs = !data.queue
            ? '<p class="text-sm text-muted-foreground">This server crawls when you click Crawl Selected; there is no background queue.</p>'
            : data.jobs.length ? `
                <ul class="space-y-2">
                    ${data.jobs.map(j => `
                        <li class="flex items-center gap-3 p-2 rounded-md text-sm bg-background border border-border">
                            ${stateBadge(j.state)}
                            <span class="flex-1 min-w-0">
                                <span class="block truncate" title="${attr(j.url)}">${esc(j.url)}</span>
                                <span class="block text-xs text-muted-foreground truncate">${esc(j.display_name)}${j.detail ? ` · ${esc(j.detail)}` : ''}</span>
                            </span>
                        </li>`).join('')}
                </ul>
                ${data.active_jobs > data.jobs.length ? `<p class="text-xs text-muted-foreground mt-2">and ${data.active_jobs - data.jobs.length} more</p>` : ''}`
            : '<p class="text-sm text-muted-foreground">No crawls running or waiting.</p>';
        return `
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-4 mt-4">
                <table class="w-full text-sm self-start">
                    <thead><tr class="border-b border-border"><th class="text-left ${th} !px-0">Site</th><th class="text-right ${th}">Queued</th><th class="text-right ${th}">Failed</th></tr></thead>
                    <tbody>${hosts}</tbody>
                </table>
                <div>${jobs}</div>
            </div>`;
    }

    // Poll the summary while crawls are running and the tab is on screen;
    // when the last one finishes, refresh the view once so its rows show it
    function watch(active) {
        clearTimeout(S.summaryTimer);
        S.summaryTimer = null;
        const visible = !$('espManagementTab')?.classList.contains('hidden')
            && !$('adminModal')?.classList.contains('hidden');
        if (active && visible) {
            S.hadActiveJobs = true;
            S.summaryTimer = setTimeout(loadCrawlSummary, SUMMARY_POLL_MS);
        } else if (S.hadActiveJobs && !active) {
            S.hadActiveJobs = false;
            refreshView();
        }
    }

    // ==================== Integrations list ====================

    function listShellHTML() {
        const f = S.filters;
        const facets = S.facets || { categories: [], flags: {} };
        const sel = (key, label, options) => `
            <select class="${inputCls}" data-filter="${key}" aria-label="${attr(label)}">
                <option value="">${esc(label)}</option>
                ${options.map(([v, t]) => `<option value="${attr(v)}" ${f[key] === v ? 'selected' : ''}>${esc(t)}</option>`).join('')}
            </select>`;
        const quick = (k) => `
            <label class="inline-flex items-center gap-2 text-sm text-card-foreground cursor-pointer">
                <input type="checkbox" class="w-4 h-4 rounded border-input" data-flag="${k}" ${f.flag === k ? 'checked' : ''}>
                ${esc(FLAG_NAMES[k])} <span class="text-muted-foreground">(${facets.flags[k] || 0})</span>
            </label>`;
        return `
            <div class="flex flex-wrap gap-2 mb-3">
                <input id="intSearch" value="${attr(f.q)}" placeholder="Search integrations" class="flex-1 min-w-[12rem] ${inputCls}" aria-label="Search integrations">
                ${sel('category', 'All categories', facets.categories.map(c => [c.slug, `${c.name} (${c.count})`]))}
                ${sel('type', 'All platform types', PLATFORM_TYPES.map(t => [t, TYPE_NAMES[t]]))}
                ${sel('status', 'Any status', Object.entries(STATUS_NAMES))}
                ${sel('tier', 'Any coverage', Object.entries(TIER_NAMES))}
            </div>
            <div class="flex flex-wrap gap-x-5 gap-y-2 mb-4">${Object.keys(FLAG_NAMES).map(quick).join('')}</div>
            <div id="intTable"></div>`;
    }

    function attentionHTML(i) {
        const parts = [
            i.documents.unlabelled && `<span class="text-amber-800">${i.documents.unlabelled} unlabelled</span>`,
            i.failed && `<span class="text-red-700">${i.failed} failed</span>`,
            i.misses && `<span class="text-red-700">${i.misses} missing</span>`,
            i.open_proposals && `<span class="text-card-foreground">${i.open_proposals} proposal${i.open_proposals === 1 ? '' : 's'}</span>`,
            i.type_choices.length && `<span class="text-amber-800" title="Its categories default to ${attr(i.type_choices.map(t => TYPE_NAMES[t]).join(' and '))}">type to check</span>`
        ].filter(Boolean);
        return parts.join('<span class="text-muted-foreground"> · </span>');
    }

    function tableHTML(data) {
        const rows = data.integrations.map(i => `
            <tr class="border-b border-border last:border-0 hover:bg-muted/30 cursor-pointer" data-open-int="${attr(i.name)}" tabindex="0">
                <td class="py-2.5 px-3"><div class="font-medium text-card-foreground">${esc(i.display_name)}</div><div class="text-xs text-muted-foreground truncate max-w-[15rem]">${esc(i.category_names.join(' · '))}</div></td>
                <td class="py-2.5 px-3 text-muted-foreground whitespace-nowrap">${esc(productsText(i.products))}</td>
                <td class="py-2.5 px-3 text-muted-foreground">${esc(TYPE_NAMES[i.platform_type] || '—')}</td>
                <td class="py-2.5 px-3">${statusPill(i.status)}</td>
                <td class="py-2.5 px-3 text-muted-foreground whitespace-nowrap">${esc(TIER_NAMES[i.tier])}</td>
                <td class="py-2.5 px-3 text-right tabular-nums">${i.documents.total}</td>
                <td class="py-2.5 px-3 text-xs">${attentionHTML(i)}</td>
            </tr>`).join('');
        return `
            <div class="bg-background border border-border rounded-lg overflow-x-auto">
                <table class="w-full text-sm min-w-[720px]">
                    <thead><tr class="border-b border-border bg-muted">
                        <th class="text-left ${th}">Integration</th><th class="text-left ${th}">Products</th><th class="text-left ${th}">Platform type</th>
                        <th class="text-left ${th}">Status</th><th class="text-left ${th}">Coverage</th><th class="text-right ${th}">Documents</th><th class="text-left ${th}">Needs attention</th>
                    </tr></thead>
                    <tbody>${rows || '<tr><td colspan="7" class="text-center py-8 text-muted-foreground">No integrations match</td></tr>'}</tbody>
                </table>
            </div>
            ${pager(data.total, data.page, data.per_page, 'list')}`;
    }

    async function loadList({ rebuildShell = false } = {}) {
        const box = $('espManagement');
        if (!box) return;
        const ticket = ++S.listTicket;
        let data;
        try {
            data = await getJSON(`/admin/integrations?${qs({ ...S.filters, page: S.page })}`);
        } catch (error) {
            if (ticket === S.listTicket && !S.open) {
                box.innerHTML = `<div class="text-sm text-red-700">Could not load the integrations: ${esc(error.message)}</div>`;
            }
            return;
        }
        if (ticket !== S.listTicket || S.open) return;   // a newer request, or an integration was opened
        S.facets = data.facets;
        setProposalsCount(data.facets.open_proposals);
        // The controls are drawn once, so typing in the search box keeps its focus
        if (rebuildShell || !$('intTable')) {
            box.innerHTML = listShellHTML();
            wireListShell(box);
        } else {
            box.querySelectorAll('[data-flag]').forEach(cb => {
                const n = data.facets.flags[cb.dataset.flag] || 0;
                const count = cb.parentElement.querySelector('span');
                if (count) count.textContent = `(${n})`;
            });
        }
        const table = $('intTable');
        table.innerHTML = tableHTML(data);
        table.querySelectorAll('[data-open-int]').forEach(row => {
            row.addEventListener('click', () => openIntegration(row.dataset.openInt));
            row.addEventListener('keydown', (e) => { if (e.key === 'Enter') openIntegration(row.dataset.openInt); });
        });
        table.querySelectorAll('[data-page="list"]').forEach(b => b.addEventListener('click', () => {
            S.page = Number(b.dataset.to);
            loadList();
        }));
    }

    function wireListShell(box) {
        let timer = null;
        $('intSearch').addEventListener('input', (e) => {
            clearTimeout(timer);
            timer = setTimeout(() => { S.filters.q = e.target.value.trim(); S.page = 1; loadList(); }, 250);
        });
        box.querySelectorAll('[data-filter]').forEach(s => s.addEventListener('change', () => {
            S.filters[s.dataset.filter] = s.value;
            S.page = 1;
            loadList();
        }));
        // One quick filter at a time, like the prototype
        box.querySelectorAll('[data-flag]').forEach(cb => cb.addEventListener('change', () => {
            S.filters.flag = cb.checked ? cb.dataset.flag : '';
            box.querySelectorAll('[data-flag]').forEach(o => { if (o !== cb) o.checked = false; });
            S.page = 1;
            loadList();
        }));
    }

    // ==================== One integration ====================

    function setListOnlySections(visible) {
        // Global knowledge, Create, Refresh All and the debug button belong to
        // the list. Hidden on an integration's page; app.js's bulk actions
        // skip checkboxes inside hidden sections, so a pre-checked global link
        // can't be crawled or deleted from there unseen.
        $('integrationsListOnly')?.classList.toggle('hidden', !visible);
        $('manageIntegrationsTitle')?.classList.toggle('hidden', !visible);
    }

    function openIntegration(name) {
        S.open = name;
        S.docPage = 1;
        setListOnlySections(false);
        loadDetail();
        $('espManagementTab')?.closest('.overflow-y-auto')?.scrollTo({ top: 0 });
    }

    function backToList() {
        S.open = null;
        setListOnlySections(true);
        loadList({ rebuildShell: true });
        if (typeof updateGlobalBulkActions === 'function') updateGlobalBulkActions();
    }

    function docRowHTML(name, link, readOnly = false) {
        const style = crawlStateStyle(link.status);
        const meta = [SOURCE_KIND[link.source_kind], (link.supported_plans || []).join(', '), (link.supported_platforms || []).join(', ')]
            .filter(Boolean).join(' · ');
        const missing = link.consecutive_misses >= MISS_LIMIT
            ? `<span class="block text-xs text-red-700">Missing ${link.consecutive_misses} times — retire or replace it</span>` : '';
        return `
            <div class="flex items-center gap-2 p-2 bg-background rounded-lg border ${style.row || 'border-border'} hover:border-primary transition-colors">
                ${readOnly ? '' : `<input type="checkbox" class="link-checkbox w-4 h-4 rounded border-input cursor-pointer shrink-0" data-esp="${attr(name)}" value="${attr(link.url)}" ${(isCrawlCandidate(link) || link.needs_backfill) ? 'checked' : ''} aria-label="Select ${attr(link.url)}">`}
                ${stateBadge(link.status)}
                ${link.needs_backfill ? '<span class="text-xs font-medium px-2 py-0.5 rounded bg-amber-100 text-amber-800 uppercase tracking-wide" title="No content backup in the database — run Crawl Selected once to store a copy (re-crawls, or backs up the saved copy if the site blocks crawling)">no backup</span>' : ''}
                <div class="flex-1 min-w-0">
                    <a href="${attr(link.url)}" target="_blank" rel="noopener" class="block text-sm text-foreground hover:text-primary hover:underline truncate">${esc(link.title || link.url)}</a>
                    <span class="block text-xs text-muted-foreground truncate">${esc([link.title ? link.url : '', meta].filter(Boolean).join(' · '))}</span>
                    ${linkDetailHTML(link)}
                    ${missing}
                </div>
                ${readOnly ? '' : productPickerHTML(name, link)}
                ${!readOnly && isCrawlCandidate(link) ? `<button type="button" class="paste-btn px-3 py-1 bg-primary/10 text-primary border border-primary rounded text-xs font-medium hover:bg-primary hover:text-primary-foreground transition-colors whitespace-nowrap" data-url="${attr(link.url)}" title="Paste content manually">📋 Paste Content</button>` : ''}
            </div>`;
    }

    function factsHTML(i) {
        const owner = isOwner();
        const statusButtons = ['active', 'listed', 'archived'].map(s => `
            <button type="button" role="radio" aria-checked="${s === i.status}" data-set-status="${s}"
                class="px-2.5 py-1 text-xs font-medium rounded-md ${s === i.status ? 'bg-background shadow-sm text-foreground' : 'text-muted-foreground hover:text-foreground'} disabled:cursor-not-allowed"
                ${owner ? '' : 'disabled'}>${STATUS_NAMES[s]}</button>`).join('');
        const typeNote = i.type_choices.length
            ? `<div class="mt-2 rounded-md border border-amber-300 bg-amber-50 px-2 py-1.5 text-[11px] text-amber-900">
                   Its categories default to ${esc(i.type_choices.map(t => TYPE_NAMES[t]).join(' and '))}. Pick the type that fits, or keep this one.
                   <button type="button" class="ml-1 underline font-medium" data-keep-type>Keep ${esc(TYPE_NAMES[i.platform_type] || 'it')}</button>
               </div>`
            : i.type_set_by ? `<p class="text-[11px] text-muted-foreground mt-1">Chosen by ${esc(i.type_set_by)}.</p>` : '';
        return `
            <div class="${card} space-y-4">
                <h4 class="text-sm font-semibold text-card-foreground">Catalog facts</h4>
                <div>
                    <div class="text-xs text-muted-foreground mb-1.5">Status ${owner ? '' : '<span class="opacity-70">(owner only)</span>'}</div>
                    <div class="inline-flex gap-1 p-1 rounded-lg bg-muted border border-border" role="radiogroup" aria-label="Status">${statusButtons}</div>
                    <p class="text-[11px] text-muted-foreground mt-1">Active is in chat. Listed is not in chat yet. Only Messaging integrations can be active for now.</p>
                </div>
                <div>
                    <label class="block text-xs text-muted-foreground mb-1.5" for="intType">Platform type</label>
                    <select id="intType" class="w-full ${inputCls}">
                        ${i.platform_type ? '' : '<option value="" selected disabled>Not set</option>'}
                        ${PLATFORM_TYPES.map(t => `<option value="${t}" ${i.platform_type === t ? 'selected' : ''}>${TYPE_NAMES[t]}</option>`).join('')}
                    </select>
                    <p class="text-[11px] text-muted-foreground mt-1">Chooses the system prompt. The catalog import set it from the categories.</p>
                    ${typeNote}
                </div>
                <div>
                    <div class="text-xs text-muted-foreground mb-1.5">Products</div>
                    <div class="flex gap-4 text-sm">${['loyalty', 'reviews'].map(p => `<label class="flex items-center gap-2"><input type="checkbox" class="w-4 h-4 rounded" data-product="${p}" ${i.products.includes(p) ? 'checked' : ''}>${PRODUCT_NAMES[p]}</label>`).join('')}</div>
                </div>
                <div>
                    <div class="text-xs text-muted-foreground mb-1.5">Categories</div>
                    <div class="flex flex-wrap gap-1">${i.category_names.length ? i.category_names.map(c => `<span class="text-xs px-2 py-0.5 rounded-full bg-background border border-border">${esc(c)}</span>`).join('') : '<span class="text-xs text-muted-foreground">None</span>'}</div>
                </div>
                <div>
                    <div class="text-xs text-muted-foreground mb-1.5">Catalog cards</div>
                    ${i.catalog_cards.length ? i.catalog_cards.map(c => `<a href="${attr(c.url)}" target="_blank" rel="noopener" class="block font-mono text-xs text-foreground hover:underline py-0.5">${esc(c.slug)} ↗</a>`).join('') : '<span class="text-xs text-muted-foreground">Not in the catalog</span>'}
                </div>
            </div>`;
    }

    function coverageHTML(i) {
        const m = i.mechanics;
        const functions = m && m.functions && m.functions.length
            ? `<p class="text-xs text-muted-foreground mt-3"><span class="font-medium text-card-foreground">Partner functions the import found:</span> ${esc(m.functions.map(f => f.name).join(', '))}</p>` : '';
        const problem = m && m.problem ? `<p class="text-xs text-amber-800 mt-2">${esc(m.problem)}</p>` : '';
        return `
            <div class="${card}">
                <h4 class="text-sm font-semibold text-card-foreground mb-2">Coverage: ${esc(TIER_NAMES[i.tier])}</h4>
                <p class="text-xs text-muted-foreground">${i.platform_type === 'messaging'
                    ? 'Basic needs a labelled, indexed Yotpo guide for a product the catalog lists, and a Shared document on the platform\'s own mechanics.'
                    : 'Basic needs a labelled, indexed Yotpo guide for a product the catalog lists.'}</p>
                ${functions}${problem}
                ${i.open_proposals ? `<button type="button" class="mt-3 text-sm font-medium text-primary hover:underline" data-review-proposals>Review ${i.open_proposals} open proposal${i.open_proposals === 1 ? '' : 's'} →</button>` : ''}
            </div>`;
    }

    async function loadDetail() {
        const box = $('espManagement');
        const name = S.open;
        if (!box || !name) return;
        let info, docs;
        try {
            [info, docs] = await Promise.all([
                getJSON(`/admin/integrations/${encodeURIComponent(name)}`),
                getJSON(`/admin/integrations/${encodeURIComponent(name)}/documents?page=${S.docPage}`)
            ]);
        } catch (error) {
            box.innerHTML = `<button type="button" class="text-sm text-muted-foreground hover:text-foreground mb-4" data-back>← All integrations</button>
                <div class="text-sm text-red-700">Could not load ${esc(name)}: ${esc(error.message)}</div>`;
            box.querySelector('[data-back]').addEventListener('click', backToList);
            return;
        }
        if (S.open !== name) return;
        const i = info.integration;
        // An archived integration's rows are shown, but not selectable: the
        // document routes don't find archived integrations
        const rows = docs.documents.map(link => docRowHTML(name, link, i.status === 'archived')).join('');
        box.innerHTML = `
            <button type="button" class="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground mb-4" data-back>← All integrations</button>
            <h4 class="text-base font-semibold text-card-foreground mb-4 flex flex-wrap items-center gap-2">
                <span>${esc(i.display_name)} (${docs.total} document${docs.total === 1 ? '' : 's'})</span>
                <span class="unlabelled-count"></span>
                <button type="button" class="text-muted-foreground hover:text-primary transition-colors" data-rename title="Rename ${attr(i.display_name)}" aria-label="Rename ${attr(i.display_name)}">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20h9"></path><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4Z"></path></svg>
                </button>
                <span class="text-xs font-normal text-muted-foreground font-mono">${esc(i.name)}</span>
            </h4>
            <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div class="lg:col-span-2 min-w-0">
                    <div class="${card}">
                        <div class="space-y-2 mb-4" id="links-${attr(name)}">
                            ${rows || `<div class="text-center py-8 text-muted-foreground text-sm italic border-2 border-dashed border-border rounded-lg">No documents yet. Approve this integration's proposals, or add a link below.</div>`}
                        </div>
                        ${i.status === 'archived' ? `<p class="text-sm text-muted-foreground">Archived: its documents can't be added, crawled or labelled. An owner can set it back to Listed.</p>` : `
                        <div class="flex gap-2">
                            <input type="text" placeholder="Add new link URL" id="newLink-${attr(name)}" class="flex-1 min-w-0 ${inputCls}" aria-label="New link URL">
                            ${newLinkProductHTML(`newLinkProduct-${name}`)}
                            <button type="button" class="${btnPrimary}" data-add-link>Add Link</button>
                        </div>
                        <p id="newLinkFlag-${attr(name)}" class="hidden mt-1.5 text-xs text-red-600" role="alert"></p>`}
                        ${pager(docs.total, docs.page, docs.per_page, 'docs')}
                    </div>
                </div>
                <div class="space-y-4">
                    ${factsHTML(i)}
                    ${coverageHTML(i)}
                </div>
            </div>`;
        wireDetail(box, i);
    }

    function wireDetail(box, i) {
        const name = i.name;
        box.querySelector('[data-back]').addEventListener('click', backToList);
        box.querySelector('[data-rename]').addEventListener('click', () => rename(i));
        box.querySelector('[data-add-link]')?.addEventListener('click', () => addLink(name));
        box.querySelectorAll('.paste-btn').forEach(b => b.addEventListener('click', () => openPasteModal(name, b.dataset.url, false)));
        box.querySelectorAll('[data-page="docs"]').forEach(b => b.addEventListener('click', () => {
            S.docPage = Number(b.dataset.to);
            loadDetail();
        }));
        box.querySelector('[data-review-proposals]')?.addEventListener('click', () => {
            S.prop = { ...S.prop, esp: name, state: 'open', source: '', page: 1 };
            showAdminTab('proposals');
        });
        wireProductPickers(box);
        if ($(`newLink-${name}`)) wireDuplicateLinkCheck($(`newLink-${name}`), name);
        box.querySelector('.new-link-product')?.addEventListener('change', () => {
            const flag = $(`newLinkFlag-${name}`);
            if (flag && flag.textContent === PICK_PRODUCT_MESSAGE) setLinkFlag(name, null);
        });
        box.querySelectorAll('.link-checkbox').forEach(cb => cb.addEventListener('change', updateGlobalBulkActions));
        updateGlobalBulkActions();

        $('intType').addEventListener('change', (e) => patch(name, { platform_type: e.target.value }));
        box.querySelector('[data-keep-type]')?.addEventListener('click', () => patch(name, { platform_type: i.platform_type }));
        box.querySelectorAll('[data-product]').forEach(cb => cb.addEventListener('change', () => {
            const products = [...box.querySelectorAll('[data-product]:checked')].map(x => x.dataset.product);
            patch(name, { products });
        }));
        box.querySelectorAll('[data-set-status]').forEach(b => b.addEventListener('click', () => {
            const status = b.dataset.setStatus;
            if (status === i.status) return;
            const what = status === 'active' ? 'put it into chat for every user'
                : status === 'archived' ? 'hide it everywhere' : 'take it out of chat';
            if (!confirm(`Make ${i.display_name} ${STATUS_NAMES[status]}? This will ${what}.`)) return;
            patch(name, { status }, { sidebar: true });
        }));
    }

    async function patch(name, body, { sidebar = false } = {}) {
        try {
            await sendJSON('PATCH', `/admin/integrations/${encodeURIComponent(name)}`, body);
            if (sidebar && typeof reloadSidebar === 'function') reloadSidebar();
        } catch (error) {
            alert(`Could not save: ${error.message}`);
        }
        loadDetail();
    }

    async function rename(i) {
        const next = prompt(`Rename "${i.display_name}":`, i.display_name);
        if (next === null || !next.trim() || next.trim() === i.display_name) return;
        await patch(i.name, { display_name: next.trim() }, { sidebar: i.status === 'active' });
    }

    // ==================== Proposals ====================

    function headerHint(p) {
        if (p.source === 'mechanics') {
            return `${p.partner_function ? `<span class="font-medium text-card-foreground">${esc(p.partner_function)}</span>: ` : ''}${esc(p.reason || p.note || '')}`;
        }
        const label = p.suggested_label === 'loyalty' || p.suggested_label === 'reviews'
            ? `Yotpo header: ${PRODUCT_NAMES[p.suggested_label]}` : 'No product from a Yotpo header';
        return `${esc(label)}${p.note ? ` · ${esc(p.note)}` : ''}`;
    }

    function proposalRowHTML(p) {
        const P = S.prop;
        const open = p.state === 'open';
        const label = P.labels[p.id] || '';
        const prefilled = label && label === p.suggested_label && !P.touched.has(p.id);
        const tone = !label ? 'border-amber-400 text-amber-800' : prefilled ? 'border-dashed border-ring' : 'border-input';
        const picker = `
            <select class="w-28 shrink-0 text-xs px-2 py-1 rounded bg-background cursor-pointer border ${tone}" data-prop-label="${attr(p.id)}" aria-label="Yotpo product for ${attr(p.url)}" title="${attr(PRODUCT_LABEL_HELP)}">
                <option value="" ${!label ? 'selected' : ''} disabled>Product…</option>
                ${Object.entries(PRODUCT_LABELS).map(([v, t]) => `<option value="${v}" ${label === v ? 'selected' : ''}>${t}</option>`).join('')}
            </select>`;
        const decided = open ? '' : `<div class="pl-6 mt-1.5 text-xs text-muted-foreground">${esc(p.state === 'approved' ? 'Approved' : 'Rejected')} by ${esc(p.decided_by || '—')}${p.decided_at ? ` · ${esc(new Date(String(p.decided_at).replace(' ', 'T')).toLocaleString())}` : ''}${p.decision_note ? ` · “${esc(p.decision_note)}”` : ''}</div>`;
        return `
            <div class="p-2 bg-background rounded-lg border ${P.sel.has(p.id) ? 'border-primary' : 'border-border'} transition-colors">
                <div class="flex flex-wrap sm:flex-nowrap items-center gap-2">
                    ${open ? `<input type="checkbox" class="w-4 h-4 rounded border-input cursor-pointer shrink-0" data-prop-sel="${attr(p.id)}" ${P.sel.has(p.id) ? 'checked' : ''} aria-label="Select ${attr(p.url)}">` : ''}
                    <span class="text-xs font-medium px-2 py-0.5 rounded bg-slate-100 text-slate-700 uppercase tracking-wide whitespace-nowrap">${esc(SOURCE_NAMES[p.source] || p.source)}</span>
                    <div class="flex-1 min-w-0">
                        <a href="${attr(p.url)}" target="_blank" rel="noopener" class="block text-sm text-foreground hover:underline truncate">${esc(p.title || p.url)}</a>
                        <span class="block text-xs text-muted-foreground truncate" title="${attr([p.url, p.reason || p.note].filter(Boolean).join(' · '))}">${p.title ? `${esc(p.url)} · ` : ''}${headerHint(p)}</span>
                    </div>
                    ${open ? `${picker}
                        <button type="button" class="px-3 py-1 rounded text-xs font-medium bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-40 disabled:cursor-not-allowed" data-prop-approve="${attr(p.id)}" ${label ? '' : 'disabled title="Pick a product first"'}>Approve</button>
                        <button type="button" class="px-3 py-1 rounded text-xs font-medium text-muted-foreground hover:text-destructive" data-prop-reject="${attr(p.id)}">Reject</button>` : ''}
                </div>
                ${decided}
            </div>`;
    }

    function proposalGroupsHTML(data) {
        const groups = [];
        const byEsp = {};
        data.proposals.forEach(p => {
            const key = p.esp || '';
            if (!byEsp[key]) { byEsp[key] = []; groups.push(key); }
            byEsp[key].push(p);
        });
        if (!groups.length) {
            return `<div class="text-center py-8 text-muted-foreground text-sm italic border-2 border-dashed border-border rounded-lg">No ${esc(S.prop.state)} proposals${S.prop.source ? ` from ${esc(SOURCE_NAMES[S.prop.source] || S.prop.source)}` : ''}.</div>`;
        }
        return groups.map(key => {
            const info = data.integrations[key] || { display_name: 'No integration', status: '', products: [], functions: [] };
            const rows = byEsp[key];
            const openIds = rows.filter(p => p.state === 'open').map(p => p.id);
            const allSelected = openIds.length && openIds.every(id => S.prop.sel.has(id));
            const functions = info.functions && info.functions.length && rows.some(p => p.source === 'mechanics')
                ? `<p class="text-xs text-muted-foreground mb-3"><span class="font-medium text-card-foreground">Partner functions the model found:</span> ${esc(info.functions.map(f => f.name).join(', '))}${info.help_centre ? ` · from ${esc(info.help_centre)}` : ''}</p>` : '';
            return `
                <div class="${card}">
                    <div class="flex flex-wrap items-center gap-2 mb-3">
                        ${openIds.length ? `<input type="checkbox" class="w-4 h-4 rounded border-input cursor-pointer" data-prop-group="${attr(key)}" ${allSelected ? 'checked' : ''} aria-label="Select all for ${attr(info.display_name)}">` : ''}
                        <h4 class="text-base font-semibold text-card-foreground">${esc(info.display_name)}</h4>
                        <span class="text-sm text-muted-foreground">· ${esc(STATUS_NAMES[info.status] || '')}${info.products.length ? ` · ${esc(productsText(info.products))} in the catalog` : ''}</span>
                        ${key ? `<button type="button" class="ml-auto text-sm text-muted-foreground hover:text-foreground" data-open-esp="${attr(key)}">Open integration</button>` : ''}
                    </div>
                    ${functions}
                    <div class="space-y-2">${rows.map(proposalRowHTML).join('')}</div>
                </div>`;
        }).join('');
    }

    function needsPersonHTML(rows) {
        if (!rows || !rows.length) return '';
        return `
            <div class="border-b border-border pb-6 mb-6">
                <h3 class="text-lg font-semibold text-card-foreground mb-2">Partner Articles to Pick by Hand</h3>
                <p class="text-sm text-muted-foreground mb-4">The import could not choose the partner's own articles for these integrations. Open one and add the articles on the functions its Yotpo guides use, with Add Link.</p>
                <div class="${card} space-y-2">
                    ${rows.map(r => `
                        <div class="flex flex-wrap sm:flex-nowrap items-center gap-2 p-2 bg-background rounded-lg border border-border">
                            <span class="font-medium text-sm text-card-foreground w-40 shrink-0 truncate">${esc(r.display_name)}</span>
                            <span class="flex-1 min-w-0 text-xs text-muted-foreground truncate" title="${attr(r.why || '')}">${esc(NEEDS_PERSON[r.kind])}${r.help_centre ? ` · ${esc(r.help_centre)}` : ''}${r.why ? ` · ${esc(r.why)}` : ''}</span>
                            <button type="button" class="${btnOutline} !text-xs" data-open-esp="${attr(r.esp)}">Open</button>
                        </div>`).join('')}
                </div>
            </div>`;
    }

    function lastImportHTML(last) {
        if (!last) {
            return `
                <div>
                    <h3 class="text-lg font-semibold text-card-foreground mb-2">Last Catalog Import</h3>
                    <p class="text-sm text-muted-foreground">No import has been applied yet. An owner runs <code class="font-mono">scripts/import_catalog.py</code>.</p>
                </div>`;
        }
        const c = last.counts || {};
        return `
            <div>
                <h3 class="text-lg font-semibold text-card-foreground mb-2">Last Catalog Import</h3>
                <p class="text-sm text-muted-foreground mb-4">Applied ${esc(last.applied_at || '')} · ${esc(String(last.cards || 0))} catalog cards · ${esc(String(c.created || 0))} integrations created · ${esc(String(c.proposals || 0))} proposals added.</p>
                <details class="${card}">
                    <summary class="text-sm text-muted-foreground hover:text-foreground cursor-pointer">View import report</summary>
                    <pre class="mt-3 text-xs font-mono bg-background border border-border rounded-lg p-3 overflow-x-auto whitespace-pre-wrap leading-relaxed max-h-[32rem]">${esc(last.report || '')}</pre>
                </details>
            </div>`;
    }

    async function loadProposals() {
        const box = $('proposalsAdmin');
        if (!box) return;
        const P = S.prop;
        let data, imp;
        try {
            [data, imp] = await Promise.all([
                getJSON(`/admin/proposals?${qs({ state: P.state, source: P.source, esp: P.esp, page: P.page })}`),
                getJSON('/admin/catalog-import')
            ]);
        } catch (error) {
            box.innerHTML = `<div class="text-sm text-red-700">Could not load the proposals: ${esc(error.message)}</div>`;
            return;
        }
        P.rows = data.proposals;
        P.integrations = data.integrations;
        // Pre-fill each label once from the page's Yotpo header (one product
        // only) or the import's Shared for partner articles: a person checks it
        data.proposals.forEach(p => {
            if (!(p.id in P.labels) && ['loyalty', 'reviews', 'shared'].includes(p.suggested_label)) {
                P.labels[p.id] = p.suggested_label;
            }
        });
        const known = new Set(data.proposals.map(p => p.id));
        [...P.sel].forEach(id => { if (!known.has(id)) P.sel.delete(id); });
        // The tab's count is the total; with one integration picked, counts are its own
        if (!P.esp) setProposalsCount(data.counts.open);
        const espName = P.esp ? (data.integrations[P.esp]?.display_name || P.esp) : '';
        box.innerHTML = `
            <div class="border-b border-border pb-6 mb-6">
                <h3 class="text-lg font-semibold text-card-foreground mb-2">Document Proposals</h3>
                <p class="text-sm text-muted-foreground mb-4">Links found by the catalog import. Nothing reaches the knowledge base until it is approved with a product label. A dashed label was pre-filled from the page's Yotpo header, or as Shared for a partner article: check it before approving. A rejected link is not proposed again.</p>
                <div class="flex flex-wrap items-center gap-2 mb-4">
                    <select class="${inputCls}" data-prop-filter="state" aria-label="State">
                        ${['open', 'approved', 'rejected'].map(s => `<option value="${s}" ${P.state === s ? 'selected' : ''}>${s[0].toUpperCase() + s.slice(1)} (${data.counts[s] || 0})</option>`).join('')}
                    </select>
                    <select class="${inputCls}" data-prop-filter="source" aria-label="Source">
                        <option value="">All sources</option>
                        ${Object.entries(SOURCE_NAMES).map(([v, t]) => `<option value="${v}" ${P.source === v ? 'selected' : ''}>${t}${data.sources[v] ? ` (${data.sources[v]})` : ''}</option>`).join('')}
                    </select>
                    ${P.esp ? `<span class="inline-flex items-center gap-2 text-sm bg-muted px-3 py-1 rounded-full">${esc(espName)} <button type="button" class="text-muted-foreground hover:text-foreground" data-clear-esp aria-label="Show every integration">✕</button></span>` : ''}
                    <span class="flex-1"></span>
                    <span id="propBulk" class="flex flex-wrap items-center gap-2"></span>
                </div>
                <div class="space-y-4" id="propGroups">${proposalGroupsHTML(data)}</div>
                ${pager(data.total, data.page, data.per_page, 'props')}
            </div>
            ${P.state === 'open' && !P.esp ? needsPersonHTML(imp.needs_person) : ''}
            ${lastImportHTML(imp.last_import)}`;
        wireProposals(box);
        renderBulk();
    }

    function renderBulk() {
        const bar = $('propBulk');
        if (!bar) return;
        const P = S.prop;
        const sel = [...P.sel];
        const needLabel = sel.filter(id => !P.labels[id]).length;
        bar.innerHTML = sel.length ? `
            <span class="bg-primary/10 text-primary px-3 py-1 rounded-full font-medium text-sm">${sel.length} selected</span>
            ${needLabel ? `<span class="text-xs text-amber-800">${needLabel} still need${needLabel === 1 ? 's' : ''} a label</span>` : ''}
            <button type="button" class="px-3 py-1.5 bg-primary text-primary-foreground rounded-lg font-medium text-sm disabled:opacity-50 disabled:cursor-not-allowed" data-bulk-approve ${needLabel ? 'disabled' : ''}>Approve Selected</button>
            <button type="button" class="px-3 py-1.5 bg-destructive text-destructive-foreground rounded-lg font-medium text-sm" data-bulk-reject>Reject Selected</button>` : '';
        bar.querySelector('[data-bulk-approve]')?.addEventListener('click', () => approve(sel));
        bar.querySelector('[data-bulk-reject]')?.addEventListener('click', () => reject(sel));
    }

    function wireProposals(box) {
        const P = S.prop;
        box.querySelectorAll('[data-prop-filter]').forEach(s => s.addEventListener('change', () => {
            P[s.dataset.propFilter] = s.value;
            P.page = 1;
            P.sel.clear();
            loadProposals();
        }));
        box.querySelector('[data-clear-esp]')?.addEventListener('click', () => { P.esp = ''; P.page = 1; loadProposals(); });
        box.querySelectorAll('[data-page="props"]').forEach(b => b.addEventListener('click', () => {
            P.page = Number(b.dataset.to);
            loadProposals();
        }));
        box.querySelectorAll('[data-open-esp]').forEach(b => {
            if (!b.closest('#propGroups')) b.addEventListener('click', () => openFromProposals(b.dataset.openEsp));
        });
        wireGroups($('propGroups'));
    }

    // The groups re-render on "select all"; only their own controls are wired here
    function wireGroups(groups) {
        const P = S.prop;
        if (!groups) return;
        groups.querySelectorAll('[data-open-esp]').forEach(b => b.addEventListener('click', () => openFromProposals(b.dataset.openEsp)));
        groups.querySelectorAll('[data-prop-sel]').forEach(cb => cb.addEventListener('change', () => {
            cb.checked ? P.sel.add(cb.dataset.propSel) : P.sel.delete(cb.dataset.propSel);
            cb.closest('.p-2')?.classList.toggle('border-primary', cb.checked);
            cb.closest('.p-2')?.classList.toggle('border-border', !cb.checked);
            renderBulk();
        }));
        groups.querySelectorAll('[data-prop-group]').forEach(cb => cb.addEventListener('change', () => {
            P.rows.filter(p => (p.esp || '') === cb.dataset.propGroup && p.state === 'open')
                .forEach(p => cb.checked ? P.sel.add(p.id) : P.sel.delete(p.id));
            groups.innerHTML = proposalGroupsHTML({ proposals: P.rows, integrations: P.integrations });
            wireGroups(groups);
            renderBulk();
        }));
        groups.querySelectorAll('[data-prop-label]').forEach(s => s.addEventListener('change', () => {
            const id = s.dataset.propLabel;
            P.labels[id] = s.value;
            P.touched.add(id);
            s.classList.remove('border-amber-400', 'text-amber-800', 'border-dashed', 'border-ring');
            s.classList.add('border-input');
            const approveBtn = groups.querySelector(`[data-prop-approve="${CSS.escape(id)}"]`);
            if (approveBtn) { approveBtn.disabled = false; approveBtn.removeAttribute('title'); }
            renderBulk();
        }));
        groups.querySelectorAll('[data-prop-approve]').forEach(b => b.addEventListener('click', () => approve([b.dataset.propApprove])));
        groups.querySelectorAll('[data-prop-reject]').forEach(b => b.addEventListener('click', () => reject([b.dataset.propReject])));
    }

    function openFromProposals(name) {
        showAdminTab('integrations');
        openIntegration(name);
    }

    async function approve(ids) {
        const P = S.prop;
        const items = ids.map(id => ({ id, product: P.labels[id] }));
        if (items.some(x => !x.product)) {
            alert(PICK_PRODUCT_MESSAGE);
            return;
        }
        try {
            const data = await sendJSON('POST', '/admin/proposals/approve', { items });
            const problems = data.results.filter(r => !r.ok || r.warning)
                .map(r => `${r.url || r.id} — ${r.error || r.warning}`);
            const queued = data.results.filter(r => r.queued).length;
            ids.forEach(id => P.sel.delete(id));
            let message = `Approved ${data.approved} of ${items.length}.`;
            if (queued) message += ` ${queued} queued for crawling.`;
            else if (data.approved) message += ' Crawl them from the integration\'s page.';
            if (problems.length) message += `\n\nNot approved or not queued:\n${problems.join('\n')}`;
            alert(message);
        } catch (error) {
            alert(`Could not approve: ${error.message}`);
        }
        loadProposals();
    }

    async function reject(ids) {
        const note = prompt(`Reject ${ids.length} link${ids.length === 1 ? '' : 's'}? They will not be proposed again.\n\nOptional note (why):`, '');
        if (note === null) return;
        try {
            await sendJSON('POST', '/admin/proposals/reject', { ids, note });
            ids.forEach(id => S.prop.sel.delete(id));
        } catch (error) {
            alert(`Could not reject: ${error.message}`);
        }
        loadProposals();
    }

    // ==================== entry points ====================

    function refreshView() {
        return S.open ? loadDetail() : loadList();
    }

    // Called by app.js's loadESPManagement after every link action
    async function reload() {
        setListOnlySections(!S.open);
        await Promise.all([refreshView(), loadCrawlSummary()]);
    }

    // A crawl was queued: follow it in the strip
    function watchCrawls() {
        S.hadActiveJobs = true;
        loadCrawlSummary();
    }

    window.AdminIntegrations = { reload, loadProposals, watchCrawls, openIntegration };
})();
