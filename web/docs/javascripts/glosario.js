document.addEventListener('DOMContentLoaded', function() {
    const filterBtns = document.querySelectorAll('.holo-filter-btn');
    const rows = document.querySelectorAll('.glossary-row');
    const list = document.getElementById('glosario-list');

    if (!filterBtns.length || !list) return;

    filterBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            filterBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            const filter = btn.getAttribute('data-filter');

            rows.forEach(row => {
                const category = row.getAttribute('data-category');
                
                if (filter === 'all' || category === filter) {
                    row.style.display = 'block';
                    setTimeout(() => {
                        row.style.opacity = '1';
                    }, 10);
                } else {
                    row.style.opacity = '0';
                    setTimeout(() => {
                        row.style.display = 'none';
                    }, 200);
                }
            });
        });
    });
});
