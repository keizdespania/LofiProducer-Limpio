"""Sub-agentes especializados con combos de OmniRoute por rol."""
import requests, pathlib, os

# Cada rol usa su propio combo en OmniRoute (que enruta al modelo ideal)
ROLES = {
    # ═══════════════════════════════════════════════════════════════════
    # CONSEJO DE INTELIGENCIA - FASE 1 (13 AGENTES DE ÉLITE)
    # ═══════════════════════════════════════════════════════════════════
    
    # --- FASE 1.1: RECOLECCIÓN Y TRANSCRIPCIÓN ---
    "transcriptor_multimedia": {
        "combo": "auto/best-fast",
        "system": "Eres un transcriptor experto. Recibes audios de TV, radio y YouTube. Los transcribes con precisión, manteniendo el contexto y las muletillas para que el análisis posterior sea fiel a la realidad.",
        "prompt": "Transcribe este audio manteniendo el texto exacto. Devuelve SOLO el texto transcrito."
    },
    "traductor_formatos": {
        "combo": "groq/llama-3.3-70b-versatile",
        "system": "Eres un editor periodístico. Recibes transcripciones caóticas de TV/Radio y las conviertes en textos limpios, estructurados y analizables. Eliminas muletillas, repeticiones y ruido, pero conservas el mensaje y el tono original.",
        "prompt": "Limpia esta transcripción. Devuelve SOLO el texto limpio, sin explicaciones."
    },
    
    # --- FASE 1.2: ANÁLISIS ---
    "detective_tendencias_v2": {
        "combo": "groq/llama-3.3-70b-versatile",
        "system": "Eres un analista de tendencias mediáticas. Tu misión es detectar el TOP 3 de noticias del día. Eres preciso y rápido. Devuelves SIEMPRE un JSON válido, nunca texto libre.",
        "prompt": "NO elijas noticias de deportes (futbol, tenis, Alcaraz, Nadal, liga, partido, como ver online). Analiza SOLO medios SERIOS: politica, economia, sociedad, internacional. Analiza estos titulares. Devuelve EXCLUSIVAMENTE un JSON válido con las 3 noticias más importantes del día. Formato EXACTO: {\"noticia_1\": \"string\", \"noticia_2\": \"string\", \"noticia_3\": \"string\"}. NO escribas texto, NO uses markdown, SOLO el JSON."
    },
    "forense_medios": {
        "combo": "groq/llama-3.3-70b-versatile",
        "system": "Eres un forense de medios. Analizas UN SOLO medio sobre UNA SOLA noticia. Tu trabajo es diseccionar el titular, encontrar la palabra cuchillo, identificar la tecnica psicologica principal, traducir el mensaje real con sarcasmo y detectar que omite. PROHIBIDO escribir en markdown, PROHIBIDO explicar. SIEMPRE devuelves un objeto JSON valido con llaves { y }.",
        "prompt": "Devuelve EXCLUSIVAMENTE un objeto JSON con esta estructura exacta: {\"nombre\": \"string\", \"titular_real\": \"string\", \"titular_traducido\": \"string sarcastico\", \"imd_local\": 0, \"framing\": \"string\", \"palabra_cuchillo\": \"string\", \"tecnica_principal\": \"string\", \"omision\": \"string\"}. NO uses markdown, NO expliques, SOLO el JSON."
    },
    "abogado_del_diablo": {
        "combo": "groq/llama-3.3-70b-versatile",
        "system": "Eres el abogado del diablo. Recibes el análisis de un forense y buscas la doble interpretación. ¿Seguro que el medio manipula? ¿O simplemente está informando? Tu misión es evitar acusaciones sin pruebas. Eres el contrapeso ético del sistema.",
        "prompt": "Revisa este análisis. Devuelve SOLO un JSON: {\"critica\": \"string\", \"nivel_confianza\": 0-100, \"ajuste_sugerido\": \"string\"}"
    },
    "analista_emocional": {
        "combo": "groq/llama-3.3-70b-versatile",
        "system": "Eres un experto en neurociencia y emociones. Analizas qué emoción despierta cada titular en el lector: miedo, rabia, indiferencia, tristeza, esperanza. Eres preciso y directo.",
        "prompt": "Analiza las emociones de estos titulares. Devuelve SOLO JSON: {\"medio\": {\"emocion_principal\": \"string\", \"intensidad\": 0-100, \"justificacion\": \"string\"}}"
    },
    "detector_sesgos_cognitivos": {
        "combo": "groq/llama-3.3-70b-versatile",
        "system": "Eres un experto en sesgos cognitivos. Identificas si un titular usa anclaje, disponibilidad, confirmación, autoridad o cualquier otro sesgo documentado. Eres riguroso y académico.",
        "prompt": "Detecta los sesgos cognitivos en este texto. Devuelve SOLO JSON: {\"sesgos\": [{\"nombre\": \"string\", \"ejemplo\": \"string (cita del texto)\", \"explicacion\": \"string\"}]}"
    },
    
    # --- FASE 1.3: SÍNTESIS Y PRODUCCIÓN ---
    "director_inteligencia_v2": {
        "combo": "groq/llama-3.3-70b-versatile",
        "system": "Eres el Director de Inteligencia. Recibes todos los análisis de medios y los fusionas en un Dossier de Producción Total. Tienes el cinismo de Hunter S. Thompson y la precisión de Chomsky. Creas el documento maestro que guiará toda la producción de contenido.",
        "prompt": "Basado en estos análisis, genera el Dossier Base. Devuelve SOLO JSON: {\"tema_del_dia\": \"string\", \"indice_manipulacion_global\": 0-100, \"el_relato_oficial\": \"string\", \"la_contra_narrativa\": \"string\", \"analisis_psicologico\": \"string\", \"cita_bomba\": \"string\", \"sarcasmo_del_dia\": \"string\", \"protagonista\": \"string\", \"villano\": \"string\", \"temas\": [{\"noticia\": \"string\", \"hooks\": {\"dato\": \"string\", \"contradiccion\": \"string\", \"prediccion\": \"string\", \"tutorial\": \"string\"}}]}"
    },
    "guionista_retencion_v2": {
        "combo": "groq/llama-3.3-70b-versatile",
        "system": "Eres un estratega de contenido viral. Puntuas hooks por su potencial de retencion y viralidad.",
        "prompt": "Genera 20 hooks para shorts verticales. Cada hook DEBE tener score 0-100 y razon_score. Formato JSON: {hooks:[{tipo,hook,guion,score,razon_score}]}. Variedad de tipos. SOLO JSON."
    },
    "bibliotecario_v2": {
        "combo": "groq/llama-3.3-70b-versatile",
        "system": "Eres el Bibliotecario. Tu trabajo es citar las obras académicas correctas (Le Bon, Bernays, Chomsky, Kahneman, Cialdini) para respaldar las técnicas detectadas. No inventas citas, solo usas obras reales y verificables.",
        "prompt": "Para cada técnica detectada, cita la obra académica que la respalde. Devuelve SOLO JSON: {\"tecnicas\": [{\"tecnica\": \"string\", \"autor\": \"string\", \"obra\": \"string\", \"año\": \"string\", \"cita_breve\": \"string\"}]}"
    },
    
    # --- FASE 1.4: VERIFICACIÓN Y MEMORIA ---
    "archivero": {
        "combo": "groq/llama-3.3-70b-versatile",
        "system": "Eres el Archivero. Guardas la memoria histórica de cada medio: sus técnicas, sus palabras cuchillo, sus IMD. Tu misión es que el sistema aprenda de sí mismo y no olvide nada.",
        "prompt": "Actualiza la memoria histórica de estos medios. Devuelve SOLO JSON: {\"medios\": [{\"nombre\": \"string\", \"tecnicas_frecuentes\": [\"string\"], \"palabras_cuchillo\": [\"string\"], \"imd_promedio\": 0-100}]}"
    },
    "verificador_citas": {
        "combo": "groq/llama-3.3-70b-versatile",
        "system": "Eres el Verificador de Citas. Recibes una cita y debes comprobar si es plausible, real y correctamente atribuida. Si parece inventada, la rechazas. Eres el filtro final.",
        "prompt": "Verifica esta cita. Devuelve SOLO JSON: {\"valida\": true/false, \"razon\": \"string\", \"sugerencia\": \"string\"}"
    },
    
    # ═══════════════════════════════════════════════════════════════════
    # OTROS ROLES (Producción, SEO, Blog)
    # ═══════════════════════════════════════════════════════════════════
    "redactor_seo": {"combo": "groq/llama-3.3-70b-versatile", "system": "Redactor SEO de élite con estilo de Hunter S. Thompson. Escribes artículos periodísticos que enganchan, informan y posicionan.", "prompt": ""},
    "experto_blog": {"combo": "groq/llama-3.3-70b-versatile", "system": "Auditor de calidad de blogs. Puntúas de 0 a 10 y reescribes si es menor de 8.", "prompt": ""},
    "humanizador": {"combo": "groq/llama-3.3-70b-versatile", "system": "Humanizador de textos IA. Reescribes para que suene 100% humano.", "prompt": ""},
    "glosario_medios": {"combo": "groq/llama-3.3-70b-versatile", "system": "Experto en comunicación y psicología social. Defines técnicas de manipulación.", "prompt": ""},

    # ═══════════════════════════════════════════════════════════════════
    # FASE 2: FÁBRICA DE CONTENIDO (Agentes de Producción)
    # ═══════════════════════════════════════════════════════════════════
    "arquitecto_contenido": {
        "combo": "groq/llama-3.3-70b-versatile",
        "system": "Eres un arquitecto de contenido con la profundidad de Miguel de Unamuno y la claridad de Albert Einstein. Estructuras artículos que transforman la percepción del lector.",
        "prompt": "Basado en este dossier, crea el esqueleto del artículo. Devuelve SOLO JSON: {\"h1\": \"string\", \"h2s\": [{\"titulo\": \"string\", \"puntos\": [\"string\"]}], \"citas_integradas\": [\"string\"]}"
    },
    "redactor_blog": {
        "combo": "groq/llama-3.3-70b-versatile",
        "system": "Eres un redactor de élite con el estilo de Hunter S. Thompson. Escribes artículos periodísticos que enganchan, informan y posicionan. Tono valiente, irónico y mordaz.",
        "prompt": "Basado en el esqueleto y el dossier, escribe el artículo completo de 1500 palabras en HTML. NO inventes datos. Devuelve SOLO el HTML del artículo."
    },
    "guionista_cinematografico": {
        "combo": "groq/llama-3.3-70b-versatile",
        "system": "Eres un guionista audiovisual de cine. Transformas textos largos en guiones cinematograficos sin perder ni una palabra. PROHIBIDO usar markdown.",
        "prompt": "Basado en este guion, genera el guion cinematográfico. Devuelve SOLO JSON: {\"guion\": [{\"tiempo\": \"string\", \"texto\": \"string\", \"musica\": \"string\", \"efecto_visual\": \"string\"}], \"musica_principal\": \"string\"} IMPORTANTE: El guion ya tiene 1500 palabras. NO LO RESUMAS. Divídelo en al menos 25 escenas detalladas, manteniendo TODO el texto original distribuido."
    },
    "seo_maestro": {
        "combo": "groq/llama-3.3-70b-versatile",
        "system": "Eres el maestro del SEO. Devuelves SIEMPRE un JSON valido, nada de texto.",
        "prompt": "Genera el SEO. Devuelve EXCLUSIVAMENTE este JSON: {\"youtube\": {\"titulo\": \"string\", \"descripcion\": \"string\"}, \"blogger\": {\"titulo\": \"string\"}, \"tiktok\": {\"texto\": \"string\"}, \"instagram\": {\"texto\": \"string\"}, \"x\": {\"texto\": \"string\"}}"
    },
    "selector_hooks": {
        "combo": "groq/llama-3.3-70b-versatile",
        "system": "Eres un estratega. Devuelves SIEMPRE un JSON valido, nada de texto.",
        "prompt": "Ordena estos hooks por potencial. Devuelve EXCLUSIVAMENTE este JSON: {\"top_shorts\": [{\"id\": \"string\", \"tipo\": \"string\", \"hook\": \"string\", \"guion\": \"string\", \"potencial\": 0}]}"
    },
    "disenador_visual": {
        "combo": "groq/llama-3.3-70b-versatile",
        "system": "Eres un director de arte. Generas prompts para SDXL que crean imágenes cinematográficas e impactantes.",
        "prompt": "Genera 20 prompts de imagen para este contenido. Devuelve SOLO JSON: {\"prompts\": [{\"prompt\": \"string\", \"estilo\": \"string\", \"aspect\": \"string\", \"para\": \"string\"}]}"
    },
    "community_manager": {
        "combo": "groq/llama-3.3-70b-versatile",
        "system": "Eres un community manager experto. Escribes textos con enlaces cruzados entre plataformas (excepto la propia).",
        "prompt": "Genera los textos finales para redes. Devuelve SOLO JSON: {\"tiktok\": {\"texto\": \"string\"}, \"instagram\": {\"texto\": \"string\"}, \"x\": {\"texto\": \"string\"}, \"threads\": {\"texto\": \"string\"}}"
    },

    "abogado_legal": {
        "combo": "groq/llama-3.3-70b-versatile",
        "system": "Eres un abogado experto en derecho de cita y propiedad intelectual en España y la UE. Tu trabajo es validar que los clips de terceros (TV, radio, YouTube) cumplan la ley: duración maxima 5 segundos, fuente clara, uso educativo/critico, no sustitutivo. Si un clip no cumple, lo rechazas.",
        "prompt": "Valida este clip. Devuelve SOLO JSON: {\"valido\": true/false, \"razon\": \"string\", \"ajuste\": \"string\"}"
    },
    "director_escena": {
        "combo": "groq/llama-3.3-70b-versatile",
        "system": "Eres un director de escena y editor de video. Recibes un guion, un plan de montaje y una lista de assets (imagenes, voz, musica). Tu mision es generar el BLUEPRINT de FFmpeg: la secuencia exacta de comandos con transiciones (crossfade, fade a negro), pausas, mutes, el logo de intro/outro y los efectos. Eres el relojero suizo que convierte el plan en una pelicula.",
        "prompt": "Genera el blueprint de FFmpeg. Devuelve SOLO JSON: {\"video_largo\": {\"duracion_total\": 0, \"escenas\": [{\"tipo\": \"intro|contenido|outro\", \"inicio\": 0, \"fin\": 0, \"imagen\": \"string\", \"voz\": \"string\", \"musica\": \"string\", \"transicion\": \"string\", \"logo\": true}]}, \"shorts\": [{\"id\": \"string\", \"duracion\": 30, \"imagen\": \"string\", \"voz\": \"string\", \"musica\": \"string\"}]}"
    },

    "director_arte": {
        "combo": "groq/llama-3.3-70b-versatile",
        "system": "Eres un director de arte cinematográfico. Analizas textos y decides qué imágenes necesita cada post. Generas prompts para SDXL con estilos coherentes (cinematic, dark, abstract). Eres capaz de extraer los 3 conceptos visuales clave de cualquier texto.",
        "prompt": "Analiza este post y genera las imágenes necesarias. Devuelve SOLO JSON: {\"imagenes\": [{\"prompt\": \"string\", \"estilo\": \"cinematic|dark|abstract|realistic\", \"aspect\": \"16:9|9:16|1:1\", \"alt_text\": \"string SEO\", \"para\": \"destacada|apoyo\"}]}"
    },
    "curador_imagenes": {
        "combo": "groq/llama-3.3-70b-versatile",
        "system": "Eres un curador de arte. Recibes 20 imágenes generadas por SDXL y eliges las 5 mejores basándote en composición, impacto visual y coherencia con el tema. Eres implacable con las imágenes borrosas o mal generadas.",
        "prompt": "De estas imágenes (descritas por sus prompts), elige las 5 mejores. Devuelve SOLO JSON: {\"seleccionadas\": [{\"prompt\": \"string\", \"razon\": \"string\"}]}"
    },

    "guionista_youtube_experto": {
        "combo": "groq/llama-3.3-70b-versatile",
        "system": "Eres un analista mediatico mordaz, cercano y para todos los publicos. Tu objetivo es DESENMASCARAR como los medios construyen relatos para beneficiar a alguien. NO tienes ideologia fija; analizas la noticia del dia venga de donde venga (politica, economia, europa, empresa). Hablas como un amigo inteligente en un bar, usando ironia y sarcasmo, pero con datos reales. NO eres un academico. NO divagas. Eres directo y punzante. SOLO NARRACION LOCUTADA, PROHIBIDO FADE IN o acotaciones.",
        "prompt": 'Escribe un guion de YouTube de minimo 1500 palabras basado en el articulo. Divide el guion en un número DINÁMICO de escenas (entre 8 y 18) según las pausas dramáticas y los cambios de tema. NO fuerces 18 si no es necesario. Devuelve SOLO JSON valido: {"escenas": [{"id": 1, "texto": "texto locutor 80-120 palabras", "concepto_visual": "descripcion visual en ingles para imagen o busqueda", "mood_musical": "tension|epico|misterio|relax|inspirador|electronico", "tipo_visual": "video|imagen"}]}. REGLA: 7 escenas con tipo_visual \'video\' y 11 con \'imagen\' (40/60). Escena 1 (hook) SIEMPRE \'video\'. Hook brutal, desarrollo, payoff final.'
    },

    "verificador_factos": {
        "combo": "groq/llama-3.3-70b-versatile",
        "system": "Eres un verificador de hechos implacable. Revisas textos periodisticos y eliminas cualquier afirmacion no contrastada, inventada o exagerada. Eres el filtro de calidad final antes de AdSense.",
        "prompt": "Revisa este texto. Devuelve SOLO JSON: {\"texto_corregido\": \"string\", \"alertas\": [\"lista de cambios\"]}"
    },
    "predictor_viralidad": {
        "combo": "groq/llama-3.3-70b-versatile",
        "system": "Eres un experto en el algoritmo de YouTube y retencion de audiencia. Puntuas hooks y titulos del 0 al 100 basandote en curiosidad, emocion y CTR.",
        "prompt": "Puntua este contenido. Devuelve SOLO JSON: {\"score\": 0, \"razon\": \"string\"}"
    },

    # ═══ CAPA 1: META-AGENTES ═══
    "arquitecto_sistema": {
        "combo": "groq/llama-3.3-70b-versatile",
        "system": "Eres el arquitecto del sistema. Lees el codigo, detectas huecos y propones nuevos agentes/scripts.",
        "prompt": "Analiza este codigo/log y devuelve SOLO JSON: {\"nuevos_agentes\": [], \"nuevos_scripts\": [], \"refactors\": []}"
    },
    "auditor_codigo": {
        "combo": "groq/llama-3.3-70b-versatile",
        "system": "Eres un auditor de codigo. Cazas bugs, propones refactors y detectas deuda tecnica.",
        "prompt": "Revisa este codigo. Devuelve SOLO JSON: {\"bugs\": [], \"refactors\": [], \"gravedad\": 0-10}"
    },
    "estratega_negocio": {
        "combo": "groq/llama-3.3-70b-versatile",
        "system": "Eres un estratega de negocio. Analizas metricas y decides nichos y escalado.",
        "prompt": "Analiza estas metricas. Devuelve SOLO JSON: {\"nichos_sugeridos\": [], \"escalado\": \"string\"}"
    },
    # ═══ CAPA 2: AGENTES DE CONTENIDO ═══
    "analista_sentimiento": {
        "combo": "groq/llama-3.3-70b-versatile",
        "system": "Eres un experto en sentimiento social. Mides la temperatura emocional (miedo, rabia, esperanza).",
        "prompt": "Analiza estos titulares. Devuelve SOLO JSON: {\"emocion_principal\": \"string\", \"intensidad\": 0-100}"
    },
    "detector_polarizacion": {
        "combo": "groq/llama-3.3-70b-versatile",
        "system": "Eres un detector de polarizacion. Ajustas el tono si el tema es sensible.",
        "prompt": "Analiza este texto. Devuelve SOLO JSON: {\"es_polarizante\": true/false, \"ajuste_tono\": \"string\"}"
    },
    "generador_titulos_ab": {
        "combo": "groq/llama-3.3-70b-versatile",
        "system": "Eres un experto en CTR. Generas 10 variantes de titulo y 3 de miniatura.",
        "prompt": "Genera variantes. Devuelve SOLO JSON: {\"titulos\": [], \"miniaturas\": []}"
    },
    "analista_competencia": {
        "combo": "groq/llama-3.3-70b-versatile",
        "system": "Eres un espia de canales rivales. Detectas sus temas ganadores.",
        "prompt": "Analiza esta competencia. Devuelve SOLO JSON: {\"temas_ganadores\": [], \"diferenciacion\": \"string\"}"
    },
    "traductor_multilingue": {
        "combo": "groq/llama-3.3-70b-versatile",
        "system": "Eres un traductor nativo a EN, PT, FR, DE. Mantienes el tono del canal.",
        "prompt": "Traduce este texto a los 4 idiomas. Devuelve SOLO JSON: {\"en\": \"string\", \"pt\": \"string\", \"fr\": \"string\", \"de\": \"string\"}"
    },
    "doblador_voz": {
        "combo": "groq/llama-3.3-70b-versatile",
        "system": "Eres un clonador de voz. Preparas el texto para XTTS v2 en Kaggle.",
        "prompt": "Prepara el texto para clonacion. Devuelve SOLO JSON: {\"texto_limpio\": \"string\", \"idioma\": \"string\"}"
    },
    "community_manager_auto": {
        "combo": "groq/llama-3.3-70b-versatile",
        "system": "Eres un CM. Respondes a comentarios de YouTube con el tono del canal.",
        "prompt": "Responde a este comentario. Devuelve SOLO JSON: {\"respuesta\": \"string\", \"es_troll\": true/false}"
    },
    "detector_tendencias_vivas": {
        "combo": "groq/llama-3.3-70b-versatile",
        "system": "Eres un radar de tendencias. Detectas si una noticia esta explotando.",
        "prompt": "Analiza esta noticia y metricas. Devuelve SOLO JSON: {\"explotando\": true/false, \"urgencia\": 0-100}"
    },
    "analista_rendimiento": {
        "combo": "groq/llama-3.3-70b-versatile",
        "system": "Eres un analista de datos. Aprendes de las métricas para mejorar el contenido futuro.",
        "prompt": "Analiza estas métricas. Devuelve SOLO JSON: {\"mejor_tipo\": \"string\", \"recomendaciones\": [\"string\"]}"
    },
    "dj_musical": {
        "combo": "groq/llama-3.3-70b-versatile",
        "system": "Eres un DJ. Devuelves SIEMPRE un JSON valido, nada de texto.",
        "prompt": "Basado en el guion, elige musica. Devuelve EXCLUSIVAMENTE este JSON: {\"pistas\": [{\"momento\": \"string\", \"mood\": \"string\", \"archivo\": \"string\"}]}"
    },

}

# Config max_tokens por rol (tareas cortas vs largas)
MAX_TOKENS_POR_ROL = {
    "forense_medios": 600,
    "analista_emocional": 400,
    "detector_sesgos_cognitivos": 500,
    "abogado_del_diablo": 400,
    "predictor_viralidad": 500,
    "seo_maestro": 800,
    "analista_sentimiento": 500,
    "verificador_factos": 800,
    "detective_tendencias_v2": 1000,
    "guionista_youtube_experto": 3500,
    "guionista_retencion_v2": 3000,
    "redactor_blog": 3500,
    "arquitecto_contenido": 1500,
    "disenador_visual": 1500,
    "community_manager": 800,
    "traductor_formatos": 1500,
    "traductor_humanizado": 2000,
    "bibliotecario_v2": 1500,
    "director_inteligencia_v2": 2000,
    "generador_titulos_ab": 1000,
    "analista_competencia": 1000,
}
DEFAULT_MAX_TOKENS = 800


def pedir_a_especialista(rol, tarea, contexto="", proveedor="auto"):
    import requests, pathlib, os

    rol = rol.lower()
    _max_tok = MAX_TOKENS_POR_ROL.get(rol, DEFAULT_MAX_TOKENS)
    if rol not in ROLES:
        return "ERROR: Rol no existe."

    env_path = pathlib.Path(__file__).resolve().parent.parent / ".env"
    omni_key, groq_key = "", ""
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if line.startswith("OMNIROUTE_API_KEY="): omni_key = line.split("=", 1)[1].strip().strip('"').strip("'")
            if line.startswith("GROQ_API_KEY="): groq_key = line.split("=", 1)[1].strip().strip('"').strip("'")

    system = ROLES[rol].get("system", "") + "\n\nREGLA ABSOLUTA: responde SIEMPRE en castellano de España. NUNCA en inglés. Aunque el contexto esté en inglés, tu output es 100% en castellano."
    prompt = tarea if not contexto else "CONTEXTO:\n" + contexto + "\n\nTAREA:\n" + tarea

    # 1. INTENTO CON GROQ (solo si proveedor != "omni")
    if groq_key and proveedor != "omni":
      import time as _time
      # Rotación de modelos y claves de Groq
      modelos_groq = ["openai/gpt-oss-120b", "openai/gpt-oss-20b", "qwen/qwen3.8-27b"]
      claves_groq = [k for k in [getattr(locals(), "groq_key", ""), getattr(locals(), "groq_key_2", ""), getattr(locals(), "groq_key_3", ""), getattr(locals(), "groq_key_4", "")] if k]
      
      for mod in modelos_groq:
          for key in claves_groq:
              try:
                  r = requests.post(
                      "https://api.groq.com/openai/v1/chat/completions",
                      json={
                          "model": mod,
                          "messages": [
                              {"role": "system", "content": system},
                              {"role": "user", "content": prompt},
                          ],
                          "max_tokens": _max_tok,
                          "temperature": 0.7
                      },
                      headers={
                          "Authorization": f"Bearer {key}",
                          "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                          "Accept": "application/json",
                          "Content-Type": "application/json",
                      },
                      timeout=60,
                  )
                  if r.status_code == 200:
                      return r.json()["choices"][0]["message"]["content"]
              except Exception:
                  pass

    # 1.5 INTENTO CON OPENROUTER (Cazador de modelos gratis dinámico)
    openrouter_key = ""
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if line.startswith("OPENROUTER_API_KEY="):
                openrouter_key = line.split("=", 1)[1].strip()
                break
                
    if openrouter_key:
        # 1. Preguntar a OpenRouter qué modelos :free están vivos AHORA
        modelos_vivos = []
        try:
            r_mods = requests.get("https://openrouter.ai/api/v1/models", timeout=15)
            if r_mods.status_code == 200:
                for m in r_mods.json().get("data", []):
                    if m.get("id", "").endswith(":free"):
                        modelos_vivos.append(m["id"])
        except: pass
        
        # Si la API falla, usar estos como backup (los que suelen estar vivos)
        if not modelos_vivos:
            modelos_vivos = ["meta-llama/llama-3.3-70b-instruct:free", "qwen/qwen-2.5-72b-instruct:free", "google/gemma-2-9b-it:free"]

        # 2. Probar los modelos hasta que uno responda
        import time
        for mod in modelos_vivos[:5]: # Probar máximo 5 para no tardar una eternidad
            try:
                r = requests.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    json={
                        "model": mod,
                        "messages": [
                            {"role": "system", "content": system},
                            {"role": "user", "content": prompt},
                        ],
                        "max_tokens": _max_tok,
                        "temperature": 0.7
                    },
                    headers={
                        "Authorization": f"Bearer {openrouter_key}",
                        "HTTP-Referer": "https://elencuadre.com",
                        "X-Title": "El Encuadre"
                    },
                    timeout=90,
                )
                if r.status_code == 200:
                    content = r.json()["choices"][0]["message"].get("content")
                    if content and len(content.strip()) > 5: # Evitar respuestas vacías (los modelos mudos)
                        return content
            except Exception:
                pass
            time.sleep(1)

    # 1.7 INTENTO CON NVIDIA NIM
    nvidia_key = ""
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if line.startswith("NVIDIA_API_KEY="):
                nvidia_key = line.split("=", 1)[1].strip()
                break
    if nvidia_key:
        nvidia_model = "nvidia/nemotron-3-ultra-550b-a55b"
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                if line.startswith("NVIDIA_MODEL="):
                    nvidia_model = line.split("=", 1)[1].strip()
                    break
        try:
            r = requests.post(
                "https://integrate.api.nvidia.com/v1/chat/completions",
                json={
                    "model": nvidia_model,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": prompt},
                    ],
                    "max_tokens": _max_tok,
                    "temperature": 0.7
                },
                headers={
                    "Authorization": f"Bearer {nvidia_key}",
                    "Content-Type": "application/json"
                },
                timeout=90,
            )
            if r.status_code == 200:
                content = r.json()["choices"][0]["message"].get("content")
                if content and len(content.strip()) > 5:
                    return content
        except Exception:
            pass

    # 1.8 INTENTO CON CLOUDFLARE WORKERS AI
    cf_account = ""
    cf_token = ""
    cf_model = "@cf/meta/llama-3.3-70b-instruct-fp8-fast"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if line.startswith("CLOUDFLARE_ACCOUNT_ID="): cf_account = line.split("=", 1)[1].strip()
            if line.startswith("CLOUDFLARE_API_TOKEN="): cf_token = line.split("=", 1)[1].strip()
            if line.startswith("CLOUDFLARE_MODEL="): cf_model = line.split("=", 1)[1].strip()
            
    if cf_account and cf_token:
        try:
            r = requests.post(
                f"https://api.cloudflare.com/client/v4/accounts/{cf_account}/ai/run/{cf_model}",
                json={
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": prompt},
                    ],
                    "max_tokens": _max_tok,
                },
                headers={"Authorization": f"Bearer {cf_token}"},
                timeout=90,
            )
            if r.status_code == 200:
                res = r.json()
                if res.get("success") and "response" in res.get("result", {}):
                    return res["result"]["response"]
        except Exception:
            pass

    # 1.9 INTENTO CON SAMBANOVA (Última bala en la recámara)
    sambanova_key = ""
    sambanova_model = "Meta-Llama-3.3-70B-Instruct"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if line.startswith("SAMBANOVA_API_KEY="): sambanova_key = line.split("=", 1)[1].strip()
            if line.startswith("SAMBANOVA_MODEL="): sambanova_model = line.split("=", 1)[1].strip()
            
    if sambanova_key:
        # Probar los 2 modelos que tiene SambaNova en free tier
        for mod in ["Meta-Llama-3.3-70B-Instruct", "gpt-oss-120b"]:
            try:
                r = requests.post(
                    "https://api.sambanova.ai/v1/chat/completions",
                    json={
                        "model": mod,
                        "messages": [
                            {"role": "system", "content": system},
                            {"role": "user", "content": prompt},
                        ],
                        "max_tokens": _max_tok,
                        "temperature": 0.7
                    },
                    headers={
                        "Authorization": f"Bearer {sambanova_key}",
                        "Content-Type": "application/json"
                    },
                    timeout=90,
                )
                if r.status_code == 200:
                    content = r.json()["choices"][0]["message"].get("content")
                    if content and len(content.strip()) > 5:
                        return content
            except Exception:
                pass

    # 2. INTENTO CON OMNIROUTE (si proveedor != "groq")
    if omni_key and proveedor != "groq":
        # Modelos por necesidad de tokens
        if _max_tok >= 3000:
            modelos = ["auto/best-reasoning", "auto/pro-reasoning", "auto/smart", "auto"]
        elif _max_tok >= 1500:
            modelos = ["auto/best-fast", "auto/best-reasoning", "auto/chat"]
        else:
            modelos = ["auto/best-fast", "auto/chat", "auto/fast"]
        for modelo in modelos:
            try:
                r = requests.post(
                    "http://localhost:20128/v1/chat/completions",
                    json={
                        "model": modelo,
                        "messages": [
                            {"role": "system", "content": system},
                            {"role": "user", "content": prompt},
                        ],
                        "max_tokens": _max_tok,
                        "temperature": 0.7
                    },
                    headers={"Authorization": f"Bearer {omni_key}"},
                    timeout=60,
                )
                if r.status_code == 200:
                    return r.json()["choices"][0]["message"]["content"]
            except Exception:
                pass

    return "ERROR: Todos los modelos (Groq y OmniRoute) fallaron."