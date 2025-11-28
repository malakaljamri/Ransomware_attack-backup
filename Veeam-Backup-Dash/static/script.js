// Auto-refresh data every 30 seconds
setInterval(() => {
    fetch('/api/data')
        .then(response => response.json())
        .then(data => {
            console.log('Data refreshed:', data);
        })
        .catch(error => console.error('Error refreshing data:', error));
}, 30000);

function updateBanner(status) {
    const banner = document.getElementById('rw-banner');
    if (!banner) return;
    const compromisedHtml = `
        <div id="rw-alert" class="metric-card danger" style="display:flex;align-items:center;justify-content:space-between;">
            <div>
                <h3>Active Ransomware Incident Detected</h3>
                <div class="metric-subtitle">Encrypted files or ransom note found in live folder</div>
            </div>
            <div>
                <button id="btn-restore" class="btn danger">Restore from Backup</button>
            </div>
        </div>`;
    const safeHtml = `
        <div id="rw-safe" class="metric-card success" style="display:flex;align-items:center;justify-content:space-between;">
            <div>
                <h3>No Active Incidents</h3>
                <div class="metric-subtitle">Live data healthy</div>
            </div>
            <div>
                <button id="btn-simulate" class="btn warning">Simulate Attack</button>
            </div>
        </div>`;
    banner.innerHTML = status === 'compromised' ? compromisedHtml : safeHtml;
    bindButtons();
}

function setResults(html) {
    const c = document.getElementById('simulation-results-container');
    if (c) c.innerHTML = html;
}

function setStatusLabel(text) {
    const s = document.getElementById('simulation-status');
    if (s) s.textContent = `Simulation Status: ${text}`;
}

function pollStatus() {
    fetch('/api/ransomware/status')
        .then(r => r.json())
        .then(s => {
            updateBanner(s.status);
            setStatusLabel(s.status);
        })
        .catch(err => console.error('Status error', err));
}

function simulateAttack() {
    fetch('/api/ransomware/simulate', { method: 'POST' })
        .then(r => r.json())
        .then(res => {
            setResults(`<pre>${JSON.stringify(res.result, null, 2)}</pre>`);
            updateBanner(res.status.status);
            setStatusLabel(res.status.status);
        })
        .catch(err => console.error('Simulate error', err));
}

function restoreFromBackup() {
    fetch('/api/ransomware/restore', { method: 'POST' })
        .then(r => r.json())
        .then(res => {
            setResults(`<pre>${JSON.stringify(res.result, null, 2)}</pre>`);
            updateBanner(res.status.status);
            setStatusLabel(res.status.status);
        })
        .catch(err => console.error('Restore error', err));
}

function bindButtons() {
    const sim = document.getElementById('btn-simulate');
    const rst = document.getElementById('btn-restore');
    if (sim) sim.onclick = simulateAttack;
    if (rst) rst.onclick = restoreFromBackup;
}

document.addEventListener('DOMContentLoaded', function() {
    console.log('Backup Dashboard loaded');
    bindButtons();
    pollStatus();
    setInterval(pollStatus, 5000);
});




// fetch('https://veeam-server:9398/api/v1/jobs', {
//     headers: {
//         'Authorization': 'Bearer <token>'
//     }
// })
// .then(res => res.json())
// .then(data => console.log('Real API data:', data))
