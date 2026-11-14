document.addEventListener('DOMContentLoaded', function() {
    const filterBtns = document.querySelectorAll('.holo-filter-btn');
    const rows = document.querySelectorAll('.glossary-row');
    const list = document.getElementById('glosario-list');

    if (!filterBtns.length || !list) return;

    function applyFilter(filter) {
        rows.forEach(row => {
            const category = row.getAttribute('data-category');
            if (filter === 'all' || category === filter) {
                row.style.display = 'block';
                setTimeout(() => { row.style.opacity = '1'; }, 10);
            } else {
                row.style.opacity = '0';
                setTimeout(() => { row.style.display = 'none'; }, 200);
            }
        });
    }

    function applyMechanism(mec) {
        rows.forEach(row => {
            const m = row.getAttribute('data-mecanismo');
            if (!mec || m === mec) {
                row.style.display = 'block';
                setTimeout(() => { row.style.opacity = '1'; }, 10);
            } else {
                row.style.opacity = '0';
                setTimeout(() => { row.style.display = 'none'; }, 200);
            }
        });
    }

    function bindBtns(selector, attr, applyFn, urlKey) {
        document.querySelectorAll(selector).forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll(selector).forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                const val = btn.getAttribute(attr);
                applyFn(val);
                const url = new URL(window.location);
                if (val === 'all' || !val) url.searchParams.delete(urlKey);
                else url.searchParams.set(urlKey, val);
                window.history.replaceState({}, '', url);
            });
        });
    }

    bindBtns('.holo-filter-btn[data-filter]', 'data-filter', applyFilter, 'filter');
    bindBtns('.holo-filter-btn[data-mechanism]', 'data-mechanism', applyMechanism, 'mec');

    const params = new URLSearchParams(window.location.search);
    const initialFilter = params.get('filter') || 'all';
    const initialBtn = document.querySelector('.holo-filter-btn[data-filter="' + initialFilter + '"]');
    if (initialBtn) initialBtn.click();
});
