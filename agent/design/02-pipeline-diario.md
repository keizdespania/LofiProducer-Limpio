# Pipeline Diario (Hacer el Dia)

06:00 cron -> scripts/hacer_dia.py
  1. Lee config/nichos.json (canales activos)
  2. Para cada canal: investigador_redes -> predictor -> informe_detective
  3. Batch Kaggle (1 kernel ACE-Step con N canciones + 1 kernel Wan con N clips)
  4. Por canal: crear_paquete_blog (4 shorts + podcast)
  5. Encola shorts en cola_publicacion (Lun-Vie 13:00)
  6. Blog en borrador o publicar (quality gate >=8)
  7. Notificacion movil Dia preparado

Panel web view=hoy muestra resumen + boton Publicar Todo.
