
// El Encuadre — animaciones
document.addEventListener('DOMContentLoaded', function() {
    // Fade-in al scroll
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
            }
        });
    }, { threshold: 0.1 });

    document.querySelectorAll('h2, h3, p, .analysis-card').forEach(el => {
        el.classList.add('fade-in');
        observer.observe(el);
    });

    // Parallax sutil en el hero
    const hero = document.querySelector('.hero');
    if (hero) {
        window.addEventListener('scroll', () => {
            const scrolled = window.pageYOffset;
            hero.style.transform = `translateY(${scrolled * 0.3}px)`;
        });
    }

    // Cursor personalizado (opcional)
    console.log('🎯 El Encuadre cargado');
});
