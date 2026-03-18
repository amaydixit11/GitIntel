document.addEventListener('DOMContentLoaded', () => {
    const ingestForm = document.getElementById('ingestForm');
    const submitBtn = document.getElementById('submitBtn');
    const resultsSection = document.getElementById('resultsSection');
    const loading = document.getElementById('loading');
    const results = document.getElementById('results');
    const isPrivate = document.getElementById('isPrivate');
    const tokenContainer = document.getElementById('tokenContainer');
    const graphSection = document.getElementById('graphSection');
    const resetGraphBtn = document.getElementById('resetGraphBtn');

    let currentRequest = null;
    let isInitialLoad = true;
    let graphSimulation = null;

    // Toggle private repo token field
    isPrivate.addEventListener('change', (e) => {
        tokenContainer.style.display = e.target.checked ? 'block' : 'none';
    });

    const handleUrlSlug = () => {
        const urlParams = new URLSearchParams(window.location.search);
        let repoUrl = urlParams.get('repo_url') || urlParams.get('url');
        
        if (!repoUrl) {
            let path = window.location.pathname.substring(1); 
            if (!path || path === "" || path.startsWith('static') || path.startsWith('api')) return;
            path = path.replace(/\/$/, "");
            repoUrl = decodeURIComponent(path);
        }

        if (repoUrl) {
            if (repoUrl.includes('/') && !repoUrl.startsWith('http')) {
                if (!repoUrl.includes('github.com')) {
                    repoUrl = `https://github.com/${repoUrl}`;
                } else {
                    repoUrl = `https://${repoUrl}`;
                }
            } else if (repoUrl.startsWith('https:/github.com/')) {
                 repoUrl = repoUrl.replace('https:/github.com/', 'https://github.com/');
            }

            if (repoUrl.includes('github.com/') && repoUrl.split('/').length >= 4) {
                 document.getElementById('repoUrl').value = repoUrl;
                 if (isInitialLoad) {
                     isInitialLoad = false;
                     triggerAnalysis();
                 }
            }
        }
    };

    const triggerAnalysis = () => {
        ingestForm.dispatchEvent(new Event('submit', { cancelable: true }));
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

             if (e.state.issueStates) {
                 document.getElementById('issueOpen').checked = e.state.issueStates.includes('OPEN');
                 document.getElementById('issueClosed').checked = e.state.issueStates.includes('CLOSED');
             }
             if (e.state.prStates) {
                 document.getElementById('prOpen').checked = e.state.prStates.includes('OPEN');
                 document.getElementById('prMerged').checked = e.state.prStates.includes('MERGED');
                 document.getElementById('prClosed').checked = e.state.prStates.includes('CLOSED');
             }

             doAnalysis();
        }
    });

    ingestForm.onsubmit = (e) => {
        e.preventDefault();
        doAnalysis();
        return false;
    };

    const doAnalysis = async () => {
        const repoUrl = document.getElementById('repoUrl').value.trim();
        const scope = document.getElementById('scope').value;
        const limit = parseInt(document.getElementById('limit').value);
        const token = document.getElementById('token').value.trim();
        const searchTerm = document.getElementById('searchTerm').value.trim();
        const includeLabels = document.getElementById('includeLabels').value.split(',').map(l => l.trim()).filter(l => l !== "");
        
        const searchIn = [];
        if (document.getElementById('searchInTitle').checked) searchIn.push('title');
        if (document.getElementById('searchInBody').checked) searchIn.push('body');
        if (document.getElementById('searchInComments').checked) searchIn.push('comments');

        const issueStates = [];
        if (document.getElementById('issueOpen').checked) issueStates.push('OPEN');
        if (document.getElementById('issueClosed').checked) issueStates.push('CLOSED');

        const prStates = [];
        if (document.getElementById('prOpen').checked) prStates.push('OPEN');
        if (document.getElementById('prMerged').checked) prStates.push('MERGED');
        if (document.getElementById('prClosed').checked) prStates.push('CLOSED');

        if (!repoUrl) return;

        if (currentRequest) currentRequest.abort();
        const controller = new AbortController();
        currentRequest = controller;

        const cleanSlug = repoUrl.replace('https://github.com/', '').replace('http://github.com/', '').replace('github.com/', '');
        const targetPath = `/${cleanSlug}`;
        if (window.location.pathname !== targetPath) {
            window.history.pushState({ repoUrl, scope, limit, searchTerm, includeLabels, searchIn, issueStates, prStates }, '', targetPath);
        }

        submitBtn.disabled = true;
        submitBtn.innerText = 'Analyzing...';
        resultsSection.style.display = 'block';
        loading.style.display = 'block';
        results.style.opacity = '0.3';
        results.style.pointerEvents = 'none';
        graphSection.style.display = 'none';

        try {
            const response = await fetch('/api/analyze', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                signal: controller.signal,
                body: JSON.stringify({
                    repo_url: repoUrl,
                    scope: scope, 
                    limit: limit,
                    token: token || null,
                    search_term: searchTerm || null,
                    search_in: searchIn,
                    include_labels: includeLabels.length > 0 ? includeLabels : null,
                    issue_states: issueStates,
                    pr_states: prStates
                })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to analyze repository');
            }

            const data = await response.json();
            updateUI(data);
        } catch (err) {
            if (err.name === 'AbortError') return;
            console.error(err);
            alert(`Error: ${err.message}`);
        } finally {
            submitBtn.disabled = false;
            submitBtn.innerText = 'Analyze';
            loading.style.display = 'none';
            results.style.opacity = '1';
            results.style.pointerEvents = 'auto';
            currentRequest = null;
        }
    };

    function updateUI(data) {
        document.getElementById('summaryText').value = data.summary;
        document.getElementById('fullContentText').value = data.full_content;
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

        // Render Knowledge Graph if data exists
        if (data.graph && data.graph.nodes.length > 0) {
            graphSection.style.display = 'block';
            setTimeout(() => renderKnowledgeGraph(data.graph), 100);
        }
    }

    function renderKnowledgeGraph(graphData) {
        const svg = d3.select("#knowledgeGraph");
        svg.selectAll("*").remove(); // Clear previous

        const width = svg.node().getBoundingClientRect().width;
        const height = svg.node().getBoundingClientRect().height;

        const g = svg.append("g");

        // Zoom setup
        const zoom = d3.zoom()
            .scaleExtent([0.1, 4])
            .on("zoom", (event) => g.attr("transform", event.transform));

        svg.call(zoom);

        resetGraphBtn.onclick = () => {
            svg.transition().duration(750).call(zoom.transform, d3.zoomIdentity);
        };

        const simulation = d3.forceSimulation(graphData.nodes)
            .force("link", d3.forceLink(graphData.links).id(d => d.id).distance(100))
            .force("charge", d3.forceManyBody().strength(-300))
            .force("center", d3.forceCenter(width / 2, height / 2))
            .force("collision", d3.forceCollide().radius(40));

        graphSimulation = simulation;

        // Links
        const link = g.append("g")
            .attr("stroke", "#94a3b8")
            .attr("stroke-opacity", 0.6)
            .attr("stroke-width", 2)
            .selectAll("line")
            .data(graphData.links)
            .join("line")
            .attr("marker-end", "url(#arrowhead)");

        // Arrowhead
        svg.append("defs").append("marker")
            .attr("id", "arrowhead")
            .attr("viewBox", "0 -5 10 10")
            .attr("refX", 25)
            .attr("refY", 0)
            .attr("markerWidth", 6)
            .attr("markerHeight", 6)
            .attr("orient", "auto")
            .append("path")
            .attr("d", "M0,-5L10,0L0,5")
            .attr("fill", "#94a3b8");

        // Nodes
        const node = g.append("g")
            .selectAll("g")
            .data(graphData.nodes)
            .join("g")
            .call(drag(simulation));

        // Node Circles
        node.append("circle")
            .attr("r", d => d.type === 'Issue' ? 12 : 14)
            .attr("fill", d => d.type === 'PR' ? '#8B5CF6' : '#06B6D4')
            .attr("stroke", "#000")
            .attr("stroke-width", 2)
            .style("box-shadow", "3px 3px 0 rgba(0,0,0,0.2)");

        // Node Labels (#ID)
        node.append("text")
            .attr("dy", 4)
            .attr("text-anchor", "middle")
            .attr("font-size", "9px")
            .attr("font-weight", "800")
            .attr("fill", "white")
            .attr("pointer-events", "none")
            .text(d => d.id);

        // Hover Effect / Tooltip
        const tooltip = d3.select("#graphTooltip");
        node.on("mouseover", (event, d) => {
            tooltip.style("display", "block")
                .html(`<strong>#${d.id} (${d.type})</strong><br/>${d.title}<br/><em>Status: ${d.state}</em>`);
            d3.select(event.currentTarget).select("circle").attr("r", 18);
        })
        .on("mousemove", (event) => {
            tooltip.style("left", (event.pageX + 10) + "px")
                .style("top", (event.pageY - 10) + "px");
        })
        .on("mouseout", (event) => {
            tooltip.style("display", "none");
            d3.select(event.currentTarget).select("circle").attr("r", d => d.type === 'Issue' ? 12 : 14);
        });

        simulation.on("tick", () => {
            link
                .attr("x1", d => d.source.x)
                .attr("y1", d => d.source.y)
                .attr("x2", d => d.target.x)
                .attr("y2", d => d.target.y);

            node.attr("transform", d => `translate(${d.x},${d.y})`);
        });

        function drag(simulation) {
            function dragstarted(event) {
                if (!event.active) simulation.alphaTarget(0.3).restart();
                event.subject.fx = event.subject.x;
                event.subject.fy = event.subject.y;
            }
            function dragged(event) {
                event.subject.fx = event.x;
                event.subject.fy = event.y;
            }
            function dragended(event) {
                if (!event.active) simulation.alphaTarget(0);
                event.subject.fx = null;
                event.subject.fy = null;
            }
            return d3.drag()
                .on("start", dragstarted)
                .on("drag", dragged)
                .on("end", dragended);
        }
    }

    window.copyToClipboard = (elementId) => {
        const el = document.getElementById(elementId);
        if (!el) return;
        
        let text = el.value || el.innerText;
        navigator.clipboard.writeText(text).then(() => {
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
        });
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
