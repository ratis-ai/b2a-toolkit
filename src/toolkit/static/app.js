// Fetch and display logs
async function fetchLogs() {
    const toolFilter = document.getElementById('toolFilter').value;
    const statusFilter = document.getElementById('statusFilter').value;
    
    const queryParams = new URLSearchParams();
    if (toolFilter) queryParams.append('tool', toolFilter);
    if (statusFilter !== 'all') queryParams.append('status', statusFilter);
    
    const response = await fetch(`/api/logs?${queryParams}`);
    const logs = await response.json();
    
    const logsHtml = logs.map(log => {
        const status = log.error ? 
            `<span class="error">❌ Error</span>` : 
            `<span class="success">✓ Success</span>`;
            
        const copyCallId = `
            <div class="call-id" onclick="copyToClipboard('${log.call_id}')" title="Click to copy">
                ${log.call_id}
            </div>
        `;
        
        return `
            <div class="log-entry">
                <div style="display: flex; justify-content: space-between; align-items: start">
                    <div>
                        <h3>${log.tool_name}</h3>
                        <p>Time: ${new Date(log.timestamp).toLocaleString()}</p>
                        <p>Duration: ${log.duration_ms}ms ${status}</p>
                    </div>
                    <div>
                        ${copyCallId}
                    </div>
                </div>
                <pre>Inputs: ${JSON.stringify(log.inputs, null, 2)}</pre>
                ${log.outputs ? 
                    `<pre>Outputs: ${JSON.stringify(log.outputs, null, 2)}</pre>` : 
                    `<p style="color: red">Error: ${log.error}</p>`}
            </div>
        `;
    }).join('');
    
    document.getElementById('logs-list').innerHTML = logsHtml;
}

function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        // Could add a toast notification here
        console.log('Copied to clipboard:', text);
    });
}

// Add event listeners for filters
document.getElementById('toolFilter').addEventListener('input', fetchLogs);
document.getElementById('statusFilter').addEventListener('change', fetchLogs);

// Fetch logs initially and every 5 seconds
fetchLogs();
setInterval(fetchLogs, 5000); 