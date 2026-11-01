// ═══ KEIZ OS · Notificaciones ═══
window.Notify = {
  async push(titulo, cuerpo){
    // Fallback: toast local
    App.toast(`${titulo}: ${cuerpo}`, 'info', 5000);
    // Notificación navegador si permitida
    if('Notification' in window && Notification.permission === 'granted'){
      new Notification(titulo, {body: cuerpo, icon: '/assets/logo.png'});
    }
  },
  pedirPermiso: async function(){
    if('Notification' in window && Notification.permission === 'default'){
      await Notification.requestPermission();
    }
  }
};
setTimeout(()=>Notify.pedirPermiso(), 3000);
