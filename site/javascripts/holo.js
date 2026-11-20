// EL ENCUADRE — Interacciones holográficas
document.addEventListener('DOMContentLoaded', () => {
  // Cursor glow (solo desktop)
  if (window.matchMedia('(hover: hover) and (pointer: fine)').matches) {
    const cursor = document.createElement('div');
    cursor.id = 'holo-cursor';
    document.body.appendChild(cursor);
    
    let mouseX = 0, mouseY = 0;
    let cursorX = 0, cursorY = 0;
    
    document.addEventListener('mousemove', (e) => {
      mouseX = e.clientX;
      mouseY = e.clientY;
    });
    
    function animate() {
      cursorX += (mouseX - cursorX) * 0.15;
      cursorY += (mouseY - cursorY) * 0.15;
      cursor.style.transform = `translate(${cursorX - 10}px, ${cursorY - 10}px)`;
      requestAnimationFrame(animate);
    }
    animate();
    
    // Efecto hover en links
    document.querySelectorAll('a, button').forEach(el => {
      el.addEventListener('mouseenter', () => {
        cursor.style.transform += ' scale(1.5)';
        cursor.style.borderColor = 'var(--holo-magenta)';
      });
      el.addEventListener('mouseleave', () => {
        cursor.style.borderColor = 'var(--holo-cyan)';
      });
    });
  }
  
  // Parallax sutil en imágenes
  const imgs = document.querySelectorAll('.md-typeset img');
  window.addEventListener('scroll', () => {
    const scrollY = window.scrollY;
    imgs.forEach(img => {
      const rect = img.getBoundingClientRect();
      if (rect.top < window.innerHeight && rect.bottom > 0) {
        const offset = (rect.top - window.innerHeight / 2) * 0.02;
        img.style.transform = `translateY(${offset}px)`;
      }
    });
  }, { passive: true });
});
