// Global ripple effect for buttons and subtle glow class auto-attach
(function(){
  function createRipple(e){
    const btn = e.currentTarget;
    // Create ripple element
    const ripple = document.createElement('span');
    ripple.className = 'btn-ripple';

    // Dark ripple for dark buttons
    const btnBg = window.getComputedStyle(btn).backgroundColor || '';
    const isDark = btnBg && btnBg !== 'rgba(0, 0, 0, 0)' && btn.classList.contains('btn-outline') === false && btn.classList.contains('btn-light') === false;
    if(isDark) ripple.classList.add('dark');

    const rect = btn.getBoundingClientRect();
    const size = Math.max(rect.width, rect.height) * 2;
    ripple.style.width = ripple.style.height = size + 'px';

    const x = e.clientX - rect.left - size/2;
    const y = e.clientY - rect.top - size/2;
    ripple.style.left = x + 'px';
    ripple.style.top = y + 'px';

    btn.appendChild(ripple);

    requestAnimationFrame(() => {
      ripple.style.transition = 'transform 600ms cubic-bezier(.21,.8,.3,1), opacity 600ms ease-out';
      ripple.style.transform = 'scale(1)';
      ripple.style.opacity = '0';
      ripple.style.animation = 'ripple-effect 600ms ease-out forwards';
    });

    // Cleanup
    setTimeout(() => {
      try { ripple.remove(); } catch (err) { if (ripple.parentNode) ripple.parentNode.removeChild(ripple); }
    }, 700);
  }

  function attachToButtons(){
    // Enhance typical action buttons
    const selectors = ['.btn', '.btn-action', '.btn-primary', '.btn-success', '.btn-danger', '.btn-outline-danger', '.btn-outline-primary'];
    const els = new Set();
    selectors.forEach(s => document.querySelectorAll(s).forEach(el => els.add(el)));

    els.forEach(btn => {
      // Add glow class if not present
      if(!btn.classList.contains('btn-action-glow')) btn.classList.add('btn-action-glow');

      // Avoid duplicate listeners
      if(!btn.__rippleBound){
        btn.addEventListener('click', createRipple);
        btn.__rippleBound = true;
      }
    });
  }

  // Attach on DOM ready and on dynamic changes
  if(document.readyState === 'loading'){
    document.addEventListener('DOMContentLoaded', attachToButtons);
  } else {
    attachToButtons();
  }

  // Re-scan on AJAX/DOM changes - simple polling to pick up new buttons (cheap and safe)
  let lastCount = document.querySelectorAll('button, a.btn').length;
  setInterval(() => {
    const count = document.querySelectorAll('button, a.btn').length;
    if(count !== lastCount){ lastCount = count; attachToButtons(); }
  }, 1200);
})();
