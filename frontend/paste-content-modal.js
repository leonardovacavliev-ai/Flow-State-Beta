// ========== PASTE CONTENT MODAL FUNCTIONS ==========

let currentPasteContext = {
    espName: null,
    url: null,
    isGlobal: false
};

function openPasteModal(espName, url, isGlobal = false) {
    currentPasteContext = { espName, url, isGlobal };

    const modal = document.getElementById('pasteContentModal');
    const urlInput = document.getElementById('pasteContentUrl');
    const espInput = document.getElementById('pasteContentEsp');
    const textArea = document.getElementById('pasteContentText');

    urlInput.value = url;
    espInput.value = isGlobal ? 'Global Knowledge' : espName;
    textArea.value = '';

    modal.classList.remove('hidden');
    textArea.focus();
}

function closePasteModal() {
    const modal = document.getElementById('pasteContentModal');
    modal.classList.add('hidden');
    currentPasteContext = { espName: null, url: null, isGlobal: false };
}

async function submitPasteContent() {
    const content = document.getElementById('pasteContentText').value.trim();

    if (!content) {
        alert('Please paste some content before submitting.');
        return;
    }

    if (content.length < 100) {
        if (!confirm('The content seems very short (less than 100 characters). Are you sure you want to continue?')) {
            return;
        }
    }

    const submitBtn = document.getElementById('submitPasteContent');
    const originalText = submitBtn.innerHTML;

    try {
        // Show loading state
        submitBtn.disabled = true;
        submitBtn.innerHTML = `
            <div class="flex items-center gap-2">
                <svg class="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <span>Saving & Vectorizing...</span>
            </div>
        `;

        const endpoint = currentPasteContext.isGlobal
            ? `${API_URL}/admin/global-knowledge/paste-content`
            : `${API_URL}/admin/esp/${currentPasteContext.espName}/paste-content`;

        const response = await fetch(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                password: adminPassword,
                url: currentPasteContext.url,
                content: content
            })
        });

        const data = await response.json();

        if (data.success) {
            alert(`✅ Content saved successfully!\n\nFile: ${data.filename}\n\nThe content has been vectorized and is now available for the AI assistant.`);
            closePasteModal();
            await loadESPManagement(); // Refresh the ESP management view
        } else {
            alert('❌ Error: ' + (data.error || 'Unknown error'));
        }
    } catch (error) {
        alert('❌ Error saving content: ' + error.message);
    } finally {
        // Restore button state
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalText;
    }
}

// Event listeners for paste modal
document.addEventListener('DOMContentLoaded', () => {
    const closePasteBtn = document.getElementById('closePasteModal');
    const cancelPasteBtn = document.getElementById('cancelPasteContent');
    const submitPasteBtn = document.getElementById('submitPasteContent');
    const modal = document.getElementById('pasteContentModal');

    if (closePasteBtn) {
        closePasteBtn.addEventListener('click', closePasteModal);
    }

    if (cancelPasteBtn) {
        cancelPasteBtn.addEventListener('click', closePasteModal);
    }

    if (submitPasteBtn) {
        submitPasteBtn.addEventListener('click', submitPasteContent);
    }

    // Close modal when clicking outside
    if (modal) {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                closePasteModal();
            }
        });
    }

    // Close modal with Escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && !modal.classList.contains('hidden')) {
            closePasteModal();
        }
    });
});
