document.addEventListener('DOMContentLoaded', function () {
  const pageType = document.body.dataset.accountType || '';
  const forms = document.querySelectorAll('form');

  forms.forEach((form) => {
    form.addEventListener('submit', async function (event) {
      event.preventDefault();

      const username = form.querySelector('input[name="username"]')?.value?.trim();
      const password = form.querySelector('input[name="password"]')?.value || '';
      const name = form.querySelector('input[name="name"]')?.value?.trim() || '';
      const account = pageType || form.querySelector('select[name="account"]')?.value || 'Login One';

      const endpoint = form.dataset.authAction === 'signup' ? '/api/auth/signup' : '/api/auth/login';
      const payload = form.dataset.authAction === 'signup'
        ? { name, username, password, account_type: account }
        : { username, password, account_type: account };

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'same-origin',
        body: JSON.stringify(payload)
      });

      const result = await response.json().catch(() => ({ error: 'Request failed.' }));
      if (!response.ok) {
        alert(result.error || 'Authentication failed.');
        return;
      }

      if (result.token) {
        localStorage.setItem('auth_token', result.token);
      }

   window.location.href = '/frontend/pages/dashboard/index.html';
    });
  });

  const logoutButton = document.querySelector('[data-logout]');
  if (logoutButton) {
    logoutButton.addEventListener('click', async function () {
      const token = localStorage.getItem('auth_token');
      if (!token) {
       window.location.href = '/homepage.html';
    
  
        return;
      }

      await fetch('/api/auth/logout', {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
        credentials: 'same-origin'
      });

      localStorage.removeItem('auth_token');
     window.location.href = '/homepage.html';
    });
  }
});
