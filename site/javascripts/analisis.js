document.addEventListener('DOMContentLoaded', function() {
    const filterBtns = document.querySelectorAll('.holo-filter-btn');
    const cards = document.querySelectorAll('.holo-card[data-category]');
    const grid = document.getElementById('archivo-grid');

    if (!filterBtns.length || !grid) return;

    filterBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            // 1. Actualizar estado de los botones
            filterBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            // 2. Obtener el filtro seleccionado
            const filter = btn.getAttribute('data-filter');

            // 3. Filtrar las tarjetas con animación
            cards.forEach(card => {
                const category = card.getAttribute('data-category');
                
                // Si es "Todos" o la categoría coincide
                if (filter === 'all' || category === filter) {
                    card.style.display = 'flex';
                    // Pequeño delay para la animación de opacidad
                    setTimeout(() => {
                        card.style.opacity = '1';
                        card.style.transform = 'scale(1)';
                    }, 10);
                } else {
                    card.style.opacity = '0';
                    card.style.transform = 'scale(0.95)';
                    // Ocultar después de que termine la transición CSS
                    setTimeout(() => {
                        card.style.display = 'none';
                    }, 300);
                }
            });
        });
    });
});
