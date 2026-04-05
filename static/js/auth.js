/**
 * MMU Clearance — Shared Auth Helper
 * Prevents redirect loops by verifying token once per page load.
 */
const MMUAuth = {
  token: () => localStorage.getItem('mmu_token'),
  user: () => { try { return JSON.parse(localStorage.getItem('mmu_user') || 'null'); } catch(e) { return null; } },

  clearSession() {
    localStorage.removeItem('mmu_token');
    localStorage.removeItem('mmu_user');
  },

  // Call on protected staff pages — redirects ONCE to login if not authenticated
  requireStaff() {
    const token = this.token();
    const user = this.user();
    if (!token || !user || !user.staff_number) {
      this.clearSession();
      if (window.location.pathname !== '/staff/login/') {
        window.location.replace('/staff/login/');
      }
      return false;
    }
    return true;
  },

  // Call on protected student pages
  requireStudent() {
    const token = this.token();
    const user = this.user();
    if (!token || !user || !user.reg_number) {
      this.clearSession();
      if (window.location.pathname !== '/login/') {
        window.location.replace('/login/');
      }
      return false;
    }
    return true;
  },

  // Call on login pages — redirect away if already logged in
  redirectIfStaffLoggedIn() {
    const token = this.token();
    const user = this.user();
    if (token && user && user.staff_number && window.location.pathname !== '/staff/dashboard/') {
      window.location.replace('/staff/dashboard/');
      return true;
    }
    return false;
  },

  redirectIfStudentLoggedIn() {
    const token = this.token();
    const user = this.user();
    if (token && user && user.reg_number && window.location.pathname !== '/dashboard/') {
      window.location.replace('/dashboard/');
      return true;
    }
    return false;
  },

  headers() {
    return { 'Authorization': 'Token ' + this.token(), 'Content-Type': 'application/json' };
  },

  async logout(redirectTo) {
    try {
      await fetch('/api/auth/logout/', { method: 'POST', headers: this.headers() });
    } catch(e) {}
    this.clearSession();
    window.location.replace(redirectTo || '/login/');
  }
};
