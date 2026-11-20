// ═══ KEIZ OS · Blogs SEO (real) ═══
window.Views = window.Views || {};
window.Views.blogs = {
  onEnter: function(){
    const v = document.getElementById('view-blogs');
    v.innerHTML = `
      <h1>📝 Centro Editorial</h1>
      <p class="text-muted mt-2 mb-6">Borradores reales + publicar en Blogger</p>
      <div class="card mb-6">
        <div class="flex gap-2" style="flex-wrap:wrap">
          <input id="blog-tema" class="input" style="flex:1;min-width:200px" placeholder="Tema (ej: OpenAI GPT-5)">
          <button class="btn btn-primary" onclick="Views.blogs.crear()">✍️ Redactar noticia</button>
          <button class="btn btn-ghost" onclick="Views.blogs.cargar()">🔄 Refresh</button>
        </div>
      </div>
      <div id="blogs-list"><div class="empty-state"><div class="spinner"></div></div></div>
    `;
    Views.blogs.cargar();
  },
  cargar: async function(){
    const el = document.getElementById('blogs-list');
    try {
      const r = await App.api('/api/borradores_blog').catch(()=>[]);
      const bs = Array.isArray(r) ? r : (r.borradores || r.files || []);
      if(!bs.length){ el.innerHTML = '<div class="empty-state"><div class="emoji">📝</div><p>Sin borradores</p></div>'; return; }
      el.innerHTML = `<div class="text-sm text-muted mb-4">${bs.length} borradores</div><div class="grid-2">${bs.map(b=>{
        const titulo = b.titulo || b.title || b.filename || b.id || 'Sin título';
        const resumen = b.resumen || b.summary || b.evaluacion || '';
        return `<div class="card">
          <div class="card-title mb-2">📄 ${String(titulo).substring(0,60)}</div>
          <p class="text-sm mb-4" style="max-height:80px;overflow:hidden">${String(resumen).substring(0,150)}</p>
          <div class="flex gap-2">
            <button class="btn btn-primary btn-sm" style="flex:1" onclick="Views.blogs.publicar('${b.filename||b.id||''}')">📤 Publicar</button>
            <button class="btn btn-danger btn-sm" onclick="Views.blogs.descartar('${b.filename||b.id||''}')">🗑</button>
          </div>
        </div>`;
      }).join('')}</div>`;
    } catch(e){ el.innerHTML = `<div class="empty-state"><p>${e.message}</p></div>`; }
  },
  crear: async function(){
    const tema = document.getElementById('blog-tema').value.trim();
    if(!tema){ App.toast('Escribe un tema','warning'); return; }
    App.toast('Redactando borrador (2-3 min)...','info',5000);
    try { await App.api('/api/crear_post_blog',{method:'POST',body:{tema}}); App.toast('Borrador creado ✅','success'); setTimeout(()=>Views.blogs.cargar(),3000); } catch(e){}
  },
  publicar: async function(f){
    if(!f){ App.toast('Falta filename','warning'); return; }
    if(!confirm('¿Publicar en Blogger?')) return;
    try { await App.api('/api/publicar_borrador',{method:'POST',body:{filename:f}}); App.toast('Publicado ✅','success'); Views.blogs.cargar(); } catch(e){}
  },
  descartar: async function(f){
    if(!confirm('¿Descartar?')) return;
    try { await App.api('/api/descartar_borrador',{method:'POST',body:{filename:f}}); App.toast('Descartado','info'); Views.blogs.cargar(); } catch(e){}
  }
};
