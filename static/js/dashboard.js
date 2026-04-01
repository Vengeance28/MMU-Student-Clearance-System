/**
 * MMU Clearance System — Dashboard Polling (Objective i)
 * Auto-refreshes clearance status every 30 seconds via REST API.
 * Used as a standalone module; the dashboard template also has inline logic.
 */

const MMUDashboard = (() => {
  const API = '/api';
  let pollTimer = null;
  const POLL_INTERVAL = 30000; // 30 seconds

  function getToken() { return localStorage.getItem('mmu_token'); }
  function authHeaders() {
    return { 'Authorization': `Token ${getToken()}`, 'Content-Type': 'application/json' };
  }

  async function fetchClearanceStatus() {
    const res = await fetch(`${API}/student/clearance/status/`, { headers: authHeaders() });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  }

  function startPolling(onUpdate, onError) {
    stopPolling();
    pollTimer = setInterval(async () => {
      try {
        const data = await fetchClearanceStatus();
        onUpdate(data);
      } catch (err) {
        if (onError) onError(err);
      }
    }, POLL_INTERVAL);
  }

  function stopPolling() {
    if (pollTimer) { clearInterval(pollTimer); pollTimer = null; }
  }

  return { fetchClearanceStatus, startPolling, stopPolling };
})();
