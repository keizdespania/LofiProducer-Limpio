(function() {
  function initAnalisisFilters() {
    const filterBtns = document.querySelectorAll('.holo-filter-btn[data-filter]');
    const cards = document.querySelectorAll('#archivo-grid .holo-card[data-category]');
    const grid = document.getElementById('archivo-grid');

    if (!filterBtns.length || !cards.length || !grid) return;

    filterBtns.forEach(btn => {
      if (btn.dataset.filterBound === '1') return;
      btn.dataset.filterBound = '1';

      btn.addEventListener('click', () => {
        filterBtns.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');

        const filter = btn.getAttribute('data-filter');

        cards.forEach(card => {
          if (card._hideTimer) {
            clearTimeout(card._hideTimer);
            card._hideTimer = null;
          }
          if (card._showTimer) {
            clearTimeout(card._showTimer);
            card._showTimer = null;
          }

          const category = card.getAttribute('data-category');
          const match = (filter === 'all' || category === filter);

          if (match) {
            card.style.display = 'flex';
            card._showTimer = setTimeout(() => {
              card.style.opacity = '1';
              card.style.transform = 'scale(1)';
            }, 15);
          } else {
            card.style.opacity = '0';
            card.style.transform = 'scale(0.95)';
            card._hideTimer = setTimeout(() => {
              card.style.display = 'none';
            }, 250);
          }
        });
      });
    });
  }

  document.addEventListener('DOMContentLoaded', initAnalisisFilters);
  if (typeof document$ !== 'undefined' && document$ && typeof document$.subscribe === 'function') {
    document$.subscribe(initAnalisisFilters);
  }
})();
