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
    // What the admin shows for each internal value: plain words, so nobody
    // needs to know the code.
    const TYPE_NAMES = { messaging: 'Email & SMS', storefront: 'Store & checkout', service: 'Customer service', data: 'Data & automation', content: 'Reviews & content' };
    // Two states (Leo, 2026-10-15): in chat, or admin only. A row archived by
    // older code reads "Not in chat" and is read-only until set to it.
    const STATUS_NAMES = { active: 'In chat', listed: 'Not in chat', archived: 'Not in chat' };
    // One short line each: shown under the In chat? control and as tooltips
    const STATUS_HELP = {
        active: 'Anyone using the chat can pick it.',
        listed: 'Only admins see it, here. Prepare its documents before it goes into chat.',
        archived: 'Archived by an older version: set it to Not in chat to work on its documents.'
    };
    const PRODUCT_NAMES = { loyalty: 'Loyalty', reviews: 'Reviews' };
    const SOURCE_KIND = { yotpo_support: 'Yotpo guide', yotpo_developer: 'Yotpo developer docs', partner: "Platform's own page", pasted: 'Pasted' };
    const SOURCE_NAMES = { catalog: 'From yotpo.com', sitemap: 'New Yotpo article', manual: 'Added by hand', mechanics: 'Platform help article' };
    // The list's To do filter, one at a time
    const FLAG_NAMES = {
        proposals: 'Links to review',
        unlabelled: 'No product picked',
        failed: 'Crawl failed',
        misses: 'Page gone',
        mixed_types: 'Kind of platform to set or confirm'
    };
    const NEEDS_PERSON = {
        blocked: 'Help site blocks automatic reading',
        nothing_found: "Articles found didn't fit",
        no_help_centre: 'Help site not found'
    };
    // The crawl box, in this order, when non-zero
    const STRIP_STATES = ['crawling', 'queued', 'waiting', 'retrying', 'failed', 'saved_copy', 'pending'];
    const STRIP_TEXT = {
        crawling: 'crawling now',
        queued: 'waiting',
        waiting: 'paused by the website',
        retrying: 'retrying',
        failed: 'failed',
        saved_copy: 'using a saved copy',
        pending: 'not crawled yet'
    };
    // The answers to "what is this?", one hover away (the ⓘ beside a label)
    const HELP = {
        crawls: "Crawling reads a document's page and saves its text for the AI. Only crawled documents are used.",
        products: "Which Yotpo products it works with. Ticked automatically when it has a document labelled with that product; the yotpo.com import ticks them too. Tick the others by hand.",
        kind: 'Picks the instructions the AI follows for it. Only Email & SMS works in chat for now.',
        inChat: 'In chat: anyone using the chat can pick it. Not in chat: only admins see it, here. Only an owner changes this.',
        yotpoCom: 'Where yotpo.com/integrations lists it, and under which categories. The yotpo.com import links these.',
        documents: "What the AI reads about it. Each needs a product: Loyalty, Reviews, or Shared (the platform's own help, true for both).",
        suggested: 'Links the yotpo.com import and Find links found for each integration. None is used until you approve it.',
        sitemap: "Yotpo's help centre lists every article and when it last changed. It is read once a month: our Yotpo guides that changed are crawled again, and new or vanished articles are listed here.",
        findLinks: "Looks for its documentation: its yotpo.com page, Yotpo's guides on support.yotpo.com, and its own help articles on the features the integration uses (the AI picks and checks those). What it finds goes to Suggested Links; nothing is used until you approve it."
    };
    // Under each kind in the Add integration dialog: what it means, with
    // integrations of that kind
    const KIND_HELP = {
        messaging: 'Sends the emails and texts: Klaviyo, Attentive.',
        storefront: 'Where shoppers browse, pay or subscribe: Shopify, Recharge, Tapcart.',
        service: 'Help desks and chat, where agents answer customers: Gorgias, Zendesk.',
        data: 'Moves data between systems, with no screen shoppers see: analytics, ads, automation.',
        content: 'Reviews and other customer content, in or out: Bazaarvoice.'
    };
    // What a running Find links is doing (find_links_job.STEPS)
    const FIND_STEPS = {
        starting: 'Starting…',
        'yotpo.com': 'Reading its yotpo.com page…',
        yotpo_guides: "Reading Yotpo's guides…",
        help_site: 'Searching its help site; the AI reads the articles…',
        help_site_no_ai: 'Looking for its help site…',
        saving: 'Saving what it found…'
    };
    const FIND_POLL_MS = 3000;
    const NOT_LINKED = 'Not linked to yotpo.com yet: the yotpo.com import fills this in.';
    const SUMMARY_POLL_MS = 5000;
    const SAVED_MS = 1600;
    const MISS_LIMIT = 3;

    const inputCls = 'h-10 px-3 border border-input bg-background rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-ring';
    const card = 'bg-muted/50 rounded-lg p-4 border border-border';
    const th = 'py-3 px-4 text-xs font-medium uppercase tracking-wide text-muted-foreground';
    const btnPrimary = 'px-4 py-2 bg-primary text-primary-foreground rounded-lg font-medium text-sm hover:bg-primary/90 transition-colors whitespace-nowrap';
    const btnOutline = 'px-3 py-1 border border-input bg-background text-foreground rounded-lg font-medium text-sm hover:bg-muted transition-colors whitespace-nowrap disabled:opacity-50 disabled:cursor-not-allowed';

    const S = {
        filters: { q: '', category: '', type: '', status: '', flag: '' },
        page: 1,
        open: null,            // the integration whose page is shown, or null for the list
        docPage: 1,
        facets: null,
        crawlDetails: false,
        crawlSince: null,      // the database's clock when the page first asked: "this visit"
        summaryTimer: null,
        hadActiveJobs: false,
        listTicket: 0,
        detail: null,          // the open integration, as last loaded
        findTimer: null,
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

    const STATE_HELP = {
        crawled: 'Its text is saved and the AI uses it.',
        pending: "Not crawled yet, so the AI can't use it. Tick it and press Crawl Selected.",
        failed: 'The last crawl failed (the reason is below it).',
        saved_copy: "The page couldn't be crawled, so an older saved copy is used.",
        queued: 'Waiting its turn to be crawled.',
        crawling: 'Being crawled right now.',
        retrying: 'The crawl failed and will be tried again.',
        waiting: 'The website asked us to slow down; it will be crawled shortly.',
        retired: "Retired: no longer crawled, and the AI doesn't use it. Tick it and press Crawl Selected to bring it back."
    };

    function stateBadge(state) {
        return `<span class="text-xs font-medium px-2 py-0.5 rounded ${crawlStateStyle(state).badge} uppercase tracking-wide whitespace-nowrap" ${tip(STATE_HELP[state])}>${esc(statusLabel(state))}</span>`;
    }

    function statusPill(status) {
        const tone = status === 'active' ? 'bg-green-100 text-green-800' : 'bg-slate-100 text-slate-700';
        return `<span class="text-xs font-medium px-2 py-0.5 rounded whitespace-nowrap ${tone}" ${tip(STATUS_HELP[status])}>${esc(STATUS_NAMES[status] || status)}</span>`;
    }

    // A product box. Ticked because it has documents with that label: locked,
    // since unticking would be undone by those documents. Not `disabled` (the
    // browser greys that out until it reads as unticked): a click is
    // cancelled and shows why (wireTips)
    function productBox(i, p, dataAttr) {
        const fromDocs = (i.products_from_documents || []).includes(p);
        return `
            <label class="inline-flex items-center gap-1.5 mr-3 last:mr-0 text-sm text-card-foreground ${fromDocs ? 'cursor-help' : 'cursor-pointer'}" ${fromDocs ? tip(`Ticked because it has documents labelled ${PRODUCT_NAMES[p]}.`) : ''}>
                <input type="checkbox" class="w-4 h-4 rounded border-input ${fromDocs ? 'cursor-help' : ''}" ${dataAttr}="${p}" data-esp="${attr(i.name)}" ${i.products.includes(p) ? 'checked' : ''} ${fromDocs ? 'data-locked="1" aria-disabled="true"' : ''} aria-label="${attr(`${i.display_name} works with ${PRODUCT_NAMES[p]}`)}">${PRODUCT_NAMES[p]}
            </label>`;
    }

    // An explanation shown in the admin's own popup (wireTips below), not the
    // browser's title tooltip: that one appears late or never, and not on a
    // click. Empty text adds nothing.
    function tip(text) {
        return text ? `data-tip="${attr(text)}"` : '';
    }

    // A small ⓘ beside a label: hover, focus or click it for the explanation
    function info(text) {
        return `<button type="button" class="info-tip inline-flex items-center justify-center w-4 h-4 rounded-full border border-border text-[10px] leading-none font-semibold text-muted-foreground hover:text-foreground hover:border-foreground cursor-help align-middle select-none focus:outline-none focus-visible:ring-2 focus-visible:ring-ring" ${tip(text)} aria-label="${attr(text)}">i</button>`;
    }

    // One popup for every [data-tip] in the admin panel. Hover or focus
    // shows it; a click on an ⓘ keeps it open until a click elsewhere,
    // Escape, or scrolling. Its text is set with textContent.
    function wireTips() {
        const modal = $('adminModal');
        if (!modal || modal.dataset.tipsWired) return;
        modal.dataset.tipsWired = '1';
        const pop = document.createElement('div');
        pop.id = 'adminTip';
        pop.setAttribute('role', 'tooltip');
        pop.className = 'hidden fixed max-w-xs rounded-md bg-gray-900 text-white text-xs leading-snug px-2.5 py-1.5 shadow-lg pointer-events-none';
        pop.style.zIndex = '70';
        document.body.appendChild(pop);
        let shownFor = null;
        let pinned = false;
        let timer = null;

        const place = (el) => {
            const r = el.getBoundingClientRect();
            const w = pop.offsetWidth;
            const h = pop.offsetHeight;
            const left = Math.min(Math.max(8, r.left + r.width / 2 - w / 2), window.innerWidth - w - 8);
            const below = r.bottom + 6;
            pop.style.left = `${left}px`;
            pop.style.top = `${below + h > window.innerHeight - 8 ? Math.max(8, r.top - h - 6) : below}px`;
        };
        const show = (el) => {
            const text = el.getAttribute('data-tip');
            if (!text) return;
            pop.textContent = text;
            pop.classList.remove('hidden');
            place(el);
            shownFor = el;
            el.setAttribute('aria-describedby', 'adminTip');
        };
        const hide = () => {
            clearTimeout(timer);
            pop.classList.add('hidden');
            shownFor?.removeAttribute('aria-describedby');
            shownFor = null;
            pinned = false;
        };

        modal.addEventListener('mouseover', (e) => {
            const el = e.target.closest('[data-tip]');
            if (!el || pinned || el === shownFor) return;
            clearTimeout(timer);
            timer = setTimeout(() => show(el), 120);
        });
        modal.addEventListener('mouseout', (e) => {
            const el = e.target.closest('[data-tip]');
            if (!el || pinned || el.contains(e.relatedTarget)) return;
            clearTimeout(timer);
            if (el === shownFor) hide();
        });
        modal.addEventListener('focusin', (e) => {
            const el = e.target.closest('[data-tip]');
            if (el && !pinned) show(el);
        });
        modal.addEventListener('focusout', (e) => {
            if (!pinned && e.target.closest('[data-tip]') === shownFor) hide();
        });
        // Capture, so a click on an ⓘ inside a clickable row or a label
        // doesn't also open the row or focus the field
        modal.addEventListener('click', (e) => {
            // A locked product tick: keep it ticked and say why
            const locked = e.target.closest('label')?.querySelector('input[data-locked]');
            if (locked && e.target.closest('label').hasAttribute('data-tip')) {
                e.preventDefault();
                e.stopPropagation();
                show(e.target.closest('label'));
                pinned = true;
                return;
            }
            const el = e.target.closest('.info-tip');
            if (!el) {
                if (pinned) hide();
                return;
            }
            e.preventDefault();
            e.stopPropagation();
            if (pinned && shownFor === el) return hide();
            show(el);
            pinned = true;
        }, true);
        document.addEventListener('keydown', (e) => { if (e.key === 'Escape' && shownFor) hide(); });
        modal.addEventListener('scroll', () => { if (shownFor) hide(); }, true);
        window.addEventListener('resize', () => { if (shownFor) hide(); });
    }

    // A brief "Saved" beside what was just saved
    function flashSaved(el, { below = false } = {}) {
        if (!el) return;
        const note = document.createElement('span');
        note.className = `${below ? 'absolute left-3 bottom-0 text-[11px]' : 'ml-2 text-xs'} font-normal text-green-700 transition-opacity duration-500`;
        note.textContent = 'Saved';
        note.setAttribute('role', 'status');
        el.appendChild(note);
        setTimeout(() => { note.style.opacity = '0'; }, SAVED_MS);
        setTimeout(() => note.remove(), SAVED_MS + 600);
    }

    function productsText(products, empty = 'Not set') {
        return (products || []).map(p => PRODUCT_NAMES[p] || p).join(' · ') || empty;
    }

    function plural(n, one, many) {
        return `${n} ${n === 1 ? one : many}`;
    }

    function hostOf(url) {
        try { return new URL(url).hostname.replace(/^www\./, ''); } catch (e) { return ''; }
    }

    // An address without its https://www., for the line under a name
    function shortUrl(url) {
        return String(url || '').replace(/^https?:\/\/(www\.)?/, '').replace(/\/$/, '');
    }

    // A document's name when it has no title yet (titles come from crawls of
    // Yotpo guides): the last part of its address, as words. An address that
    // ends in a number (help-centre article ids) reads as "<site> article <id>".
    function pageName(url) {
        try {
            const u = new URL(url);
            const host = u.hostname.replace(/^www\./, '');
            const last = u.pathname.split('/').filter(Boolean).pop() || '';
            const decoded = decodeURIComponent(last).replace(/\.[a-z]+$/i, '');
            const id = decoded.match(/^(\d{4,})(?:[-_]|$)/);
            const words = decoded.replace(/^\d+[-_]?/, '').replace(/[-_]+/g, ' ').trim();
            if (words) return words[0].toUpperCase() + words.slice(1);
            return id ? `${host} article ${id[1]}` : host;
        } catch (e) {
            return url;
        }
    }

    // A help-site address as a link, escaped
    function siteLink(url) {
        return url ? `<a href="${attr(url)}" target="_blank" rel="noopener" class="underline hover:text-foreground">${esc(shortUrl(url))}</a>` : '';
    }

    // What the import found, or didn't, about the platform's own help site
    // (HTML: the address is a link)
    function helpSiteHTML(m) {
        if (!m) return '';
        if (m.blocked) return `Its help site${m.help_centre ? ` (${siteLink(m.help_centre)})` : ''} blocks automatic reading: add its help articles yourself, labelled Shared.`;
        if (!m.help_centre) return "Its help site wasn't found: add its help articles yourself, labelled Shared.";
        if (!m.accepted) return `The articles found on ${siteLink(m.help_centre)} didn't fit: add the right ones yourself, labelled Shared.`;
        return '';
    }

    // The import's notes on a suggested link, in words
    function noteText(note) {
        if (!note) return '';
        if (note === 'Yotpo guide linked from the catalog') return 'Yotpo guide';
        if (note === 'partner page linked from the catalog') return "Platform's own page about Yotpo";
        if (note === 'Yotpo guide found by its name on support.yotpo.com') return "Yotpo guide with its name in the address: check it's about this platform";
        if (note.startsWith('renamed from ')) return 'Dead link on yotpo.com; this is its new address';
        if (note.startsWith('redirected from ')) return 'The yotpo.com link now leads here';
        return note;
    }

    function pager(total, page, perPage, kind) {
        if (total <= perPage) {
            // An integration's documents: the count is in the heading already
            if (kind === 'docs') return '';
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
            data = await getJSON(`/admin/crawl-summary${S.crawlSince ? `?since=${encodeURIComponent(S.crawlSince)}` : ''}`);
        } catch (error) {
            box.innerHTML = `<div class="${card} mb-6 text-sm text-red-700">Could not load the crawl status: ${esc(error.message)}</div>`;
            return;
        }
        if (!S.crawlSince) S.crawlSince = data.now;
        // Shown only when there is something to see: documents waiting,
        // crawling, failed or never crawled, or crawled during this visit
        const counts = STRIP_STATES.filter(s => data.states[s]);
        const crawledNow = data.crawled_since || 0;
        if (!counts.length && !crawledNow && !data.active_jobs) {
            box.innerHTML = '';
            watch(false);
            return;
        }
        const dot = '<span class="text-muted-foreground" aria-hidden="true">·</span>';
        const parts = (crawledNow ? [`<span class="text-green-800" ${tip('Crawled since you opened the Integrations tab.')}><span class="font-medium tabular-nums">${crawledNow}</span> crawled</span>`] : [])
            .concat(counts.map(s => `<span class="${s === 'failed' ? 'text-red-700' : ''}" ${s === 'pending' ? tip('Listed under To do as “not crawled”') : ''}><span class="font-medium tabular-nums">${data.states[s]}</span> ${esc(STRIP_TEXT[s])}</span>`));
        box.innerHTML = `
            <div class="${card} !py-3 mb-6">
                <div class="flex flex-wrap items-center gap-x-3 gap-y-1 text-sm text-card-foreground">
                    <span class="inline-flex items-center gap-1.5 font-semibold">Crawls ${info(HELP.crawls)}</span>
                    ${parts.join(dot)}
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
            </tr>`).join('') : `<tr><td colspan="3" class="py-3 text-sm text-muted-foreground">No website has crawls waiting or failed.</td></tr>`;
        const jobs = !data.queue
            ? '<p class="text-sm text-muted-foreground">On this server a crawl runs while you wait, so nothing queues here.</p>'
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
                    <thead><tr class="border-b border-border"><th class="text-left ${th} !px-0">Website</th><th class="text-right ${th}">Waiting</th><th class="text-right ${th}">Failed</th></tr></thead>
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
        // Each filter is named like the column it filters
        const sel = (key, label, options, width) => `
            <select class="filter-select ${inputCls} ${width}" data-filter="${key}" aria-label="${attr(label)}">
                <option value="">${esc(label)}</option>
                ${options.map(([v, t]) => `<option value="${attr(v)}" ${f[key] === v ? 'selected' : ''}>${esc(t)}</option>`).join('')}
            </select>`;
        return `
            <div class="flex flex-wrap items-center gap-3 mb-5">
                <input id="intSearch" value="${attr(f.q)}" placeholder="Search" class="flex-1 min-w-[12rem] ${inputCls}" aria-label="Search integrations by name or category">
                ${sel('category', 'Category', facets.categories.map(c => [c.slug, `${c.name} (${c.count})`]), 'w-40')}
                ${sel('type', 'Kind of platform', PLATFORM_TYPES.map(t => [t, TYPE_NAMES[t]]), 'w-44')}
                ${sel('status', 'In chat?', [['active', STATUS_NAMES.active], ['listed', STATUS_NAMES.listed]], 'w-36')}
                ${sel('flag', 'To do', Object.keys(FLAG_NAMES).map(k => [k, flagOption(k, facets.flags[k])]), 'w-36')}
            </div>
            <div id="intTable"></div>`;
    }

    function flagOption(k, n) {
        return `${FLAG_NAMES[k]} (${n || 0})`;
    }

    function attentionHTML(i) {
        const waiting = i.not_crawled;
        const parts = [
            i.open_proposals && `<span class="text-card-foreground">${plural(i.open_proposals, 'link to review', 'links to review')}</span>`,
            i.documents.unlabelled && `<span class="text-amber-800">${plural(i.documents.unlabelled, 'needs a product', 'need a product')}</span>`,
            i.failed && `<span class="text-red-700">${plural(i.failed, 'crawl failed', 'crawls failed')}</span>`,
            i.misses && `<span class="text-red-700">${plural(i.misses, 'page gone', 'pages gone')}</span>`,
            waiting && `<span class="text-amber-800" ${tip(STATE_HELP.pending)}>${waiting} not crawled</span>`,
            !i.platform_type && '<span class="text-amber-800">set its kind</span>',
            i.type_choices.length && `<span class="text-amber-800" ${tip(`yotpo.com lists it under ${i.type_choices.map(t => TYPE_NAMES[t]).join(' and ')}`)}>confirm its kind</span>`
        ].filter(Boolean);
        // one per line: the column is narrow
        return parts.join('<br>');
    }

    function tableHTML(data) {
        const rows = data.integrations.map(i => `
            <tr class="group border-b border-border last:border-0 hover:bg-muted/30 cursor-pointer" data-open-int="${attr(i.name)}" tabindex="0">
                <td class="py-3 px-4"><div class="font-medium text-card-foreground">${esc(i.display_name)}</div><div class="text-xs text-muted-foreground truncate max-w-[12rem]" title="${attr(i.category_names.join(' · '))}">${esc(i.category_names.join(' · '))}</div></td>
                <td class="relative py-3 px-4 whitespace-nowrap cursor-default" data-products-cell>
                    ${['loyalty', 'reviews'].map(p => productBox(i, p, 'data-row-product')).join('')}
                </td>
                <td class="py-3 px-4 whitespace-nowrap ${i.platform_type ? 'text-muted-foreground' : 'text-amber-800'}">${esc(TYPE_NAMES[i.platform_type] || 'Not set')}</td>
                <td class="py-3 px-4">${statusPill(i.status)}</td>
                <td class="py-3 px-4 text-right tabular-nums text-muted-foreground">${i.documents.total}</td>
                <td class="py-3 pl-8 pr-4 text-xs min-w-[7rem]">${attentionHTML(i) || '<span class="text-muted-foreground">—</span>'}</td>
                <td class="py-3 pr-4 text-muted-foreground group-hover:text-foreground" aria-hidden="true">›</td>
            </tr>`).join('');
        const head = (text, help) => `<th class="text-left ${th}"><span class="inline-flex items-center gap-1.5 whitespace-nowrap">${text}${help ? ` ${info(help)}` : ''}</span></th>`;
        return `
            <div class="bg-background border border-border rounded-lg overflow-x-auto">
                <table class="w-full text-sm min-w-[680px]">
                    <thead><tr class="border-b border-border bg-muted">
                        ${head('Integration')}${head('Yotpo products', HELP.products)}${head('Kind of platform', HELP.kind)}
                        ${head('In chat?', HELP.inChat)}<th class="text-right ${th}">Documents</th>${head('To do').replace('px-4', 'pl-8 pr-4')}<th class="w-4"></th>
                    </tr></thead>
                    <tbody>${rows || '<tr><td colspan="7" class="text-center py-8 text-muted-foreground">No integrations match these filters.</td></tr>'}</tbody>
                </table>
            </div>
            ${pager(data.total, data.page, data.per_page, 'list')}`;
    }

    async function loadList({ rebuildShell = false } = {}) {
        const box = $('espManagement');
        if (!box) return;
        const ticket = ++S.listTicket;
        if (!box.innerHTML.trim()) box.innerHTML = '<p class="text-sm text-muted-foreground">Loading integrations…</p>';
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
            box.querySelectorAll('[data-filter="flag"] option[value]:not([value=""])').forEach(o => {
                o.textContent = flagOption(o.value, data.facets.flags[o.value]);
            });
        }
        const table = $('intTable');
        table.innerHTML = tableHTML(data);
        table.querySelectorAll('[data-open-int]').forEach(row => {
            row.addEventListener('click', (e) => {
                // The product ticks save on their own; clicking them never opens the row
                if (e.target.closest('[data-products-cell]')) return;
                openIntegration(row.dataset.openInt);
            });
            row.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' && !e.target.closest('[data-products-cell]')) openIntegration(row.dataset.openInt);
            });
        });
        table.querySelectorAll('[data-row-product]').forEach(cb => cb.addEventListener('change', () => saveRowProducts(cb)));
        table.querySelectorAll('[data-page="list"]').forEach(b => b.addEventListener('click', () => {
            S.page = Number(b.dataset.to);
            loadList();
        }));
    }

    // A product tick in the list: saved at once, then the list redraws
    async function saveRowProducts(cb) {
        const cell = cb.closest('[data-products-cell]');
        const boxes = [...cell.querySelectorAll('[data-row-product]')];
        const products = boxes.filter(x => x.checked).map(x => x.dataset.rowProduct);
        const esp = cb.dataset.esp;
        boxes.forEach(x => { x.disabled = true; });
        let saved = true;
        try {
            await sendJSON('PATCH', `/admin/integrations/${encodeURIComponent(esp)}`, { products });
        } catch (error) {
            saved = false;
            cb.checked = !cb.checked;
            alert(`Could not save: ${error.message}`);
        }
        await loadList();
        if (saved) {
            const again = [...document.querySelectorAll('#intTable [data-row-product]')].find(x => x.dataset.esp === esp);
            flashSaved(again?.closest('[data-products-cell]'), { below: true });
        }
    }

    function wireListShell(box) {
        let timer = null;
        $('intSearch').addEventListener('input', (e) => {
            clearTimeout(timer);
            timer = setTimeout(() => { S.filters.q = e.target.value.trim(); S.page = 1; loadList(); }, 250);
        });
        // To do (data-filter="flag") is one choice at a time, like the other filters
        box.querySelectorAll('[data-filter]').forEach(s => s.addEventListener('change', () => {
            S.filters[s.dataset.filter] = s.value;
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
        stopFindPoll();
        S.open = name;
        S.docPage = 1;
        setListOnlySections(false);
        loadDetail();
        $('espManagementTab')?.closest('.overflow-y-auto')?.scrollTo({ top: 0 });
    }

    function backToList() {
        stopFindPoll();
        S.open = null;
        setListOnlySections(true);
        loadList({ rebuildShell: true });
        if (typeof updateGlobalBulkActions === 'function') updateGlobalBulkActions();
    }

    function docRowHTML(name, link, readOnly = false) {
        const style = crawlStateStyle(link.status);
        const meta = [SOURCE_KIND[link.source_kind], (link.supported_plans || []).join(', '), (link.supported_platforms || []).join(', ')]
            .filter(Boolean).join(' · ');
        const missing = link.consecutive_misses >= MISS_LIMIT && !link.retired && !readOnly
            ? `<span class="flex flex-wrap items-center gap-x-2 text-xs text-red-700">Page not found in the last ${link.consecutive_misses} crawls.
                   <button type="button" class="underline hover:text-red-900" data-replace="${attr(link.url)}">Replace with its new address…</button>
                   <button type="button" class="underline hover:text-red-900" data-retire="${attr(link.url)}">Retire it</button></span>` : '';
        return `
            <div class="flex items-center gap-2 p-2 bg-background rounded-lg border ${style.row || 'border-border'} hover:border-primary transition-colors">
                ${readOnly ? '' : `<input type="checkbox" class="link-checkbox w-4 h-4 rounded border-input cursor-pointer shrink-0" data-esp="${attr(name)}" value="${attr(link.url)}" aria-label="Tick ${attr(link.url)}">`}
                ${stateBadge(link.status)}
                ${link.needs_backfill ? '<span class="text-xs font-medium px-2 py-0.5 rounded bg-amber-100 text-amber-800 uppercase tracking-wide" data-tip="Its text is not saved in the database yet. Crawl it once (Crawl Selected) to save a copy.">no backup</span>' : ''}
                <div class="flex-1 min-w-0">
                    <a href="${attr(link.url)}" target="_blank" rel="noopener" class="block text-sm text-foreground hover:text-primary hover:underline truncate" title="${attr(link.url)}">${esc(link.title || pageName(link.url))}</a>
                    <span class="block text-xs text-muted-foreground truncate" title="${attr(link.url)}">${esc([shortUrl(link.url), meta].filter(Boolean).join(' · '))}</span>
                    ${linkDetailHTML(link)}
                    ${missing}
                </div>
                ${readOnly ? '' : productPickerHTML(name, link)}
                ${!readOnly && isCrawlCandidate(link) ? `<button type="button" class="paste-btn px-2 py-1 text-xs font-medium text-muted-foreground hover:text-foreground border border-border rounded whitespace-nowrap" data-url="${attr(link.url)}" title="If the page can't be crawled, paste its text instead">Paste text</button>` : ''}
            </div>`;
    }

    function factsHTML(i) {
        const owner = isOwner();
        const linked = i.catalog_cards.length > 0;
        // "In chat" is offered only for the kinds whose instructions exist
        const canChat = (i.in_chat_types || ['messaging']).includes(i.platform_type);
        const statusButtons = ['active', 'listed'].map(s => {
            const blocked = s === 'active' && !canChat && i.status !== 'active';
            const why = blocked ? 'Only Email & SMS platforms can be in chat for now.' : STATUS_HELP[s];
            return `
            <button type="button" role="radio" aria-checked="${s === i.status}" data-set-status="${s}"
                class="px-2.5 py-1 text-xs font-medium rounded-md whitespace-nowrap ${s === i.status ? 'bg-background shadow-sm text-foreground' : 'text-muted-foreground hover:text-foreground'} disabled:cursor-not-allowed disabled:opacity-50"
                ${owner && !blocked ? '' : 'disabled'} title="${attr(why)}">${STATUS_NAMES[s]}</button>`;
        }).join('');
        // One line under the control: what the current state means, or why it can't change
        const statusLine = !canChat && i.status !== 'active'
            ? 'Only Email &amp; SMS platforms can be in chat for now.'
            : `${esc(STATUS_HELP[i.status] || '')}${owner ? '' : ' Only an owner can change this.'}`;
        const kindsText = (i.category_kinds || []).filter(c => c.type).map(c => `${c.name}: ${TYPE_NAMES[c.type]}`).join(' · ');
        const note = (html) => `<div class="mt-2 rounded-md border border-amber-300 bg-amber-50 px-2 py-1.5 text-xs text-amber-900">${html}</div>`;
        const typeNote = !i.platform_type
            ? note('Not set yet: pick the closest kind.')
            : i.type_choices.length
            ? note(`<span class="cursor-help underline decoration-dotted" ${tip(kindsText)}>A guess: its yotpo.com categories fit more than one kind.</span>
                   <button type="button" class="mt-1.5 block px-3 py-1 rounded-md bg-background border border-amber-400 font-medium text-amber-900 hover:bg-amber-100" data-keep-type>Confirm ${esc(TYPE_NAMES[i.platform_type])}</button>`)
            : '';
        const kindHelp = HELP.kind + (i.type_set_by && !i.type_choices.length
            ? ` Confirmed by ${i.type_set_by === 'admin password' ? 'an admin' : i.type_set_by}.` : '');
        const label = (text, help, savedFor) => `<div class="flex items-center gap-1.5 text-sm font-medium text-card-foreground mb-1.5"${savedFor ? ` data-saved-for="${savedFor}"` : ''}>${text}${help ? ` ${info(help)}` : ''}</div>`;
        const muted = (html) => `<p class="text-xs text-muted-foreground mt-1.5">${html}</p>`;
        return `
            <div class="${card} space-y-5">
                <div>
                    ${label('In chat?', HELP.inChat)}
                    <div class="inline-flex flex-wrap gap-1 p-1 rounded-lg bg-muted border border-border" role="radiogroup" aria-label="In chat?">${statusButtons}</div>
                    ${muted(statusLine)}
                </div>
                <div>
                    <label class="flex items-center gap-1.5 text-sm font-medium text-card-foreground mb-1.5" for="intType" data-saved-for="kind">Kind of platform ${info(kindHelp)}</label>
                    <select id="intType" class="w-full ${inputCls}">
                        ${i.platform_type ? '' : '<option value="" selected disabled>Not set</option>'}
                        ${PLATFORM_TYPES.map(t => `<option value="${t}" ${i.platform_type === t ? 'selected' : ''}>${TYPE_NAMES[t]}</option>`).join('')}
                    </select>
                    ${typeNote}
                </div>
                <div>
                    ${label('Yotpo products', HELP.products, 'products')}
                    <div class="flex text-sm">${['loyalty', 'reviews'].map(p => productBox(i, p, 'data-product')).join('')}</div>
                </div>
                <div>
                    ${label('On yotpo.com', HELP.yotpoCom)}
                    ${linked || i.category_names.length ? `
                        <div class="flex flex-wrap gap-1">${i.category_names.map(c => `<span class="text-xs px-2 py-0.5 rounded-full bg-background border border-border">${esc(c)}</span>`).join('')}</div>
                        <div class="mt-1.5">${i.catalog_cards.map(c => `<a href="${attr(c.url)}" target="_blank" rel="noopener" class="block text-xs text-foreground hover:underline py-0.5">yotpo.com/integrations/${esc(c.slug)} ↗</a>`).join('')}</div>`
                        : `<p class="text-xs text-muted-foreground">${esc(NOT_LINKED)}</p>`}
                </div>
            </div>`;
    }

    // Under its documents: what to do next, only when there is something
    function nextStepsHTML(i, docsTotal) {
        const helpSite = helpSiteHTML(i.mechanics);
        const searching = i.find_links && i.find_links.state === 'running';
        const lines = [
            !docsTotal && !i.open_proposals && i.status !== 'archived' && !searching
                && '<p class="text-xs text-muted-foreground">Nothing suggested for it yet: use Find links, or add a link above.</p>',
            helpSite && `<p class="text-xs text-amber-800">${helpSite}</p>`
        ].filter(Boolean).join('');
        return lines ? `<div class="mt-3 space-y-2">${lines}</div>` : '';
    }

    async function loadDetail() {
        const box = $('espManagement');
        const name = S.open;
        if (!box || !name) return;
        let detail, docs;
        try {
            [detail, docs] = await Promise.all([
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
        const i = detail.integration;
        S.detail = i;
        // An archived integration's rows are shown, but not selectable: the
        // document routes don't find archived integrations
        const rows = docs.documents.map(link => docRowHTML(name, link, i.status === 'archived')).join('');
        box.innerHTML = `
            <button type="button" class="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground mb-4" data-back>← All integrations</button>
            <h4 class="text-base font-semibold text-card-foreground mb-4 flex flex-wrap items-center gap-2">
                <span>${esc(i.display_name)}</span>
                <button type="button" class="text-muted-foreground hover:text-primary transition-colors" data-rename title="Rename ${attr(i.display_name)}" aria-label="Rename ${attr(i.display_name)}">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20h9"></path><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4Z"></path></svg>
                </button>
                ${statusPill(i.status)}
            </h4>
            <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div class="lg:col-span-2 min-w-0">
                    <div class="${card}">
                        <div class="flex flex-wrap items-center gap-2 mb-3">
                            <h4 class="flex items-center gap-1.5 text-sm font-semibold text-card-foreground">Documents (${docs.total}) ${info(HELP.documents)}</h4>
                            ${docs.total ? '<span class="unlabelled-count"></span>' : ''}
                            ${i.open_proposals && !(i.find_links && i.find_links.state === 'done')
                                ? `<button type="button" class="ml-auto ${btnPrimary} !px-3 !py-1" data-review-proposals>Review ${plural(i.open_proposals, 'suggested link', 'suggested links')} →</button>`
                                : docs.total && i.status !== 'archived' ? '<span class="ml-auto text-xs text-muted-foreground">Tick documents to crawl or delete them.</span>' : ''}
                        </div>
                        <div class="space-y-2 mb-4" id="links-${attr(name)}">
                            ${rows || '<div class="text-center py-8 text-muted-foreground text-sm italic border-2 border-dashed border-border rounded-lg">No documents yet.</div>'}
                        </div>
                        ${i.status === 'archived' ? '<p class="text-sm text-muted-foreground">Archived by an older version, so its documents can\'t be changed. An owner can set it to Not in chat.</p>' : `
                        <div class="flex gap-2">
                            <input type="text" placeholder="Paste a link to add" id="newLink-${attr(name)}" class="flex-1 min-w-0 ${inputCls}" aria-label="New link URL">
                            ${newLinkProductHTML(`newLinkProduct-${name}`)}
                            <button type="button" class="${btnPrimary}" data-add-link>Add Link</button>
                        </div>
                        <p id="newLinkFlag-${attr(name)}" class="hidden mt-1.5 text-xs text-red-600" role="alert"></p>`}
                        ${nextStepsHTML(i, docs.total)}
                        ${pager(docs.total, docs.page, docs.per_page, 'docs')}
                    </div>
                </div>
                <div class="space-y-4">
                    <div id="findLinksCard">${findLinksHTML(i)}</div>
                    ${factsHTML(i)}
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
        box.querySelectorAll('[data-retire]').forEach(b => b.addEventListener('click', () => retireLink(name, b.dataset.retire)));
        box.querySelectorAll('[data-replace]').forEach(b => b.addEventListener('click', () => replaceLink(name, b.dataset.replace)));
        box.querySelectorAll('[data-page="docs"]').forEach(b => b.addEventListener('click', () => {
            S.docPage = Number(b.dataset.to);
            loadDetail();
        }));
        // The Find links card wires its own (wireFindLinks), as it redraws alone
        box.querySelectorAll('[data-review-proposals]').forEach(b => {
            if (b.closest('#findLinksCard')) return;
            b.addEventListener('click', () => {
                S.prop = { ...S.prop, esp: name, state: 'open', source: '', page: 1 };
                showAdminTab('proposals');
            });
        });
        wireFindLinks(i);
        wireProductPickers(box);
        if ($(`newLink-${name}`)) wireDuplicateLinkCheck($(`newLink-${name}`), name);
        box.querySelector('.new-link-product')?.addEventListener('change', () => {
            const flag = $(`newLinkFlag-${name}`);
            if (flag && flag.textContent === PICK_PRODUCT_MESSAGE) setLinkFlag(name, null);
        });
        box.querySelectorAll('.link-checkbox').forEach(cb => cb.addEventListener('change', updateGlobalBulkActions));
        updateGlobalBulkActions();

        $('intType').addEventListener('change', (e) => patch(name, { platform_type: e.target.value }, { flash: 'kind' }));
        box.querySelector('[data-keep-type]')?.addEventListener('click', () => patch(name, { platform_type: i.platform_type }, { flash: 'kind' }));
        box.querySelectorAll('[data-product]').forEach(cb => cb.addEventListener('change', () => {
            const products = [...box.querySelectorAll('[data-product]:checked')].map(x => x.dataset.product);
            patch(name, { products }, { flash: 'products' });
        }));
        box.querySelectorAll('[data-set-status]').forEach(b => b.addEventListener('click', () => {
            const status = b.dataset.setStatus;
            if (status === i.status) return;
            const question = status === 'active' ? `Put ${i.display_name} in chat? Everyone using the chat will be able to pick it.`
                : `Set ${i.display_name} to "Not in chat"?${i.status === 'active' ? ' People will no longer be able to pick it in chat.' : ''}`;
            if (!confirm(question)) return;
            patch(name, { status }, { sidebar: true });
        }));
    }

    // A page that keeps answering "not found": retire it (its search entries
    // go, the row stays, marked retired) or point it at the page's new address
    async function retireLink(name, url) {
        if (!confirm(`Retire this document?\n\n${url}\n\nThe AI stops using it and it isn't crawled again. You can bring it back by crawling it.`)) return;
        try {
            const data = await sendJSON('POST', `/admin/esp/${encodeURIComponent(name)}/retire`, { urls: [url] });
            if (data.skipped.length) alert(`Not retired: ${data.skipped.map(x => x.error).join('; ')}`);
        } catch (error) {
            alert(`Could not retire it: ${error.message}`);
        }
        loadESPManagement();
    }

    async function replaceLink(name, url) {
        const next = prompt(`The page's new address?\n\nIt gets the same product label and is crawled. The old one is retired once the new one is in the AI's search.\n\nOld: ${url}`, '');
        if (next === null || !next.trim()) return;
        try {
            const data = await sendJSON('POST', `/admin/esp/${encodeURIComponent(name)}/replace`, { old_url: url, new_url: next.trim() });
            alert(data.queued
                ? 'Added and queued for crawling. The old link is retired once the new one is in the AI\'s search.'
                : `Added.${data.warning ? ` ${data.warning}` : ' Tick it and press Crawl Selected:'} the old link is retired once the new one is in the AI's search.`);
            if (data.queued && window.AdminIntegrations) window.AdminIntegrations.watchCrawls();
        } catch (error) {
            alert(`Could not replace it: ${error.message}`);
        }
        loadESPManagement();
    }

    async function patch(name, body, { sidebar = false, flash = '' } = {}) {
        let saved = true;
        try {
            await sendJSON('PATCH', `/admin/integrations/${encodeURIComponent(name)}`, body);
            if (sidebar && typeof reloadSidebar === 'function') reloadSidebar();
        } catch (error) {
            saved = false;
            alert(`Could not save: ${error.message}`);
        }
        await loadDetail();
        if (saved && flash && S.open === name) flashSaved($('espManagement')?.querySelector(`[data-saved-for="${flash}"]`));
    }

    async function rename(i) {
        const next = prompt(`Rename "${i.display_name}":`, i.display_name);
        if (next === null || !next.trim() || next.trim() === i.display_name) return;
        await patch(i.name, { display_name: next.trim() }, { sidebar: i.status === 'active' });
    }

    // ==================== Find links ====================

    function whenText(value) {
        if (!value) return '';
        const d = new Date(value);
        return Number.isNaN(d.getTime()) ? String(value) : d.toLocaleString();
    }

    // Why no help articles were suggested, in words (HTML: the site is a link)
    function helpLineHTML(run) {
        if (run.model_skipped) return `Its help articles weren't looked for: ${run.model_problem === 'unavailable' ? "the AI didn't start (see the server log)" : "the AI key isn't set"}.${run.help_centre ? ` Its help site: ${siteLink(run.help_centre)}.` : ''}`;
        if (run.blocked) return `Its help site${run.help_centre ? ` (${siteLink(run.help_centre)})` : ''} blocks automatic reading: add its help articles yourself, labelled Shared.`;
        if (!run.help_centre) return "Its help site wasn't found: give its website below and run it again, or add its help articles yourself.";
        const p = run.help_problem || '';
        if (!p) return '';
        if (/accepted none/.test(p)) return `The articles found on ${siteLink(run.help_centre)} didn't fit: add the right ones yourself, labelled Shared.`;
        if (/no partner function/.test(p)) return `The AI found nothing in its guides to look up on ${siteLink(run.help_centre)}.`;
        if (/could not (list|check)/.test(p)) return "The AI didn't answer this time. Try again later.";
        if (/skipped/.test(p)) return 'Its help site is skipped on purpose (scripts/help_centres.json).';
        if (/could not be searched|show no text|refused|could not be read/.test(p)) return `Its help site (${siteLink(run.help_centre)}) couldn't be read automatically: add its help articles yourself, labelled Shared.`;
        return esc(p);
    }

    function runResultHTML(i, run) {
        const c = run.counts || {};
        const n = (run.added || []).length;
        const kinds = [
            c.yotpo_guides && plural(c.yotpo_guides, 'Yotpo guide', 'Yotpo guides'),
            c.partner_pages && plural(c.partner_pages, 'page of its own', 'pages of its own'),
            c.help_articles && plural(c.help_articles, 'help article', 'help articles')
        ].filter(Boolean);
        const lines = [
            run.by_name && (c.yotpo_guides
                ? "yotpo.com doesn't list it, so Yotpo's guides were matched by its name: check each is about this platform."
                : "yotpo.com doesn't list it, and no Yotpo guide has its name in the address."),
            run.matched_on_yotpo_com && run.matched_on_yotpo_com.length && 'Found on yotpo.com under this name; the next yotpo.com import links it here.',
            c.already && `${plural(c.already, 'link it found was', 'links it found were')} already documents or suggested before (rejected ones stay rejected).`,
            (run.gone || []).length && `${plural(run.gone.length, 'Yotpo guide linked from yotpo.com is', 'Yotpo guides linked from yotpo.com are')} gone.`,
            run.sitemap_read === false && "support.yotpo.com's list of guides couldn't be read, so guides weren't searched by name.",
            !c.help_articles && helpLineHTML(run)
        ].filter(Boolean);
        return `
            <p class="text-sm text-card-foreground">${n ? `Found ${plural(n, 'new link', 'new links')}: ${esc(kinds.join(', '))}.` : 'Nothing new found.'}</p>
            ${i.open_proposals ? `<button type="button" class="mt-2 ${btnPrimary} !px-3 !py-1 w-full" data-review-proposals>Review ${plural(i.open_proposals, 'suggested link', 'suggested links')} →</button>` : ''}
            ${lines.length ? `<ul class="mt-2 space-y-1">${lines.map(l => `<li class="text-xs text-muted-foreground">${l}</li>`).join('')}</ul>` : ''}`;
    }

    function findLinksHTML(i) {
        const run = i.find_links;
        const running = run && run.state === 'running';
        let body;
        if (!run) {
            body = '<p class="text-xs text-muted-foreground">Not run yet.</p>';
        } else if (running) {
            body = `
                <p class="flex items-center gap-2 text-sm text-card-foreground" role="status">
                    <svg class="animate-spin h-4 w-4 shrink-0" viewBox="0 0 24 24" fill="none" aria-hidden="true"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path></svg>
                    ${esc(FIND_STEPS[run.step === 'help_site' && run.model_skipped ? 'help_site_no_ai' : run.step] || 'Working…')}
                </p>
                <p class="text-xs text-muted-foreground mt-1">Takes a minute or two. You can leave this page: it carries on.</p>`;
        } else if (run.state === 'done') {
            body = runResultHTML(i, run);
        } else if (run.state === 'interrupted') {
            body = '<p class="text-xs text-red-700">The last search was cut short (the server restarted). Run it again.</p>';
        } else {
            body = `<p class="text-xs text-red-700">The last search stopped with an error: ${esc(run.error || 'unknown')}.</p>`;
        }
        const who = run && run.requested_by ? (run.requested_by === 'admin password' ? 'an admin' : run.requested_by) : '';
        const when = run && !running ? `<p class="text-[11px] text-muted-foreground mt-2">Last run ${esc(whenText(run.finished_at || run.started_at))}${who ? ` by ${esc(who)}` : ''}</p>` : '';
        const form = i.status === 'archived' || running ? '' : `
            <div class="mt-3 pt-3 border-t border-border space-y-2">
                <input type="text" id="findWebsite" value="${attr((run && run.website) || '')}" maxlength="500" placeholder="Its website or help site (optional)" class="w-full ${inputCls}" aria-label="Its website or help site (optional)">
                <button type="button" class="${btnOutline} w-full !py-2" data-find-links>${run ? 'Find links again' : 'Find links'}</button>
                <p class="text-[11px] text-muted-foreground">Uses the chat's Gemini credit for its help articles.</p>
            </div>`;
        return `
            <div class="${card}">
                <div class="flex items-center gap-1.5 text-sm font-semibold text-card-foreground mb-2">Find links ${info(HELP.findLinks)}</div>
                ${body}${when}${form}
            </div>`;
    }

    // Only the card redraws while a search runs, so nothing else on the page moves
    function renderFindCard(i) {
        const holder = $('findLinksCard');
        if (!holder) return;
        holder.innerHTML = findLinksHTML(i);
        wireFindLinks(i);
    }

    function wireFindLinks(i) {
        const holder = $('findLinksCard');
        if (!holder) return;
        holder.querySelector('[data-find-links]')?.addEventListener('click', () => startFindLinks(i));
        holder.querySelectorAll('[data-review-proposals]').forEach(b => b.addEventListener('click', () => {
            S.prop = { ...S.prop, esp: i.name, state: 'open', source: '', page: 1 };
            showAdminTab('proposals');
        }));
        $('findWebsite')?.addEventListener('keydown', (e) => { if (e.key === 'Enter') startFindLinks(i); });
        stopFindPoll();
        if (i.find_links && i.find_links.state === 'running') {
            S.findTimer = setTimeout(() => pollFindLinks(i.name), FIND_POLL_MS);
        }
    }

    function stopFindPoll() {
        clearTimeout(S.findTimer);
        S.findTimer = null;
    }

    async function startFindLinks(i) {
        const btn = $('findLinksCard')?.querySelector('[data-find-links]');
        if (!btn || btn.disabled) return;     // a second Enter while it starts
        btn.disabled = true;
        const website = ($('findWebsite')?.value || '').trim();
        try {
            const data = await sendJSON('POST', `/admin/integrations/${encodeURIComponent(i.name)}/find-links`, { website });
            if (S.open !== i.name) return;
            i.find_links = data.run;
            renderFindCard(i);
        } catch (error) {
            alert(`Could not start Find links: ${error.message}`);
            btn.disabled = false;
        }
    }

    async function pollFindLinks(name) {
        S.findTimer = null;
        if (S.open !== name || !S.detail) return;
        // Not on screen (panel closed, another tab): stop; opening the
        // integration again starts it over
        if ($('espManagementTab')?.classList.contains('hidden') || $('adminModal')?.classList.contains('hidden')) return;
        let run;
        try {
            run = (await getJSON(`/admin/integrations/${encodeURIComponent(name)}/find-links`)).run;
        } catch (error) {
            // A passing error is tried again a few times; then the page says what it last knew
            S.findErrors = (S.findErrors || 0) + 1;
            if (S.findErrors < 5) S.findTimer = setTimeout(() => pollFindLinks(name), FIND_POLL_MS * 2);
            return;
        }
        S.findErrors = 0;
        if (S.open !== name) return;
        if (run && run.state === 'running') {
            S.detail.find_links = run;
            renderFindCard(S.detail);
        } else {
            // Finished: its suggestions change the page's counts
            loadDetail();
        }
    }

    // ==================== Add integration ====================

    function addDialog() {
        return $('addIntegrationModal');
    }

    function setAddError(text) {
        const el = $('addIntegrationError');
        if (!el) return;
        el.textContent = text || '';
        el.classList.toggle('hidden', !text);
    }

    function markKinds() {
        document.querySelectorAll('#addIntegrationKinds label').forEach(l => {
            const on = l.querySelector('input').checked;
            l.classList.toggle('border-primary', on);
            l.classList.toggle('bg-primary/5', on);
            l.classList.toggle('border-input', !on);
        });
    }

    function openAddDialog() {
        const modal = addDialog();
        if (!modal) return;
        const kinds = $('addIntegrationKinds');
        // Nothing chosen in advance: the kind is the admin's decision (I10)
        kinds.innerHTML = PLATFORM_TYPES.map(t => `
            <label class="flex items-start gap-2.5 p-3 rounded-lg border border-input bg-background hover:border-primary cursor-pointer transition-colors">
                <input type="radio" name="addIntegrationKind" value="${t}" class="mt-0.5 shrink-0">
                <span class="min-w-0">
                    <span class="block text-sm font-medium text-card-foreground">${esc(TYPE_NAMES[t])}</span>
                    <span class="block text-xs text-muted-foreground mt-0.5">${esc(KIND_HELP[t])}</span>
                </span>
            </label>`).join('');
        kinds.querySelectorAll('input').forEach(r => r.addEventListener('change', () => { markKinds(); setAddError(''); }));
        $('addIntegrationName').value = '';
        $('addIntegrationWebsite').value = '';
        setAddError('');
        $('addIntegrationSubmit').disabled = false;
        $('addIntegrationSubmit').textContent = 'Add and find links';
        modal.classList.remove('hidden');
        $('addIntegrationName').focus();
    }

    function closeAddDialog() {
        addDialog()?.classList.add('hidden');
        $('addIntegrationBtn')?.focus();
    }

    async function submitAddDialog(e) {
        e.preventDefault();
        const name = $('addIntegrationName').value.trim();
        const kind = document.querySelector('input[name="addIntegrationKind"]:checked')?.value || '';
        const website = $('addIntegrationWebsite').value.trim();
        if (!name) {
            setAddError('Give it a name.');
            $('addIntegrationName').focus();
            return;
        }
        // No integration without its kind of platform (I10)
        if (!kind) {
            setAddError("Pick its kind of platform: an integration can't be added without one.");
            return;
        }
        const submit = $('addIntegrationSubmit');
        submit.disabled = true;
        submit.textContent = 'Adding…';
        let data;
        try {
            // display_name keeps the name as typed (HubSpot, dotdigital)
            data = await sendJSON('POST', '/admin/esp/create', { name, display_name: name, platform_type: kind, website, find_links: true });
        } catch (error) {
            setAddError(error.message);
            submit.disabled = false;
            submit.textContent = 'Add and find links';
            return;
        }
        closeAddDialog();
        if (data.in_chat && typeof reloadSidebar === 'function') reloadSidebar();
        openIntegration(data.esp.name);
        if (data.find_links_error) alert(`${data.esp.display_name} was added, but Find links didn't start: ${data.find_links_error}`);
    }

    function wireAddDialog() {
        const modal = addDialog();
        if (!modal || modal.dataset.wired) return;
        modal.dataset.wired = '1';
        $('addIntegrationBtn')?.addEventListener('click', openAddDialog);
        $('addIntegrationForm').addEventListener('submit', submitAddDialog);
        modal.querySelectorAll('[data-close-add]').forEach(b => b.addEventListener('click', closeAddDialog));
        modal.addEventListener('mousedown', (e) => { if (e.target === modal) closeAddDialog(); });
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && !modal.classList.contains('hidden')) {
                e.stopImmediatePropagation();
                closeAddDialog();
            }
        });
    }

    // ==================== Proposals ====================

    function headerHint(p) {
        if (p.source === 'mechanics') {
            return `${p.partner_function ? `Explains <span class="font-medium text-card-foreground">${esc(p.partner_function)}</span>: ` : ''}${esc(p.reason || p.note || '')}`;
        }
        return esc(noteText(p.note));
    }

    function proposalRowHTML(p) {
        const P = S.prop;
        const open = p.state === 'open';
        const label = P.labels[p.id] || '';
        const prefilled = label && label === p.suggested_label && !P.touched.has(p.id);
        const tone = !label ? 'border-amber-400 text-amber-800' : prefilled ? 'border-dashed border-ring' : 'border-input';
        const said = p.suggested_label === 'loyalty' || p.suggested_label === 'reviews'
            ? ` The page says it is about ${PRODUCT_NAMES[p.suggested_label]}.` : '';
        const pickerTip = `${PRODUCT_LABEL_HELP}${said}${prefilled ? ' Filled in for you (dashed): check it.' : ''}`;
        const picker = `
            <select class="w-28 shrink-0 text-xs px-2 py-1 rounded bg-background cursor-pointer border ${tone}" data-prop-label="${attr(p.id)}" aria-label="Yotpo product for ${attr(p.url)}" title="${attr(pickerTip)}">
                <option value="" ${!label ? 'selected' : ''} disabled>Pick product</option>
                ${Object.entries(PRODUCT_LABELS).map(([v, t]) => `<option value="${v}" ${label === v ? 'selected' : ''}>${t}</option>`).join('')}
            </select>`;
        const decided = open ? '' : `<div class="pl-6 mt-1.5 text-xs text-muted-foreground">${esc(p.state === 'approved' ? 'Approved' : 'Rejected')} by ${esc(p.decided_by || '—')}${p.decided_at ? ` · ${esc(new Date(String(p.decided_at).replace(' ', 'T')).toLocaleString())}` : ''}${p.decision_note ? ` · “${esc(p.decision_note)}”` : ''}</div>`;
        return `
            <div class="p-2 bg-background rounded-lg border ${P.sel.has(p.id) ? 'border-primary' : 'border-border'} transition-colors">
                <div class="flex flex-wrap sm:flex-nowrap items-center gap-2">
                    ${open ? `<input type="checkbox" class="w-4 h-4 rounded border-input cursor-pointer shrink-0" data-prop-sel="${attr(p.id)}" ${P.sel.has(p.id) ? 'checked' : ''} aria-label="Select ${attr(p.url)}">` : ''}
                    ${p.source === 'catalog' ? '' : `<span class="text-xs font-medium px-2 py-0.5 rounded bg-slate-100 text-slate-700 uppercase tracking-wide whitespace-nowrap">${esc(SOURCE_NAMES[p.source] || p.source)}</span>`}
                    <div class="flex-1 min-w-0">
                        <a href="${attr(p.url)}" target="_blank" rel="noopener" class="block text-sm text-foreground hover:underline truncate" title="${attr(p.url)}">${esc(p.title || pageName(p.url))}</a>
                        <span class="block text-xs text-muted-foreground truncate" title="${attr([p.url, p.reason || p.note].filter(Boolean).join(' · '))}">${[esc(shortUrl(p.url)), headerHint(p)].filter(Boolean).join(' · ')}</span>
                    </div>
                    ${open ? `${picker}
                        <button type="button" class="px-3 py-1 rounded text-xs font-medium bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-40 disabled:cursor-not-allowed" data-prop-approve="${attr(p.id)}" ${label ? '' : 'disabled title="Pick its product first"'}>Approve</button>
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
            const what = { open: 'Nothing to review', approved: 'Nothing approved yet', rejected: 'Nothing rejected yet' }[S.prop.state];
            return `<div class="text-center py-8 text-muted-foreground text-sm italic border-2 border-dashed border-border rounded-lg">${esc(what)}${S.prop.source ? ` from "${esc(SOURCE_NAMES[S.prop.source] || S.prop.source)}"` : ''}.</div>`;
        }
        return groups.map(key => {
            const info = data.integrations[key] || { display_name: 'No integration', status: '', products: [], functions: [] };
            const rows = byEsp[key];
            const openIds = rows.filter(p => p.state === 'open').map(p => p.id);
            const allSelected = openIds.length && openIds.every(id => S.prop.sel.has(id));
            const functions = info.functions && info.functions.length && rows.some(p => p.source === 'mechanics')
                ? `<p class="text-xs text-muted-foreground mb-3" ${tip("The features its Yotpo guide uses. The yotpo.com import searched its help site for articles on them.")}>Help articles on: ${esc(info.functions.map(f => f.name).join(', '))}${info.help_centre ? ` · ${siteLink(info.help_centre)}` : ''}</p>` : '';
            return `
                <div class="${card}">
                    <div class="flex flex-wrap items-center gap-2 mb-3">
                        ${openIds.length ? `<input type="checkbox" class="w-4 h-4 rounded border-input cursor-pointer" data-prop-group="${attr(key)}" ${allSelected ? 'checked' : ''} aria-label="Select all for ${attr(info.display_name)}">` : ''}
                        <h4 class="text-base font-semibold text-card-foreground">${esc(info.display_name)}</h4>
                        ${info.status ? statusPill(info.status) : ''}
                        ${info.products.length ? `<span class="text-xs text-muted-foreground">works with ${esc(productsText(info.products))}</span>` : ''}
                        ${key ? `<button type="button" class="ml-auto text-sm text-muted-foreground hover:text-foreground" data-open-esp="${attr(key)}">Open →</button>` : ''}
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
                <h3 class="text-lg font-semibold text-card-foreground mb-1">Help Articles to Add by Hand</h3>
                <p class="text-sm text-muted-foreground mb-4">The yotpo.com import couldn't suggest these platforms' own help. Add it on each one's page, labelled Shared.</p>
                <div class="${card} space-y-2">
                    ${rows.map(r => `
                        <div class="flex flex-wrap sm:flex-nowrap items-center gap-2 p-2 bg-background rounded-lg border border-border">
                            <span class="font-medium text-sm text-card-foreground w-40 shrink-0 truncate">${esc(r.display_name)}</span>
                            <span class="flex-1 min-w-0 text-xs text-muted-foreground truncate" title="${attr(r.help_centre || '')}">${esc(NEEDS_PERSON[r.kind] || '')}${r.help_centre ? `: ${siteLink(r.help_centre)}` : ''}</span>
                            <button type="button" class="${btnOutline} !text-xs" data-open-esp="${attr(r.esp)}">Open</button>
                        </div>`).join('')}
                </div>
            </div>`;
    }

    // support.yotpo.com's sitemap, read monthly (C1.3): new articles
    // nobody holds yet, and held ones that vanished. Never matched to an
    // integration automatically: names collide with ordinary words.
    function sitemapHTML(sm) {
        if (!sm) return '';
        const run = sm.last_run;
        const when = run && (run.finished_at || run.started_at);
        const nowBtn = isOwner() ? `<button type="button" class="${btnOutline} !text-xs" data-sitemap-now>Read it now</button>` : '';
        const head = `
            <div class="flex flex-wrap items-center gap-2 mb-1">
                <h3 class="flex items-center gap-1.5 text-lg font-semibold text-card-foreground">New on support.yotpo.com ${info(HELP.sitemap)}</h3>
                <span class="flex-1"></span>${nowBtn}
            </div>`;
        if (!run) {
            return `<div class="border-b border-border pb-6 mb-6">${head}
                <p class="text-sm text-muted-foreground">Not read yet. ${sm.scheduled ? 'It is read on the 1st of each month at 03:17 UTC.' : 'On this server it is only read when an owner presses Read it now.'}</p></div>`;
        }
        const unheld = (sm.new || []).filter(x => !x.document && !x.proposal);
        const gone = (sm.vanished || []).filter(x => x.document && !x.document.retired);
        const status = !run.ok
            ? `The last read failed (${esc(whenText(when))}): ${esc(run.problem || 'unknown')}.`
            : run.first_read
            ? `First read ${esc(whenText(when))}: ${esc(String(run.urls))} articles recorded. ${run.not_queued ? `${esc(String(run.not_queued))} of our guides changed since their last crawl; they weren't crawled again (the first read only records). Crawl them by hand if you want them current now.` : 'From the next read on, our guides Yotpo changes are crawled again.'}`
            : `Last read ${esc(whenText(when))}: ${esc(String(run.urls))} articles, ${esc(String(run.changed))} changed (${esc(String(run.queued))} of our guides queued to crawl again).`;
        const item = (x, extra) => `
            <li class="flex flex-wrap sm:flex-nowrap items-center gap-2 p-2 bg-background rounded-lg border border-border">
                <a href="${attr(x.url)}" target="_blank" rel="noopener" class="flex-1 min-w-0 text-sm text-foreground hover:underline truncate" title="${attr(x.url)}">${esc(pageName(x.url))}</a>
                ${extra}
            </li>`;
        const list = (rows, render) => rows.length ? `<ul class="space-y-2">${rows.slice(0, 50).map(render).join('')}</ul>${rows.length > 50 ? `<p class="text-xs text-muted-foreground mt-2">and ${rows.length - 50} more</p>` : ''}` : '';
        return `
            <div class="border-b border-border pb-6 mb-6">
                ${head}
                <p class="text-sm text-muted-foreground mb-4">${status}${run.problem && run.ok ? ` ${esc(run.problem)}.` : ''}</p>
                <h4 class="text-sm font-semibold text-card-foreground mb-2">New articles since ${esc(sm.since)} (${unheld.length})</h4>
                ${unheld.length ? `<p class="text-xs text-muted-foreground mb-2">Nobody has them yet. If one is an integration's guide, open that integration and add it there.</p>` : '<p class="text-xs text-muted-foreground mb-4">None.</p>'}
                ${list(unheld, x => item(x, `<span class="text-xs text-muted-foreground whitespace-nowrap">${esc(whenText(x.when))}</span>`))}
                ${gone.length ? `
                    <h4 class="text-sm font-semibold text-card-foreground mt-4 mb-2">Our guides gone from the sitemap (${gone.length})</h4>
                    <p class="text-xs text-muted-foreground mb-2">Yotpo removed or moved them. Open the integration to replace or retire each.</p>
                    ${list(gone, x => item(x, `<button type="button" class="${btnOutline} !text-xs" data-open-esp="${attr(x.document.esp)}">${esc(x.document.display_name)}</button>`))}` : ''}
            </div>`;
    }

    function lastImportHTML(last) {
        if (!last) {
            return `
                <div>
                    <h3 class="text-lg font-semibold text-card-foreground mb-1">The yotpo.com import</h3>
                    <p class="text-sm text-muted-foreground">Reads yotpo.com/integrations, adds missing integrations and suggests their links. Not run yet. Leo runs it (<code class="font-mono">scripts/import_catalog.py</code>).</p>
                </div>`;
        }
        const c = last.counts || {};
        return `
            <div>
                <h3 class="text-lg font-semibold text-card-foreground mb-1">The yotpo.com import</h3>
                <p class="text-sm text-muted-foreground mb-4">Reads yotpo.com/integrations, adds missing integrations and suggests the links above. Last run ${esc(last.applied_at || '')}: ${esc(String(last.cards || 0))} pages read, ${esc(String(c.created || 0))} integrations added, ${esc(String(c.proposals || 0))} links suggested.</p>
                <details class="${card}">
                    <summary class="text-sm text-muted-foreground hover:text-foreground cursor-pointer">Technical report (for developers)</summary>
                    <pre class="mt-3 text-xs font-mono bg-background border border-border rounded-lg p-3 overflow-x-auto whitespace-pre-wrap leading-relaxed max-h-[32rem]">${esc(last.report || '')}</pre>
                </details>
            </div>`;
    }

    async function loadProposals() {
        const box = $('proposalsAdmin');
        if (!box) return;
        const P = S.prop;
        let data, imp, sm;
        try {
            [data, imp, sm] = await Promise.all([
                getJSON(`/admin/proposals?${qs({ state: P.state, source: P.source, esp: P.esp, page: P.page })}`),
                getJSON('/admin/catalog-import'),
                getJSON('/admin/sitemap-changes').catch(() => null)
            ]);
        } catch (error) {
            box.innerHTML = `<div class="text-sm text-red-700">Could not load the suggested links: ${esc(error.message)}</div>`;
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
                <h3 class="flex items-center gap-1.5 text-lg font-semibold text-card-foreground mb-1">Suggested Links ${info(HELP.suggested)}</h3>
                <p class="text-sm text-muted-foreground mb-4">Open each link, pick its product, then Approve. Rejected links aren't suggested again.</p>
                <div class="flex flex-wrap items-center gap-2 mb-4">
                    <select class="${inputCls}" data-prop-filter="state" aria-label="Which links">
                        ${[['open', 'To review'], ['approved', 'Approved'], ['rejected', 'Rejected']].map(([s, t]) => `<option value="${s}" ${P.state === s ? 'selected' : ''}>${t} (${data.counts[s] || 0})</option>`).join('')}
                    </select>
                    <select class="${inputCls}" data-prop-filter="source" aria-label="Where they came from">
                        <option value="">From anywhere</option>
                        ${Object.entries(SOURCE_NAMES).map(([v, t]) => `<option value="${v}" ${P.source === v ? 'selected' : ''}>${t} (${data.sources[v] || 0})</option>`).join('')}
                    </select>
                    ${P.esp ? `<span class="inline-flex items-center gap-2 text-sm bg-muted px-3 py-1 rounded-full">${esc(espName)} <button type="button" class="text-muted-foreground hover:text-foreground" data-clear-esp aria-label="Show every integration">✕</button></span>` : ''}
                    <span class="flex-1"></span>
                    <span id="propBulk" class="flex flex-wrap items-center gap-2"></span>
                </div>
                <div class="space-y-4" id="propGroups">${proposalGroupsHTML(data)}</div>
                ${pager(data.total, data.page, data.per_page, 'props')}
            </div>
            ${P.state === 'open' && !P.esp ? needsPersonHTML(imp.needs_person) : ''}
            ${P.state === 'open' && !P.esp ? sitemapHTML(sm) : ''}
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
            ${needLabel ? `<span class="text-xs text-amber-800">${needLabel} still need${needLabel === 1 ? 's' : ''} a product picked</span>` : ''}
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
        box.querySelector('[data-sitemap-now]')?.addEventListener('click', async (e) => {
            e.target.disabled = true;
            try {
                await sendJSON('POST', '/admin/sitemap-refresh', {});
                alert("Reading support.yotpo.com's sitemap. It takes a minute or two: come back to this tab to see it.");
            } catch (error) {
                alert(`Could not start it: ${error.message}`);
                e.target.disabled = false;
            }
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
            let message = `Approved ${data.approved} of ${items.length}. They are now documents of their integration.`;
            if (queued) message += ` ${queued} will be crawled automatically.`;
            else if (data.approved) message += ' Open the integration and press Crawl Selected to crawl them.';
            if (problems.length) message += `\n\nNeeds a look:\n${problems.join('\n')}`;
            alert(message);
        } catch (error) {
            alert(`Could not approve: ${error.message}`);
        }
        loadProposals();
    }

    async function reject(ids) {
        const note = prompt(`Reject ${plural(ids.length, 'link', 'links')}? ${ids.length === 1 ? 'It' : 'They'} won't be suggested again.\n\nWhy? (optional, for whoever looks later)`, '');
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

    wireTips();
    wireAddDialog();
    window.AdminIntegrations = { reload, loadProposals, watchCrawls, openIntegration };
})();
