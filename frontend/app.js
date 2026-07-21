// Auto-detect API URL based on environment
const API_URL = window.location.hostname === 'localhost'
    ? 'http://localhost:5001/api'
    : `${window.location.protocol}//${window.location.host}/api`;

let selectedESP = 'klaviyo';
let adminPassword = '';
let sessionId = null;
let sessionStartTime = null;

// Store conversation history per ESP in session storage
let conversationHistories = {
    'klaviyo': [],
    'dotdigital': [],
    'attentive': [],
    'other/webhook': []
};

// Load histories from session storage
const loadHistories = () => {
    const stored = sessionStorage.getItem('espConversationHistories');
    if (stored) {
        conversationHistories = JSON.parse(stored);
    }
};

// Save histories to session storage
const saveHistories = () => {
    sessionStorage.setItem('espConversationHistories', JSON.stringify(conversationHistories));
};

// Get current conversation history
const getCurrentHistory = () => {
    return conversationHistories[selectedESP] || [];
};

// Add to current conversation history
const addToHistory = (role, content) => {
    if (!conversationHistories[selectedESP]) {
        conversationHistories[selectedESP] = [];
    }
    conversationHistories[selectedESP].push({ role, content, timestamp: new Date().toISOString() });
    saveHistories();
};

// Clear current ESP history
const clearCurrentHistory = () => {
    conversationHistories[selectedESP] = [];
    saveHistories();
};

// Initialize session tracking
async function initializeSession() {
    try {
        const response = await fetch(`${API_URL}/session/init`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        const data = await response.json();
        sessionId = data.session_id;
        sessionStartTime = Date.now();
        console.log('Session initialized:', sessionId);
    } catch (error) {
        console.error('Error initializing session:', error);
    }
}

// End session on page unload
window.addEventListener('beforeunload', () => {
    if (sessionId) {
        navigator.sendBeacon(`${API_URL}/session/end`, JSON.stringify({ session_id: sessionId }));
    }
});

// Track ESP selection
async function trackESPSelection(esp) {
    if (!sessionId) return;

    try {
        await fetch(`${API_URL}/esp/select`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_id: sessionId, esp })
        });
    } catch (error) {
        console.error('Error tracking ESP selection:', error);
    }
}

// Initialize
loadHistories();
initializeSession();

// DOM Elements
const chatMessages = document.getElementById('chatMessages');
const messageInput = document.getElementById('messageInput');
const sendBtn = document.getElementById('sendBtn');
const feedbackBtn = document.getElementById('feedbackBtn');
const adminBtn = document.getElementById('adminBtn');
const feedbackModal = document.getElementById('feedbackModal');
const adminModal = document.getElementById('adminModal');
const closeFeedback = document.getElementById('closeFeedback');
const closeAdmin = document.getElementById('closeAdmin');

// Initialize ESP buttons
function initializeESPButtons() {
    const espButtons = document.querySelectorAll('.esp-item');
    const espHistoryButtons = document.querySelectorAll('.esp-history-btn');

    // ESP Selection
    espButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            // Update active state on button groups
            document.querySelectorAll('.esp-button-group').forEach(g => g.classList.remove('active'));
            btn.parentElement.classList.add('active');

            // Update button styling
            document.querySelectorAll('.esp-item').forEach(item => {
                item.classList.remove('bg-primary', 'text-primary-foreground', 'border-primary', 'hover:bg-primary', 'hover:text-primary-foreground');
                item.classList.add('bg-transparent', 'text-sidebar-foreground', 'border-sidebar-border', 'hover:bg-sidebar-accent', 'hover:text-sidebar-accent-foreground');
            });
            btn.classList.remove('bg-transparent', 'text-sidebar-foreground', 'border-sidebar-border', 'hover:bg-sidebar-accent', 'hover:text-sidebar-accent-foreground');
            btn.classList.add('bg-primary', 'text-primary-foreground', 'border-primary', 'hover:bg-primary', 'hover:text-primary-foreground');

            selectedESP = btn.dataset.esp;

            // Track ESP selection
            trackESPSelection(selectedESP);

            // Show welcome message for current ESP
            const espName = btn.textContent;
            const isOtherWebhook = selectedESP === 'other/webhook';
            const welcomeText = isOtherWebhook
                ? "Ask me anything about Yotpo's Loyalty & Referrals API and Webhook integrations. I draw from Yotpo's official API and Webhook documentation to help you build custom integrations, set up event listeners, and leverage our developer resources. If something isn't working as expected, please use the Feedback button to let us know."
                : `Ask me anything about setting up loyalty campaigns and flows in ${espName}. I draw from both Yotpo's loyalty expertise and ${espName}'s official resources to provide step-by-step guidance tailored to your needs. If something isn't working as expected, please use the Feedback button to let us know.`;

            chatMessages.innerHTML = `
                <div class="max-w-4xl mx-auto">
                    <div class="yotpo-gradient rounded-2xl p-8 shadow-sm gradient-intro" id="gradientIntro">
                        <h2 class="yotpo-heading text-3xl font-bold mb-3 text-white">Yotpo ${isOtherWebhook ? 'API & Webhooks' : 'x ' + espName}</h2>
                        <p class="text-white/95 leading-relaxed">${welcomeText}</p>
                    </div>
                </div>
            `;
        });
    });

    // History buttons
    espHistoryButtons.forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation(); // Prevent ESP selection
            const esp = btn.dataset.esp;
            showHistory(esp);
        });
    });
}

// Reload sidebar ESPs dynamically
async function reloadSidebar() {
    try {
        const response = await fetch(`${API_URL}/admin/esps`);
        const data = await response.json();

        const espList = document.getElementById('espList');
        espList.innerHTML = '';

        // If no ESPs exist, show a message
        if (!data.esps || data.esps.length === 0) {
            espList.innerHTML = '<div class="text-muted-foreground/50 p-4 text-sm">No ESPs found. Add one in the admin panel.</div>';
            return;
        }

        // Set first ESP as selected if none is selected
        let hasSelectedESP = false;
        for (const esp of data.esps) {
            const espValue = esp.name.replace('_', '/');
            if (espValue === selectedESP) {
                hasSelectedESP = true;
                break;
            }
        }

        if (!hasSelectedESP) {
            // Auto-select first ESP
            const firstESP = data.esps[0];
            selectedESP = firstESP.name.replace('_', '/');
        }

        for (const esp of data.esps) {
            const displayName = esp.display_name || esp.name;
            const espValue = esp.name.replace('_', '/');

            // Initialize conversation history for new ESP if needed
            if (!conversationHistories[espValue]) {
                conversationHistories[espValue] = [];
            }

            const isActive = espValue === selectedESP;
            const buttonGroup = document.createElement('div');
            buttonGroup.className = 'esp-button-group';
            if (isActive) {
                buttonGroup.classList.add('active');
            }

            buttonGroup.innerHTML = `
                <button class="esp-item px-3 py-2 text-sm font-medium transition-colors rounded-lg border ${
                    isActive
                    ? 'bg-primary text-primary-foreground border-primary hover:bg-primary hover:text-primary-foreground'
                    : 'bg-transparent text-sidebar-foreground border-sidebar-border hover:bg-sidebar-accent hover:text-sidebar-accent-foreground'
                }" data-esp="${espValue}">${displayName}</button>
                <button class="esp-history-btn flex items-center justify-center bg-sidebar-accent text-sidebar-accent-foreground hover:bg-primary hover:text-primary-foreground transition-colors" data-esp="${espValue}" title="View conversation history">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="12" cy="12" r="10"></circle>
                        <polyline points="12 6 12 12 16 14"></polyline>
                    </svg>
                </button>
            `;

            espList.appendChild(buttonGroup);
        }

        // Re-initialize button listeners
        initializeESPButtons();

        // Update welcome message for selected ESP
        const selectedESPData = data.esps.find(esp => esp.name.replace('_', '/') === selectedESP);
        if (selectedESPData) {
            const displayName = selectedESPData.display_name || selectedESPData.name;
            const isOtherWebhook = selectedESP === 'other/webhook';
            const welcomeText = isOtherWebhook
                ? "Ask me anything about Yotpo's Loyalty & Referrals API and Webhook integrations. I draw from Yotpo's official API and Webhook documentation to help you build custom integrations, set up event listeners, and leverage our developer resources. If something isn't working as expected, please use the Feedback button to let us know."
                : `Ask me anything about setting up loyalty campaigns and flows in ${displayName}. I draw from both Yotpo's loyalty expertise and ${displayName}'s official resources to provide step-by-step guidance tailored to your needs. If something isn't working as expected, please use the Feedback button to let us know.`;

            chatMessages.innerHTML = `
                <div class="max-w-4xl mx-auto">
                    <div class="yotpo-gradient rounded-2xl p-8 shadow-sm gradient-intro" id="gradientIntro">
                        <h2 class="yotpo-heading text-3xl font-bold mb-3 text-white">Yotpo ${isOtherWebhook ? 'API & Webhooks' : 'x ' + displayName}</h2>
                        <p class="text-white/95 leading-relaxed">${welcomeText}</p>
                    </div>
                </div>
            `;
        }

    } catch (error) {
        console.error('Error reloading sidebar:', error);
    }
}

// Initialize on page load - load ESPs from backend
reloadSidebar();

// Send Message
async function sendMessage() {
    const message = messageInput.value.trim();
    if (!message) return;

    // Add user message to chat
    addMessage('user', message);
    messageInput.value = '';
    sendBtn.disabled = true;

    // Add loading indicator
    const loadingId = addLoading();

    try {
        // Normalize ESP name for API (other/webhook -> other_webhook)
        const espNormalized = selectedESP.replace('/', '_');

        const response = await fetch(`${API_URL}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message,
                esp: espNormalized,
                history: getCurrentHistory(),
                session_id: sessionId
            })
        });

        const data = await response.json();

        // Remove loading
        removeLoading(loadingId);

        if (data.error) {
            addMessage('assistant', `Error: ${data.error}`);
        } else {
            addMessage('assistant', data.response);

            // Save to conversation history
            addToHistory('user', message);
            addToHistory('assistant', data.response);
        }
    } catch (error) {
        removeLoading(loadingId);
        addMessage('assistant', `Error: ${error.message}`);
    }

    sendBtn.disabled = false;
    messageInput.focus();
}

function addMessage(role, content) {
    // Fade out and remove gradient intro on first user message
    if (role === 'user') {
        const gradientIntro = document.getElementById('gradientIntro');
        if (gradientIntro) {
            gradientIntro.classList.add('fade-out');
            setTimeout(() => {
                gradientIntro.remove();
            }, 500); // Match animation duration
        }
    }

    const messageDiv = document.createElement('div');
    messageDiv.className = `max-w-4xl mx-auto mb-4 flex gap-3 ${role === 'user' ? 'justify-end' : 'justify-start'}`;

    if (role === 'assistant') {
        // Add avatar for assistant - sized to match one-line message bubble height
        const avatarDiv = document.createElement('div');
        avatarDiv.className = 'flex-shrink-0 w-10 h-10 mt-1';
        avatarDiv.innerHTML = '<img src="yotpo-avatar.svg" alt="Yotpo" class="w-full h-full object-contain">';
        messageDiv.appendChild(avatarDiv);
    }

    const bubble = document.createElement('div');
    bubble.className = `relative ${
        role === 'user'
        ? 'max-w-3xl bg-primary text-primary-foreground rounded-2xl rounded-tr-sm'
        : 'max-w-4xl bg-card text-card-foreground border border-border rounded-2xl rounded-tl-sm'
    } p-4 shadow-sm`;

    const contentDiv = document.createElement('div');
    contentDiv.className = 'prose prose-xs max-w-none';

    // Render markdown for assistant messages, plain text for user
    if (role === 'assistant' && typeof marked !== 'undefined') {
        contentDiv.innerHTML = marked.parse(content);
    } else {
        contentDiv.textContent = content;
    }

    bubble.appendChild(contentDiv);

    // Create a wrapper for bubble and copy button for assistant messages
    if (role === 'assistant') {
        const bubbleWrapper = document.createElement('div');
        bubbleWrapper.className = 'flex flex-col gap-2';

        bubbleWrapper.appendChild(bubble);

        // Add copy button underneath the bubble
        const copyBtn = document.createElement('button');
        copyBtn.className = 'copy-btn flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors opacity-60 hover:opacity-100 pl-4';
        copyBtn.innerHTML = `
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="opacity-70">
                <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
            </svg>
            <span class="copy-text">Copy</span>
        `;
        copyBtn.addEventListener('click', async () => {
            try {
                // Clone the content to manipulate it
                const clone = contentDiv.cloneNode(true);

                // Strip font-family, font-size, color, and other styling attributes
                const elementsWithStyle = clone.querySelectorAll('*');
                elementsWithStyle.forEach(el => {
                    // Remove inline styles
                    el.removeAttribute('style');

                    // Remove class attributes that might contain styling
                    el.removeAttribute('class');

                    // Keep only semantic HTML tags (headings, bold, italic, lists, etc.)
                    // Remove div/span wrappers and replace with their content
                    if (el.tagName === 'DIV' || el.tagName === 'SPAN') {
                        const parent = el.parentNode;
                        while (el.firstChild) {
                            parent.insertBefore(el.firstChild, el);
                        }
                        parent.removeChild(el);
                    }
                });

                // Get cleaned HTML
                const cleanedHTML = clone.innerHTML;
                const plainText = contentDiv.textContent;

                // Create a ClipboardItem with cleaned HTML and plain text
                const clipboardItem = new ClipboardItem({
                    'text/html': new Blob([cleanedHTML], { type: 'text/html' }),
                    'text/plain': new Blob([plainText], { type: 'text/plain' })
                });

                await navigator.clipboard.write([clipboardItem]);

                const textSpan = copyBtn.querySelector('.copy-text');
                const originalText = textSpan.textContent;
                textSpan.textContent = 'Copied!';
                setTimeout(() => {
                    textSpan.textContent = originalText;
                }, 2000);
            } catch (error) {
                console.error('Failed to copy:', error);
                // Fallback to plain text if rich text copy fails
                try {
                    await navigator.clipboard.writeText(contentDiv.textContent);
                } catch (fallbackError) {
                    console.error('Fallback copy also failed:', fallbackError);
                }
            }
        });

        bubbleWrapper.appendChild(copyBtn);
        messageDiv.appendChild(bubbleWrapper);
    } else {
        messageDiv.appendChild(bubble);
    }

    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function addLoading() {
    const loadingDiv = document.createElement('div');
    const loadingId = `loading-${Date.now()}`;
    loadingDiv.id = loadingId;
    loadingDiv.className = 'max-w-4xl mx-auto mb-4 flex gap-3 justify-start';
    loadingDiv.innerHTML = `
        <div class="flex-shrink-0 w-10 h-10 mt-1">
            <img src="yotpo-avatar.svg" alt="Yotpo" class="w-full h-full object-contain">
        </div>
        <div class="bg-card text-card-foreground border border-border rounded-2xl rounded-tl-sm p-4 shadow-sm">
            <div class="flex gap-2">
                <div class="w-2 h-2 bg-primary rounded-full loading-dot"></div>
                <div class="w-2 h-2 bg-primary rounded-full loading-dot"></div>
                <div class="w-2 h-2 bg-primary rounded-full loading-dot"></div>
            </div>
        </div>
    `;
    chatMessages.appendChild(loadingDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    return loadingId;
}

function removeLoading(loadingId) {
    const loadingDiv = document.getElementById(loadingId);
    if (loadingDiv) loadingDiv.remove();
}

sendBtn.addEventListener('click', sendMessage);
messageInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

// Feedback Modal
feedbackBtn.addEventListener('click', () => {
    feedbackModal.classList.remove('hidden');
    document.getElementById('feedbackESP').value = selectedESP;
});

closeFeedback.addEventListener('click', () => {
    feedbackModal.classList.add('hidden');
});

document.getElementById('feedbackForm').addEventListener('submit', async (e) => {
    e.preventDefault();

    const formData = {
        email: document.getElementById('feedbackEmail').value,
        esp: document.getElementById('feedbackESP').value,
        rating: document.getElementById('feedbackRating').value,
        comments: document.getElementById('feedbackComments').value,
        session_id: sessionId
    };

    try {
        const response = await fetch(`${API_URL}/feedback`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData)
        });

        const data = await response.json();

        if (data.success) {
            alert('Thank you for your feedback!');
            feedbackModal.classList.add('hidden');
            document.getElementById('feedbackForm').reset();
        }
    } catch (error) {
        alert('Error submitting feedback: ' + error.message);
    }
});

// Admin Modal
adminBtn.addEventListener('click', () => {
    adminModal.classList.remove('hidden');
});

closeAdmin.addEventListener('click', () => {
    adminModal.classList.add('hidden');
});

document.getElementById('verifyAdmin').addEventListener('click', async () => {
    const password = document.getElementById('adminPassword').value;

    try {
        const response = await fetch(`${API_URL}/admin/verify`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ password })
        });

        const data = await response.json();

        if (data.valid) {
            adminPassword = password;
            document.getElementById('adminAuth').style.display = 'none';
            document.getElementById('adminPanel').style.display = 'block';
            initializeAdminTabs();
            // Load analytics by default (first tab)
            loadAnalytics();
        } else {
            alert('Invalid password');
        }
    } catch (error) {
        alert('Error verifying password: ' + error.message);
    }
});

function initializeAdminTabs() {
    const tabs = document.querySelectorAll('.admin-tab');
    const timeRangeSelect = document.getElementById('analyticsTimeRange');

    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const targetTab = tab.dataset.tab;

            // Update tab styles
            tabs.forEach(t => {
                t.classList.remove('active', 'border-primary', 'text-primary');
                t.classList.add('border-transparent', 'text-muted-foreground');
            });
            tab.classList.add('active', 'border-primary', 'text-primary');
            tab.classList.remove('border-transparent', 'text-muted-foreground');

            // Show/hide content
            document.querySelectorAll('.admin-tab-content').forEach(content => {
                content.classList.add('hidden');
            });

            if (targetTab === 'esp-management') {
                document.getElementById('espManagementTab').classList.remove('hidden');
                loadESPManagement();
            } else if (targetTab === 'usage-analytics') {
                document.getElementById('usageAnalyticsTab').classList.remove('hidden');
                loadAnalytics();
            } else if (targetTab === 'general-settings') {
                document.getElementById('generalSettingsTab').classList.remove('hidden');
                loadGeneralSettings();
            }
        });
    });

    // Time range change handler
    if (timeRangeSelect) {
        timeRangeSelect.addEventListener('change', () => {
            loadAnalytics();
        });
    }
}

function getCountryFlag(countryName) {
    // Map of country names to flag emojis
    const flagMap = {
        'United States': '🇺🇸',
        'USA': '🇺🇸',
        'United Kingdom': '🇬🇧',
        'UK': '🇬🇧',
        'Canada': '🇨🇦',
        'Australia': '🇦🇺',
        'Germany': '🇩🇪',
        'France': '🇫🇷',
        'Italy': '🇮🇹',
        'Spain': '🇪🇸',
        'Netherlands': '🇳🇱',
        'Belgium': '🇧🇪',
        'Switzerland': '🇨🇭',
        'Austria': '🇦🇹',
        'Sweden': '🇸🇪',
        'Norway': '🇳🇴',
        'Denmark': '🇩🇰',
        'Finland': '🇫🇮',
        'Poland': '🇵🇱',
        'Ireland': '🇮🇪',
        'Portugal': '🇵🇹',
        'Greece': '🇬🇷',
        'Czech Republic': '🇨🇿',
        'Romania': '🇷🇴',
        'Hungary': '🇭🇺',
        'Japan': '🇯🇵',
        'China': '🇨🇳',
        'India': '🇮🇳',
        'South Korea': '🇰🇷',
        'Singapore': '🇸🇬',
        'Hong Kong': '🇭🇰',
        'Taiwan': '🇹🇼',
        'Thailand': '🇹🇭',
        'Malaysia': '🇲🇾',
        'Indonesia': '🇮🇩',
        'Philippines': '🇵🇭',
        'Vietnam': '🇻🇳',
        'Brazil': '🇧🇷',
        'Mexico': '🇲🇽',
        'Argentina': '🇦🇷',
        'Chile': '🇨🇱',
        'Colombia': '🇨🇴',
        'Israel': '🇮🇱',
        'Saudi Arabia': '🇸🇦',
        'United Arab Emirates': '🇦🇪',
        'Turkey': '🇹🇷',
        'South Africa': '🇿🇦',
        'Egypt': '🇪🇬',
        'New Zealand': '🇳🇿',
        'Russia': '🇷🇺',
        'Ukraine': '🇺🇦',
        'Unknown': '🏴‍☠️'
    };

    return flagMap[countryName] || '🏴‍☠️';
}

async function loadAnalytics() {
    const timeRange = document.getElementById('analyticsTimeRange').value;
    const loading = document.getElementById('analyticsLoading');
    const dashboard = document.getElementById('analyticsDashboard');

    loading.classList.remove('hidden');
    dashboard.classList.add('hidden');

    try {
        const response = await fetch(`${API_URL}/admin/analytics?time_range=${timeRange}`);
        const data = await response.json();

        if (data.error) {
            alert('Error loading analytics: ' + data.error);
            return;
        }

        // Update KPI cards
        updateKPI('sessions', data.sessions.value, data.sessions.change, timeRange);
        updateKPI('unique-users', data.unique_users.value, data.unique_users.change, timeRange);
        updateKPI('avg-messages', data.avg_messages.value, data.avg_messages.change, timeRange);
        updateKPI('feedback', data.feedback_count.value, data.feedback_count.change, timeRange);
        updateKPI('session-time', data.avg_session_time.value, data.avg_session_time.change, timeRange);
        updateKPI('msg-length', data.avg_message_length.value, data.avg_message_length.change, timeRange);

        // Render sparklines
        if (data.sparkline && data.sparkline.dates && data.sparkline.dates.length > 0) {
            renderSparkline('sparkline-sessions', data.sparkline.sessions, data.sparkline.dates, 'Sessions');
            renderSparkline('sparkline-unique-users', data.sparkline.unique_users, data.sparkline.dates, 'Users');
            renderSparkline('sparkline-avg-messages', data.sparkline.avg_messages, data.sparkline.dates, 'Avg Messages');
            renderSparkline('sparkline-feedback', data.sparkline.feedback, data.sparkline.dates, 'Feedback');
            renderSparkline('sparkline-session-time', data.sparkline.session_time, data.sparkline.dates, 'Seconds');
            renderSparkline('sparkline-msg-length', data.sparkline.msg_length, data.sparkline.dates, 'Characters');
        }

        // ESP breakdown table
        renderESPBreakdown(data.esp_breakdown);

        // Country breakdown table
        renderCountryBreakdown(data.country_breakdown);

        loading.classList.add('hidden');
        dashboard.classList.remove('hidden');
    } catch (error) {
        alert('Error loading analytics: ' + error.message);
        loading.classList.add('hidden');
    }
}

function updateKPI(kpiId, value, change, timeRange) {
    const valueElement = document.getElementById(`kpi-${kpiId}`);
    const changeElement = document.getElementById(`change-${kpiId}`);

    valueElement.textContent = value;

    if (timeRange === 'all_time' || change === null) {
        changeElement.textContent = '';
        changeElement.className = 'text-sm mb-1';
    } else {
        const isPositive = change > 0;
        const arrow = isPositive ? '↑' : '↓';
        const colorClass = isPositive ? 'text-green-700' : 'text-red-600';

        changeElement.textContent = `${arrow} ${Math.abs(change).toFixed(1)}%`;
        changeElement.className = `text-sm mb-1 font-semibold ${colorClass}`;
    }
}

function renderESPBreakdown(esps) {
    const tableBody = document.getElementById('espBreakdownTable');

    if (!esps || esps.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="2" class="text-center py-8 text-muted-foreground">No data available</td></tr>';
        return;
    }

    // Format ESP names for display
    const formatESPName = (esp) => {
        const nameMap = {
            'klaviyo': 'Klaviyo',
            'dotdigital': 'DotDigital',
            'attentive': 'Attentive',
            'other_webhook': 'Other/Webhook'
        };
        return nameMap[esp] || esp.charAt(0).toUpperCase() + esp.slice(1);
    };

    tableBody.innerHTML = esps.map(item => `
        <tr class="border-b border-border hover:bg-muted/30">
            <td class="py-2 px-3 text-card-foreground">${formatESPName(item.esp)}</td>
            <td class="py-2 px-3 text-right font-medium text-card-foreground">${item.conversations}</td>
        </tr>
    `).join('');
}

function renderCountryBreakdown(countries) {
    const tableBody = document.getElementById('countryBreakdownTable');

    if (!countries || countries.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="2" class="text-center py-8 text-muted-foreground">No data available</td></tr>';
        return;
    }

    tableBody.innerHTML = countries.map(item => `
        <tr class="border-b border-border hover:bg-muted/30">
            <td class="py-2 px-3 text-card-foreground">
                <span class="text-xl mr-2">${getCountryFlag(item.country)}</span>
                ${item.country}
            </td>
            <td class="py-2 px-3 text-right font-medium text-card-foreground">${item.sessions}</td>
        </tr>
    `).join('');
}

function renderSparkline(canvasId, data, dates, label) {
    const canvas = document.getElementById(canvasId);
    if (!canvas || !data || data.length === 0) return;

    const ctx = canvas.getContext('2d');
    const width = canvas.offsetWidth;
    const height = 50;

    // Set canvas actual size (for retina displays)
    const dpr = window.devicePixelRatio || 1;
    canvas.width = width * dpr;
    canvas.height = height * dpr;
    ctx.scale(dpr, dpr);

    // Clear canvas
    ctx.clearRect(0, 0, width, height);

    if (data.length < 2) return;

    // Calculate min/max with padding
    const minValue = Math.min(...data);
    const maxValue = Math.max(...data);
    const range = maxValue - minValue || 1;
    const padding = range * 0.1;

    // Calculate points
    const points = data.map((value, index) => {
        const x = (index / (data.length - 1)) * width;
        const y = height - ((value - minValue + padding) / (range + padding * 2)) * height;
        return { x, y, value, date: dates[index] };
    });

    // Draw line
    ctx.strokeStyle = 'oklch(0.205 0 0)';
    ctx.lineWidth = 2;
    ctx.lineJoin = 'round';
    ctx.lineCap = 'round';

    ctx.beginPath();
    ctx.moveTo(points[0].x, points[0].y);
    for (let i = 1; i < points.length; i++) {
        ctx.lineTo(points[i].x, points[i].y);
    }
    ctx.stroke();

    // Draw area fill
    ctx.fillStyle = 'oklch(0.205 0 0 / 0.1)';
    ctx.beginPath();
    ctx.moveTo(points[0].x, height);
    ctx.lineTo(points[0].x, points[0].y);
    for (let i = 1; i < points.length; i++) {
        ctx.lineTo(points[i].x, points[i].y);
    }
    ctx.lineTo(points[points.length - 1].x, height);
    ctx.closePath();
    ctx.fill();

    // Create tooltip element if it doesn't exist
    let tooltip = document.getElementById(`tooltip-${canvasId}`);
    if (!tooltip) {
        tooltip = document.createElement('div');
        tooltip.id = `tooltip-${canvasId}`;
        tooltip.className = 'sparkline-tooltip';
        canvas.parentElement.appendChild(tooltip);
    }

    // Mouse interaction for tooltip
    canvas.style.cursor = 'crosshair';

    const showTooltip = (e) => {
        const rect = canvas.getBoundingClientRect();
        const mouseX = e.clientX - rect.left;

        // Find closest point
        let closestIndex = 0;
        let closestDistance = Infinity;

        points.forEach((point, index) => {
            const distance = Math.abs(point.x - mouseX);
            if (distance < closestDistance) {
                closestDistance = distance;
                closestIndex = index;
            }
        });

        const point = points[closestIndex];

        // Format date
        const date = new Date(point.date);
        const dateStr = date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });

        // Show tooltip
        tooltip.innerHTML = `<div>${dateStr}</div><div><strong>${point.value}</strong> ${label}</div>`;
        tooltip.classList.add('visible');

        // Position tooltip
        const tooltipX = point.x + rect.left;
        const tooltipY = rect.top - 10;
        tooltip.style.left = `${tooltipX}px`;
        tooltip.style.top = `${tooltipY}px`;
        tooltip.style.transform = 'translate(-50%, -100%)';

        // Draw highlight dot
        ctx.clearRect(0, 0, width, height);

        // Redraw line
        ctx.strokeStyle = 'oklch(0.205 0 0)';
        ctx.lineWidth = 2;
        ctx.lineJoin = 'round';
        ctx.lineCap = 'round';
        ctx.beginPath();
        ctx.moveTo(points[0].x, points[0].y);
        for (let i = 1; i < points.length; i++) {
            ctx.lineTo(points[i].x, points[i].y);
        }
        ctx.stroke();

        // Redraw area fill
        ctx.fillStyle = 'oklch(0.205 0 0 / 0.1)';
        ctx.beginPath();
        ctx.moveTo(points[0].x, height);
        ctx.lineTo(points[0].x, points[0].y);
        for (let i = 1; i < points.length; i++) {
            ctx.lineTo(points[i].x, points[i].y);
        }
        ctx.lineTo(points[points.length - 1].x, height);
        ctx.closePath();
        ctx.fill();

        // Draw highlight dot
        ctx.fillStyle = 'oklch(0.205 0 0)';
        ctx.beginPath();
        ctx.arc(point.x, point.y, 3, 0, Math.PI * 2);
        ctx.fill();

        // Draw vertical line
        ctx.strokeStyle = 'oklch(0.205 0 0 / 0.3)';
        ctx.lineWidth = 1;
        ctx.setLineDash([2, 2]);
        ctx.beginPath();
        ctx.moveTo(point.x, 0);
        ctx.lineTo(point.x, height);
        ctx.stroke();
        ctx.setLineDash([]);
    };

    const hideTooltip = () => {
        tooltip.classList.remove('visible');

        // Redraw without highlight
        ctx.clearRect(0, 0, width, height);

        // Redraw line
        ctx.strokeStyle = 'oklch(0.205 0 0)';
        ctx.lineWidth = 2;
        ctx.lineJoin = 'round';
        ctx.lineCap = 'round';
        ctx.beginPath();
        ctx.moveTo(points[0].x, points[0].y);
        for (let i = 1; i < points.length; i++) {
            ctx.lineTo(points[i].x, points[i].y);
        }
        ctx.stroke();

        // Redraw area fill
        ctx.fillStyle = 'oklch(0.205 0 0 / 0.1)';
        ctx.beginPath();
        ctx.moveTo(points[0].x, height);
        ctx.lineTo(points[0].x, points[0].y);
        for (let i = 1; i < points.length; i++) {
            ctx.lineTo(points[i].x, points[i].y);
        }
        ctx.lineTo(points[points.length - 1].x, height);
        ctx.closePath();
        ctx.fill();
    };

    canvas.addEventListener('mousemove', showTooltip);
    canvas.addEventListener('mouseleave', hideTooltip);
}

async function loadESPManagement() {
    try {
        const response = await fetch(`${API_URL}/admin/esps`);
        const data = await response.json();

        const container = document.getElementById('espManagement');
        container.innerHTML = '';

        // Fetch all ESP links in parallel (performance optimization)
        const espPromises = data.esps.map(async esp => {
            const linksResponse = await fetch(`${API_URL}/admin/esp/${esp.name}/links`);
            const linksData = await linksResponse.json();
            return { esp, links: linksData.links };
        });

        const espResults = await Promise.all(espPromises);

        // Render all ESPs
        for (const { esp, links: linksData } of espResults) {
            const espDiv = document.createElement('div');
            espDiv.className = 'bg-muted/50 rounded-lg p-4 border border-border';

            const displayName = esp.display_name || esp.name;

            // Build links HTML
            let linksHTML = '';
            if (linksData && linksData.length > 0) {
                linksHTML = linksData.map(link => {
                    // Determine badge color based on status
                    let badgeClass = '';
                    if (link.status === 'crawled') {
                        badgeClass = 'bg-green-100 text-green-800';
                    } else if (link.status === 'pending') {
                        badgeClass = 'bg-yellow-100 text-yellow-800';
                    } else if (link.status === 'checking') {
                        badgeClass = 'bg-blue-100 text-blue-800';
                    }

                    return `
                    <div class="flex items-center gap-2 p-2 bg-background rounded-lg border border-border hover:border-primary transition-colors ${link.status === 'pending' ? 'bg-accent/10 border-primary' : ''}">
                        <input type="checkbox" class="link-checkbox w-4 h-4 rounded border-input cursor-pointer" data-esp="${esp.name}" value="${link.url}" ${link.status === 'pending' ? 'checked' : ''}>
                        <span class="text-xs font-medium px-2 py-0.5 rounded ${badgeClass} uppercase tracking-wide">${link.status}</span>
                        <a href="${link.url}" target="_blank" class="flex-1 text-sm text-foreground hover:text-primary hover:underline truncate">${link.url}</a>
                        ${link.status === 'pending' ? `
                            <button onclick="openPasteModal('${esp.name}', '${link.url.replace(/'/g, "\\'")}', false)" class="px-3 py-1 bg-primary/10 text-primary border border-primary rounded text-xs font-medium hover:bg-primary hover:text-primary-foreground transition-colors whitespace-nowrap" title="Paste content manually">
                                📋 Paste Content
                            </button>
                        ` : ''}
                    </div>
                `;
                }).join('');
            } else {
                linksHTML = '<div class="text-center py-8 text-muted-foreground text-sm italic border-2 border-dashed border-border rounded-lg">No links added yet. Add a link below to get started.</div>';
            }

            espDiv.innerHTML = `
                <h4 class="text-base font-semibold text-card-foreground mb-3">${displayName} (${esp.doc_count} documents)</h4>
                <div class="space-y-2 mb-4" id="links-${esp.name}">
                    ${linksHTML}
                </div>
                <div class="flex gap-2">
                    <input type="text" placeholder="Add new link URL" id="newLink-${esp.name}" class="flex-1 px-3 py-2 border border-input bg-background rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-ring">
                    <button class="px-4 py-2 bg-primary text-primary-foreground rounded-lg font-medium text-sm hover:bg-primary/90 transition-colors whitespace-nowrap" onclick="addLink('${esp.name}')">Add Link</button>
                </div>
            `;

            container.appendChild(espDiv);

            // Add checkbox change listeners for global bulk actions
            const checkboxes = espDiv.querySelectorAll('.link-checkbox');
            checkboxes.forEach(checkbox => {
                checkbox.addEventListener('change', () => {
                    updateGlobalBulkActions();
                });
            });
        }

        // Initial check for global bulk actions
        updateGlobalBulkActions();

    } catch (error) {
        console.error('Error loading ESP management:', error);
    }
}

function updateGlobalBulkActions() {
    const espCheckboxes = document.querySelectorAll('.link-checkbox:checked');
    const globalKnowledgeCheckboxes = document.querySelectorAll('.global-link-checkbox:checked');
    const totalChecked = espCheckboxes.length + globalKnowledgeCheckboxes.length;

    const globalActions = document.getElementById('globalBulkActions');
    const selectedCount = document.getElementById('selectedCount');

    if (totalChecked > 0) {
        globalActions.classList.remove('hidden');
        globalActions.classList.add('flex');
        selectedCount.textContent = totalChecked;
    } else {
        globalActions.classList.add('hidden');
        globalActions.classList.remove('flex');
    }
}

// Feature detection: Check if async crawl is enabled on backend
let USE_ASYNC_CRAWL = false;

async function checkAsyncCrawlSupport() {
    try {
        // Try to access the async endpoint - if it exists, async is enabled
        const response = await fetch(`${API_URL}/admin/crawl-status?job_ids=00000000-0000-0000-0000-000000000000`, {
            method: 'GET'
        });
        // If we get 200 (even with empty results), async is enabled
        // If we get 404, async endpoints don't exist
        USE_ASYNC_CRAWL = response.status !== 404;
    } catch (error) {
        USE_ASYNC_CRAWL = false;
    }
}

// Check on page load
checkAsyncCrawlSupport();

async function crawlAllSelected() {
    const espCheckboxes = document.querySelectorAll('.link-checkbox:checked');
    const globalCheckboxes = document.querySelectorAll('.global-link-checkbox:checked');

    if (espCheckboxes.length === 0 && globalCheckboxes.length === 0) {
        alert('Please select at least one link to crawl');
        return;
    }

    // Route to async or sync version based on backend support
    if (USE_ASYNC_CRAWL) {
        return await crawlAllSelectedAsync();
    } else {
        return await crawlAllSelectedSync();
    }
}

async function crawlAllSelectedAsync() {
    const espCheckboxes = document.querySelectorAll('.link-checkbox:checked');
    const globalCheckboxes = document.querySelectorAll('.global-link-checkbox:checked');

    // Group URLs by ESP
    const espGroups = {};
    espCheckboxes.forEach(cb => {
        const espName = cb.dataset.esp;
        const url = cb.value;
        if (!espGroups[espName]) {
            espGroups[espName] = [];
        }
        espGroups[espName].push(url);
    });

    // Add global knowledge URLs
    const globalUrls = Array.from(globalCheckboxes).map(cb => cb.value);

    try {
        // Disable crawl buttons
        const crawlButtons = document.querySelectorAll('button[onclick="crawlAllSelected()"]');
        crawlButtons.forEach(btn => {
            btn.disabled = true;
            btn.innerHTML = `
                <div class="flex items-center gap-2">
                    <svg class="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    <span>Queueing...</span>
                </div>
            `;
        });

        let allJobIds = [];

        // Queue crawl jobs for each ESP
        for (const [espName, urls] of Object.entries(espGroups)) {
            try {
                const response = await fetch(`${API_URL}/admin/esp/${espName}/crawl-selected`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ urls })
                });

                const data = await response.json();

                if (data.success && data.job_ids) {
                    allJobIds = allJobIds.concat(data.job_ids);
                } else {
                    console.error(`Failed to queue ${espName}:`, data.error);
                }
            } catch (error) {
                console.error(`Error queueing ${espName}:`, error);
            }
        }

        // Queue global knowledge URLs
        if (globalUrls.length > 0) {
            try {
                const response = await fetch(`${API_URL}/admin/global-knowledge/crawl-selected`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ urls: globalUrls })
                });

                const data = await response.json();

                if (data.success && data.job_ids) {
                    allJobIds = allJobIds.concat(data.job_ids);
                }
            } catch (error) {
                console.error('Error queueing global knowledge:', error);
            }
        }

        if (allJobIds.length === 0) {
            alert('Failed to queue any crawl jobs. Check console for errors.');
            // Re-enable buttons
            crawlButtons.forEach(btn => {
                btn.disabled = false;
                btn.innerHTML = 'Crawl Selected';
            });
            return;
        }

        // Find or create progress container
        let progressContainer = document.getElementById('crawl-progress-container');
        if (!progressContainer) {
            // Insert progress container after the crawl buttons
            const espManagement = document.getElementById('esp-management');
            if (espManagement) {
                progressContainer = document.createElement('div');
                progressContainer.id = 'crawl-progress-container';
                espManagement.insertBefore(progressContainer, espManagement.firstChild);
            }
        }

        // Start progress tracker
        if (progressContainer && typeof CrawlProgressTracker !== 'undefined') {
            const tracker = new CrawlProgressTracker(allJobIds, progressContainer, API_URL);
            tracker.start();
        } else {
            console.error('CrawlProgressTracker not available');
            alert(`Queued ${allJobIds.length} URLs for crawling. Refresh the page to see results.`);
        }

        // Re-enable buttons
        crawlButtons.forEach(btn => {
            btn.disabled = false;
            btn.innerHTML = 'Crawl Selected';
        });

    } catch (error) {
        alert('Error starting crawl: ' + error.message);
        console.error(error);

        // Re-enable buttons
        const crawlButtons = document.querySelectorAll('button[onclick="crawlAllSelected()"]');
        crawlButtons.forEach(btn => {
            btn.disabled = false;
            btn.innerHTML = 'Crawl Selected';
        });
    }
}

async function crawlAllSelectedSync() {
    const espCheckboxes = document.querySelectorAll('.link-checkbox:checked');
    const globalCheckboxes = document.querySelectorAll('.global-link-checkbox:checked');

    // Get the crawl button and add loading state
    const crawlButtons = document.querySelectorAll('button[onclick="crawlAllSelected()"]');
    const originalButtonContents = [];

    crawlButtons.forEach(btn => {
        originalButtonContents.push(btn.innerHTML);
        btn.disabled = true;
        btn.innerHTML = `
            <div class="flex items-center gap-2">
                <svg class="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <span>Crawling...</span>
            </div>
        `;
        btn.classList.add('opacity-75', 'cursor-not-allowed');
    });

    // Group URLs by ESP
    const espGroups = {};
    espCheckboxes.forEach(cb => {
        const espName = cb.dataset.esp;
        const url = cb.value;
        if (!espGroups[espName]) {
            espGroups[espName] = [];
        }
        espGroups[espName].push(url);
    });

    // Add global knowledge URLs
    const globalUrls = Array.from(globalCheckboxes).map(cb => cb.value);

    let totalCrawled = 0;
    let errors = [];

    try {
        // Crawl each ESP's links
        for (const [espName, urls] of Object.entries(espGroups)) {
            try {
                const response = await fetch(`${API_URL}/admin/esp/${espName}/crawl-selected`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ password: adminPassword, urls })
                });

                const data = await response.json();

                if (data.success) {
                    // API returns results.success array, not count
                    const successCount = data.results?.success?.length || 0;
                    const failedCount = data.results?.failed?.length || 0;
                    totalCrawled += successCount;

                    if (failedCount > 0) {
                        const failedUrls = data.results.failed.map(f => f.url).join(', ');
                        errors.push(`${espName}: ${failedCount} failed (${failedUrls})`);
                    }
                } else {
                    errors.push(`${espName}: ${data.error || 'Unknown error'}`);
                }
            } catch (error) {
                errors.push(`${espName}: ${error.message}`);
            }
        }

        // Crawl global knowledge links
        if (globalUrls.length > 0) {
            try {
                const response = await fetch(`${API_URL}/admin/global-knowledge/crawl-selected`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ password: adminPassword, urls: globalUrls })
                });

                const data = await response.json();

                if (data.success) {
                    // Global knowledge returns count field
                    totalCrawled += (data.count || 0);
                } else {
                    errors.push(`Global Knowledge: ${data.error || 'Unknown error'}`);
                }
            } catch (error) {
                errors.push(`Global Knowledge: ${error.message}`);
            }
        }

        // Show results
        if (errors.length === 0) {
            alert(`Successfully crawled ${totalCrawled} links!`);
        } else {
            alert(`Crawled ${totalCrawled} links with ${errors.length} errors:\n${errors.join('\n')}`);
        }

        await loadESPManagement();
    } catch (error) {
        alert('Error crawling links: ' + error.message);
    } finally {
        // Restore button state
        crawlButtons.forEach((btn, index) => {
            btn.disabled = false;
            btn.innerHTML = originalButtonContents[index];
            btn.classList.remove('opacity-75', 'cursor-not-allowed');
        });
    }
}

async function deleteAllSelected() {
    const espCheckboxes = document.querySelectorAll('.link-checkbox:checked');
    const globalCheckboxes = document.querySelectorAll('.global-link-checkbox:checked');

    if (espCheckboxes.length === 0 && globalCheckboxes.length === 0) {
        alert('Please select at least one link to delete');
        return;
    }

    const totalSelected = espCheckboxes.length + globalCheckboxes.length;
    if (!confirm(`Are you sure you want to delete ${totalSelected} link(s)? This will also remove their documentation.`)) {
        return;
    }

    // Get the delete button and add loading state
    const deleteButtons = document.querySelectorAll('button[onclick="deleteAllSelected()"]');
    const originalButtonContents = [];

    deleteButtons.forEach(btn => {
        originalButtonContents.push(btn.innerHTML);
        btn.disabled = true;
        btn.innerHTML = `
            <div class="flex items-center gap-2">
                <svg class="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <span>Deleting...</span>
            </div>
        `;
        btn.classList.add('opacity-75', 'cursor-not-allowed');
    });

    // Group URLs by ESP
    const espGroups = {};
    espCheckboxes.forEach(cb => {
        const espName = cb.dataset.esp;
        const url = cb.value;
        if (!espGroups[espName]) {
            espGroups[espName] = [];
        }
        espGroups[espName].push(url);
    });

    // Add global knowledge URLs
    const globalUrls = Array.from(globalCheckboxes).map(cb => cb.value);

    let totalDeleted = 0;
    let errors = [];

    try {
        // Delete each ESP's links
        for (const [espName, urls] of Object.entries(espGroups)) {
            try {
                const response = await fetch(`${API_URL}/admin/esp/${espName}/delete-links`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ password: adminPassword, urls })
                });

                const data = await response.json();

                if (data.success) {
                    totalDeleted += urls.length;
                } else {
                    errors.push(`${espName}: ${data.error || 'Unknown error'}`);
                }
            } catch (error) {
                errors.push(`${espName}: ${error.message}`);
            }
        }

        // Delete global knowledge links
        if (globalUrls.length > 0) {
            try {
                const response = await fetch(`${API_URL}/admin/global-knowledge/delete-links`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ password: adminPassword, urls: globalUrls })
                });

                const data = await response.json();

                if (data.success) {
                    totalDeleted += globalUrls.length;
                } else {
                    errors.push(`Global Knowledge: ${data.error || 'Unknown error'}`);
                }
            } catch (error) {
                errors.push(`Global Knowledge: ${error.message}`);
            }
        }

        // Show results
        if (errors.length === 0) {
            alert(`Successfully deleted ${totalDeleted} links!`);
        } else {
            alert(`Deleted ${totalDeleted} links with ${errors.length} errors:\n${errors.join('\n')}`);
        }

        await loadESPManagement();
    } catch (error) {
        alert('Error deleting links: ' + error.message);
    } finally {
        // Restore button state
        deleteButtons.forEach((btn, index) => {
            btn.disabled = false;
            btn.innerHTML = originalButtonContents[index];
            btn.classList.remove('opacity-75', 'cursor-not-allowed');
        });
    }
}

async function addLink(espName) {
    const input = document.getElementById(`newLink-${espName}`);
    const url = input.value.trim();

    if (!url) return;

    try {
        const response = await fetch(`${API_URL}/admin/esp/${espName}/add-link`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ password: adminPassword, url })
        });

        const data = await response.json();

        if (data.success) {
            alert('Link added successfully. It will be pre-checked for crawling.');
            input.value = '';
            // Reload the ESP management to show the new link
            await loadESPManagement();
        } else {
            alert('Error: ' + (data.error || 'Unknown error'));
        }
    } catch (error) {
        alert('Error adding link: ' + error.message);
    }
}

document.getElementById('createESPBtn').addEventListener('click', async () => {
    const name = document.getElementById('newESPName').value.trim();

    if (!name) return;

    try {
        const response = await fetch(`${API_URL}/admin/esp/create`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ password: adminPassword, name })
        });

        const data = await response.json();

        if (data.success) {
            alert('ESP created successfully!');
            document.getElementById('newESPName').value = '';
            await loadESPManagement();
            await reloadSidebar(); // Dynamically reload sidebar
        } else {
            alert('Error: ' + (data.error || 'Unknown error'));
        }
    } catch (error) {
        alert('Error creating ESP: ' + error.message);
    }
});

document.getElementById('refreshAllBtn').addEventListener('click', async () => {
    if (!confirm('This will re-crawl all documentation links. Continue?')) return;

    try {
        const response = await fetch(`${API_URL}/admin/refresh`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ password: adminPassword })
        });

        const data = await response.json();

        if (data.success) {
            alert('All documentation refreshed successfully!');
        }
    } catch (error) {
        alert('Error refreshing: ' + error.message);
    }
});

// History Modal
const historyModal = document.getElementById('historyModal');
const closeHistory = document.getElementById('closeHistory');
const historyContent = document.getElementById('historyContent');
const historyTitle = document.getElementById('historyTitle');
const clearHistoryBtn = document.getElementById('clearHistoryBtn');

function showHistory(esp) {
    const history = conversationHistories[esp] || [];
    const espName = esp === 'other/webhook' ? 'Other/Webhook' :
                    esp === 'klaviyo' ? 'Klaviyo' :
                    esp === 'dotdigital' ? 'DotDigital' :
                    esp === 'attentive' ? 'Attentive' : esp;

    historyTitle.textContent = `${espName} - Conversation History`;

    if (history.length === 0) {
        historyContent.innerHTML = `
            <div class="text-center py-12 text-muted-foreground">
                <svg class="w-16 h-16 mx-auto mb-4 opacity-30" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="10"></circle>
                    <line x1="12" y1="8" x2="12" y2="12"></line>
                    <line x1="12" y1="16" x2="12.01" y2="16"></line>
                </svg>
                <p>No conversation history yet for this ESP.</p>
            </div>
        `;
    } else {
        // Group messages into conversations (pairs of user + assistant)
        let conversationsHTML = '';

        for (let i = 0; i < history.length; i += 2) {
            const userMsg = history[i];
            const assistantMsg = history[i + 1];

            if (userMsg) {
                const timestamp = new Date(userMsg.timestamp).toLocaleString();
                const assistantContent = assistantMsg && typeof marked !== 'undefined'
                    ? marked.parse(assistantMsg.content)
                    : (assistantMsg ? assistantMsg.content : '');

                conversationsHTML += `
                    <div class="bg-muted/50 rounded-lg p-4 mb-4 border border-border">
                        <div class="flex items-start justify-between mb-3">
                            <div class="text-xs text-muted-foreground font-medium">${timestamp}</div>
                            <button class="restore-conversation-btn flex items-center gap-1.5 text-xs text-primary hover:text-primary/80 font-medium transition-colors" data-index="${i}" title="Restore this conversation to main chat">
                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                    <polyline points="23 4 23 10 17 10"></polyline>
                                    <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"></path>
                                </svg>
                                Restore
                            </button>
                        </div>
                        <div class="bg-primary text-primary-foreground rounded-lg p-3 mb-2">
                            <div class="text-xs font-medium mb-1 opacity-70 uppercase tracking-wide">You</div>
                            <div class="text-sm">${userMsg.content}</div>
                        </div>
                        ${assistantMsg ? `
                            <div class="bg-background text-foreground rounded-lg p-3 border border-border">
                                <div class="text-xs font-medium mb-1 opacity-70 uppercase tracking-wide">Assistant</div>
                                <div class="text-sm prose prose-xs max-w-none">${assistantContent}</div>
                            </div>
                        ` : ''}
                    </div>
                `;
            }
        }

        historyContent.innerHTML = conversationsHTML;

        // Add event listeners to restore buttons
        document.querySelectorAll('.restore-conversation-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const index = parseInt(e.currentTarget.dataset.index);
                restoreConversation(esp, index);
            });
        });
    }

    historyModal.classList.remove('hidden');
}

function restoreConversation(esp, index) {
    const history = conversationHistories[esp] || [];
    const userMsg = history[index];
    const assistantMsg = history[index + 1];

    if (!userMsg) return;

    // Clear current chat display
    chatMessages.innerHTML = '';

    // Add the restored conversation to the chat
    addMessage('user', userMsg.content);
    if (assistantMsg) {
        addMessage('assistant', assistantMsg.content);
    }

    // Close the history modal
    historyModal.classList.add('hidden');

    // Scroll to top of chat
    chatMessages.scrollTop = 0;
}

closeHistory.addEventListener('click', () => {
    historyModal.classList.add('hidden');
});

clearHistoryBtn.addEventListener('click', () => {
    if (confirm('Are you sure you want to clear the conversation history for this ESP? This cannot be undone.')) {
        clearCurrentHistory();
        historyModal.classList.add('hidden');
        alert('History cleared for current session.');
    }
});

// Close modals when clicking outside
window.addEventListener('click', (e) => {
    if (e.target === feedbackModal) {
        feedbackModal.classList.add('hidden');
    }
    if (e.target === adminModal) {
        adminModal.classList.add('hidden');
    }
    if (e.target === historyModal) {
        historyModal.classList.add('hidden');
    }
});

// ========== GENERAL SETTINGS FUNCTIONS ==========

let availableModels = { gemini: [], claude: [], openai: [] };

async function loadGeneralSettings() {
    await Promise.all([
        loadAIModelConfig(),
        loadSystemPrompt(),
        loadAuditLog()
    ]);
}

async function loadAIModelConfig() {
    try {
        const response = await fetch(`${API_URL}/admin/settings/ai-model`);
        const data = await response.json();

        if (data.error) {
            console.error('Error loading AI model config:', data.error);
            return;
        }

        availableModels = data.available_models;
        const currentConfig = data.current;
        const status = data.status;

        // Update current status display
        const providerNames = {
            'gemini': 'Google Gemini',
            'claude': 'Anthropic Claude',
            'openai': 'OpenAI'
        };
        document.getElementById('currentProvider').textContent = providerNames[currentConfig.provider] || currentConfig.provider;
        document.getElementById('currentModel').textContent = availableModels[currentConfig.provider]?.find(m => m.name === currentConfig.model_name)?.display || currentConfig.model_name;

        // Update status badge
        const statusBadge = document.getElementById('aiStatusBadge');
        if (status.status === 'ok') {
            statusBadge.textContent = '✓ Working';
            statusBadge.className = 'px-3 py-1 rounded-full text-xs font-semibold bg-green-100 text-green-800';
        } else {
            statusBadge.textContent = '✗ Error';
            statusBadge.className = 'px-3 py-1 rounded-full text-xs font-semibold bg-red-100 text-red-800';
        }

        // Set provider select
        document.getElementById('aiProvider').value = currentConfig.provider;

        // Populate model options
        updateModelOptions(currentConfig.provider, currentConfig.model_name);

        // Add event listener for provider change
        document.getElementById('aiProvider').addEventListener('change', (e) => {
            updateModelOptions(e.target.value);
        });

    } catch (error) {
        console.error('Error loading AI model config:', error);
    }
}

function updateModelOptions(provider, selectedModel = null) {
    const modelSelect = document.getElementById('aiModel');
    modelSelect.innerHTML = '';

    const models = availableModels[provider] || [];
    models.forEach(model => {
        const option = document.createElement('option');
        option.value = model.name;
        option.textContent = model.display;
        if (selectedModel && model.name === selectedModel) {
            option.selected = true;
        }
        modelSelect.appendChild(option);
    });
}

async function loadSystemPrompt() {
    try {
        const response = await fetch(`${API_URL}/admin/settings/system-prompt`);
        const data = await response.json();

        if (data.error) {
            console.error('Error loading system prompt:', data.error);
            return;
        }

        document.getElementById('systemPrompt').value = data.system_prompt;
    } catch (error) {
        console.error('Error loading system prompt:', error);
    }
}

async function loadAuditLog() {
    try {
        const response = await fetch(`${API_URL}/admin/settings/audit-log?limit=20`);
        const data = await response.json();

        if (data.error) {
            console.error('Error loading audit log:', data.error);
            return;
        }

        const container = document.getElementById('auditLogContainer');

        if (!data.audit_log || data.audit_log.length === 0) {
            container.innerHTML = '<div class="text-center py-8 text-muted-foreground text-sm">No changes recorded yet</div>';
            return;
        }

        // Reverse to show most recent first
        const entries = [...data.audit_log].reverse();

        container.innerHTML = entries.map((entry, index) => {
            const timestamp = new Date(entry.timestamp).toLocaleString();
            const actualIndex = data.audit_log.length - 1 - index;

            return `
                <div class="border-b border-border p-4 hover:bg-muted/30 transition-colors">
                    <div class="flex items-start justify-between mb-2">
                        <div>
                            <div class="font-medium text-card-foreground text-sm">${entry.description}</div>
                            <div class="text-xs text-muted-foreground mt-1">
                                by ${entry.user_email} • ${timestamp}
                            </div>
                        </div>
                        <button class="px-3 py-1 text-xs font-medium bg-primary text-primary-foreground rounded hover:bg-primary/90 transition-colors" onclick="restoreFromBackup(${actualIndex}, '${entry.timestamp}')">
                            Restore
                        </button>
                    </div>
                    ${entry.backup ? `
                        <div class="mt-2 text-xs">
                            <details class="cursor-pointer">
                                <summary class="text-muted-foreground hover:text-foreground">View backup details</summary>
                                <div class="mt-2 p-2 bg-background rounded border border-border font-mono text-xs overflow-x-auto">
                                    <pre>${JSON.stringify(entry.backup, null, 2)}</pre>
                                </div>
                            </details>
                        </div>
                    ` : ''}
                </div>
            `;
        }).join('');

    } catch (error) {
        console.error('Error loading audit log:', error);
    }
}

// Apply AI Configuration Changes
document.getElementById('applyAIConfigBtn').addEventListener('click', async () => {
    const provider = document.getElementById('aiProvider').value;
    const modelName = document.getElementById('aiModel').value;
    const apiKey = document.getElementById('newApiKey').value.trim();

    // Show confirmation dialog with email input
    const providerNames = {
        'gemini': 'Google Gemini',
        'claude': 'Anthropic Claude',
        'openai': 'OpenAI'
    };
    const userEmail = prompt(`You are about to change the AI configuration to:\n\nProvider: ${providerNames[provider] || provider}\nModel: ${availableModels[provider]?.find(m => m.name === modelName)?.display || modelName}${apiKey ? '\nAPI Key: [will be updated]' : ''}\n\nThis will affect all users immediately.\n\nEnter your email address to confirm:`);

    if (!userEmail) {
        // User cancelled or didn't enter email
        return;
    }

    if (!userEmail.includes('@')) {
        alert('Please enter a valid email address');
        return;
    }

    try {
        // Update API key first if provided
        if (apiKey) {
            const apiKeyResponse = await fetch(`${API_URL}/admin/settings/api-key`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    password: adminPassword,
                    provider,
                    api_key: apiKey,
                    user_email: userEmail
                })
            });

            const apiKeyData = await apiKeyResponse.json();
            if (!apiKeyData.success) {
                alert('Error updating API key: ' + (apiKeyData.error || 'Unknown error'));
                return;
            }
        }

        // Update model configuration
        const response = await fetch(`${API_URL}/admin/settings/ai-model`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                password: adminPassword,
                provider,
                model_name: modelName,
                user_email: userEmail
            })
        });

        const data = await response.json();

        if (data.success) {
            alert('AI configuration updated successfully!');
            document.getElementById('newApiKey').value = '';
            await loadGeneralSettings();
        } else {
            alert('Error: ' + (data.error || 'Unknown error'));
        }
    } catch (error) {
        alert('Error updating AI configuration: ' + error.message);
    }
});

// Update System Prompt
document.getElementById('updatePromptBtn').addEventListener('click', async () => {
    const systemPrompt = document.getElementById('systemPrompt').value;
    const userEmail = document.getElementById('promptChangeEmail').value;

    if (!userEmail) {
        alert('Please enter your email address for the audit trail');
        return;
    }

    if (!systemPrompt.trim()) {
        alert('System prompt cannot be empty');
        return;
    }

    if (!confirm('Are you sure you want to update the system prompt? This will affect all users immediately.')) {
        return;
    }

    try {
        const response = await fetch(`${API_URL}/admin/settings/system-prompt`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                password: adminPassword,
                system_prompt: systemPrompt,
                user_email: userEmail
            })
        });

        const data = await response.json();

        if (data.success) {
            alert('System prompt updated successfully!');
            document.getElementById('promptChangeEmail').value = '';
            await loadGeneralSettings();
        } else {
            alert('Error: ' + (data.error || 'Unknown error'));
        }
    } catch (error) {
        alert('Error updating system prompt: ' + error.message);
    }
});

// Restore from backup
async function restoreFromBackup(auditIndex, timestamp) {
    const userEmail = prompt('Enter your email address to confirm restoration:');

    if (!userEmail) {
        return;
    }

    if (!confirm(`Are you sure you want to restore configuration from ${new Date(timestamp).toLocaleString()}? This will replace the current settings.`)) {
        return;
    }

    try {
        const response = await fetch(`${API_URL}/admin/settings/restore`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                password: adminPassword,
                audit_index: auditIndex,
                user_email: userEmail
            })
        });

        const data = await response.json();

        if (data.success) {
            alert('Configuration restored successfully!');
            await loadGeneralSettings();
        } else {
            alert('Error: ' + (data.error || 'Unknown error'));
        }
    } catch (error) {
        alert('Error restoring configuration: ' + error.message);
    }
}

// ========== GLOBAL KNOWLEDGE FUNCTIONS ==========

async function loadGlobalKnowledge() {
    try {
        const response = await fetch(`${API_URL}/admin/global-knowledge/links`);
        const data = await response.json();

        const container = document.getElementById('globalKnowledgeLinks');

        if (!data.links || data.links.length === 0) {
            container.innerHTML = '<div class="text-center py-8 text-muted-foreground text-sm italic border-2 border-dashed border-border rounded-lg">No global knowledge sources added yet. Add a link below to get started.</div>';
            return;
        }

        container.innerHTML = data.links.map(link => {
            // Determine badge color based on status
            let badgeClass = '';
            if (link.status === 'crawled') {
                badgeClass = 'bg-green-100 text-green-800';
            } else if (link.status === 'pending') {
                badgeClass = 'bg-yellow-100 text-yellow-800';
            } else if (link.status === 'checking') {
                badgeClass = 'bg-blue-100 text-blue-800';
            }

            return `
            <div class="flex items-center gap-2 p-2 bg-background rounded-lg border border-border hover:border-primary transition-colors ${link.status === 'pending' ? 'bg-accent/10 border-primary' : ''}">
                <input type="checkbox" class="global-link-checkbox w-4 h-4 rounded border-input cursor-pointer" value="${link.url}" ${link.status === 'pending' ? 'checked' : ''}>
                <span class="text-xs font-medium px-2 py-0.5 rounded ${badgeClass} uppercase tracking-wide">${link.status}</span>
                <a href="${link.url}" target="_blank" class="flex-1 text-sm text-foreground hover:text-primary hover:underline truncate">${link.url}</a>
                ${link.status === 'pending' ? `
                    <button onclick="openPasteModal('global', '${link.url.replace(/'/g, "\\'")}', true)" class="px-3 py-1 bg-primary/10 text-primary border border-primary rounded text-xs font-medium hover:bg-primary hover:text-primary-foreground transition-colors whitespace-nowrap" title="Paste content manually">
                        📋 Paste Content
                    </button>
                ` : ''}
            </div>
        `;
        }).join('');

        // Add checkbox change listeners
        const checkboxes = container.querySelectorAll('.global-link-checkbox');
        checkboxes.forEach(checkbox => {
            checkbox.addEventListener('change', updateGlobalBulkActions);
        });

        updateGlobalBulkActions();

    } catch (error) {
        console.error('Error loading global knowledge:', error);
    }
}

async function addGlobalKnowledgeLink() {
    const input = document.getElementById('newGlobalKnowledgeLink');
    const url = input.value.trim();

    if (!url) return;

    try {
        const response = await fetch(`${API_URL}/admin/global-knowledge/add-link`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ password: adminPassword, url })
        });

        const data = await response.json();

        if (data.success) {
            alert('Global knowledge link added successfully. It will be pre-checked for crawling.');
            input.value = '';
            await loadESPManagement();
        } else {
            alert('Error: ' + (data.error || 'Unknown error'));
        }
    } catch (error) {
        alert('Error adding link: ' + error.message);
    }
}

// Update loadESPManagement to also load global knowledge (in parallel for better performance)
const originalLoadESPManagement = loadESPManagement;
loadESPManagement = async function() {
    // Load ESPs and Global Knowledge in parallel instead of sequentially
    await Promise.all([
        originalLoadESPManagement(),
        loadGlobalKnowledge()
    ]);
};
