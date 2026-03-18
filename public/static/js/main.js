document.addEventListener('DOMContentLoaded', () => {
    const ingestForm = document.getElementById('ingestForm');
    const submitBtn = document.getElementById('submitBtn');
    const resultsSection = document.getElementById('resultsSection');
    const loading = document.getElementById('loading');
    const results = document.getElementById('results');
    const isPrivate = document.getElementById('isPrivate');
    const tokenContainer = document.getElementById('tokenContainer');

    // Toggle private repo token field
    isPrivate.addEventListener('change', (e) => {
        tokenContainer.style.display = e.target.checked ? 'block' : 'none';
    });

    // --- SLUG URL AUTO-TRIGGER ---
    const handleUrlSlug = () => {
        let path = window.location.pathname.substring(1); // Remove leading slash
        if (!path || path === "" || path.startsWith('static') || path.startsWith('api')) return;

        // Cleanup path (remove trailing slashes, etc)
        path = path.replace(/\/$/, "");

        let repoUrl = path;

        // 1. Handle full https://github.com/owner/repo
        if (repoUrl.startsWith('https:/github.com/')) {
            repoUrl = repoUrl.replace('https:/github.com/', 'https://github.com/');
        } else if (repoUrl.startsWith('http:/github.com/')) {
            repoUrl = repoUrl.replace('http:/github.com/', 'https://github.com/');
        }
        // 2. Handle github.com/owner/repo
        else if (repoUrl.startsWith('github.com/')) {
            repoUrl = `https://${repoUrl}`;
        }
        // 3. Handle owner/repo
        else if (repoUrl.includes('/') && !repoUrl.startsWith('http')) {
            repoUrl = `https://github.com/${repoUrl}`;
        }

        // Validate and Set
        if (repoUrl.includes('github.com/') && repoUrl.split('/').length >= 4) {
             document.getElementById('repoUrl').value = repoUrl;
             // Auto-submit after a short delay
             setTimeout(() => {
                 ingestForm.dispatchEvent(new Event('submit'));
             }, 500);
        }
    };

    handleUrlSlug();

    window.addEventListener('popstate', (e) => {
        if (e.state && e.state.repoUrl) {
             document.getElementById('repoUrl').value = e.state.repoUrl;
             document.getElementById('scope').value = e.state.scope || 'all';
             document.getElementById('limit').value = e.state.limit || 20;
             document.getElementById('searchTerm').value = e.state.searchTerm || '';
             document.getElementById('includeLabels').value = (e.state.includeLabels || []).join(', ');
             
             if (e.state.searchIn) {
                 document.getElementById('searchInTitle').checked = e.state.searchIn.includes('title');
                 document.getElementById('searchInBody').checked = e.state.searchIn.includes('body');
                 document.getElementById('searchInComments').checked = e.state.searchIn.includes('comments');
             }
             ingestForm.dispatchEvent(new Event('submit'));
        } else {
             handleUrlSlug();
        }
    });

    // Handle Form Submission
    ingestForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        const repoUrl = document.getElementById('repoUrl').value.trim();
        const scope = document.getElementById('scope').value;
        const limit = parseInt(document.getElementById('limit').value);
        const token = document.getElementById('token').value.trim();
        
        // Search & Filters
        const searchTerm = document.getElementById('searchTerm').value.trim();
        const includeLabels = document.getElementById('includeLabels').value.split(',').map(l => l.trim()).filter(l => l !== "");
        
        const searchIn = [];
        if (document.getElementById('searchInTitle').checked) searchIn.push('title');
        if (document.getElementById('searchInBody').checked) searchIn.push('body');
        if (document.getElementById('searchInComments').checked) searchIn.push('comments');

        if (!repoUrl) return;

    // --- SYNC URL ---
    const cleanSlug = repoUrl.replace('https://github.com/', '').replace('http://github.com/', '').replace('github.com/', '');
    if (window.location.pathname !== `/${cleanSlug}`) {
        window.history.pushState({ repoUrl, scope, limit, searchTerm, includeLabels, searchIn }, '', `/${cleanSlug}`);
    }

        // UI State: Loading
        submitBtn.disabled = true;
        submitBtn.innerText = 'Analyzing...';
        resultsSection.style.display = 'block';
        loading.style.display = 'block';
        results.style.opacity = '0.3';
        results.style.pointerEvents = 'none';

        try {
            const response = await fetch('/api/analyze', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    repo_url: repoUrl,
                    scope: scope,
                    limit: limit,
                    token: token || null,
                    search_term: searchTerm || null,
                    search_in: searchIn,
                    include_labels: includeLabels.length > 0 ? includeLabels : null
                })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to analyze repository');
            }

            const data = await response.json();

            // UI State: Success
            updateUI(data);

        } catch (err) {
            console.error(err);
            alert(`Error: ${err.message}`);
        } finally {
            submitBtn.disabled = false;
            submitBtn.innerText = 'Analyze';
            loading.style.display = 'none';
            results.style.opacity = '1';
            results.style.pointerEvents = 'auto';
        }
    });

    function updateUI(data) {
        // 1. Summary
        document.getElementById('summaryText').value = data.summary;

        // 2. Full Context
        document.getElementById('fullContentText').value = data.full_content;

        // 3. Thread List
        const threadList = document.getElementById('threadList');
        threadList.innerHTML = '';
        
        if (data.threads && data.threads.length > 0) {
            data.threads.forEach(thread => {
                const li = document.createElement('li');
                li.style.padding = '12px';
                li.style.borderBottom = '1px solid #E5E7EB';
                li.style.display = 'flex';
                li.style.justifyContent = 'space-between';
                li.style.alignItems = 'center';

                const typeBadgeColor = thread.type === 'PR' ? '#8B5CF6' : '#06B6D4';
                
                li.innerHTML = `
                    <div style="flex-grow: 1;">
                        <span style="font-weight:700; color:var(--border-color); font-family:var(--font-mono);">#${thread.id}</span>
                        <span style="margin-left: 8px; font-weight:500;">${thread.title}</span>
                    </div>
                    <div style="display:flex; gap: 8px;">
                        <span style="background:${typeBadgeColor}; color:white; font-size:10px; font-weight:800; padding:2px 6px; border-radius:4px; box-shadow: 2px 2px 0 #000; border: 1px solid #000;">${thread.type}</span>
                        <span style="font-size:11px; opacity:0.6; font-weight:600;">${thread.status}</span>
                    </div>
                `;
                threadList.appendChild(li);
            });
        } else {
            threadList.innerHTML = '<li style="padding: 10px; opacity:0.5;">No results found for this selection.</li>';
        }
    }

    // Global copy function
    window.copyToClipboard = (elementId) => {
        const textArea = document.getElementById(elementId);
        if (textArea) {
            textArea.select();
            document.execCommand('copy');
            
            // Temporary feedback
            const btn = event.target;
            const originalText = btn.innerText;
            btn.innerText = 'Copied!';
            btn.style.backgroundColor = '#4ADE80';
            btn.style.color = 'white';
            setTimeout(() => {
                btn.innerText = originalText;
                btn.style.backgroundColor = '';
                btn.style.color = '';
            }, 2000);
        }
    };

    window.downloadResult = () => {
        const content = document.getElementById('fullContentText').value;
        const blob = new Blob([content], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'git-intel-digest.txt';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    };
});
