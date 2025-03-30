// Fetch and display logs
async function fetchLogs() {
    try {
        const response = await fetch('/api/logs');
        const logs = await response.json();
        displayLogs(logs);
    } catch (error) {
        console.error('Error fetching logs:', error);
    }
}

function displayLogs(logs) {
    const logsContainer = document.getElementById('logs-list');
    logsContainer.innerHTML = logs.map(log => `
        <div class="log-entry">
            <div class="log-header">
                <span class="timestamp">${new Date(log.timestamp).toLocaleString()}</span>
                <span class="tool-name">${log.tool_name}</span>
                <span class="duration">${log.duration_ms}ms</span>
            </div>
            <pre class="log-details">${JSON.stringify(log, null, 2)}</pre>
        </div>
    `).join('');
}

// Fetch logs initially and every 5 seconds
fetchLogs();
setInterval(fetchLogs, 5000); 