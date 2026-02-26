import random

# Frases cálidas, colombianas y para todo el mundo (Neutrales)
FRASES_BIENVENIDA = [
    "¡Qué alegría saludarle! Aquí sigo firme patrullando para cuidar su plata. ¿Qué tenemos para revisar hoy?",
    "¡Epa! Reciba un saludo muy especial. El Sentinel está activo. ¿Algún extracto o duda que revisemos de una?",
    "¡Hola, hola! Todo listo por acá para seguir cuidando su mina de oro. ¿Cómo le puedo ayudar en este momento?",
    "¡Qué más! Aquí reportándose su guardián financiero. Mándeme ese documento y lo auditamos sin rodeos."
]

FRASES_ANALISIS = [
    "¡De una! Déjeme le pego una ojeada a esos números para ver que todo esté en orden...",
    "Hágale pues, voy a revisar con lupa para que no le vayan a meter ningún gol.",
    "Listo el sistema. Deme un momentico mientras audito ese documento para darle noticias claras.",
    "¡Recibido! Me pongo manos a la obra ahora mismo para que su platica esté a salvo."
]

FRASES_EXITO = [
    "¡Listo! Aquí tiene el reporte detallado. Échele un ojo que hay datos importantes.",
    "¡Pilas! Ya terminé la auditoría. Aquí le cuento lo que encontré, bien clarito y sin vueltas.",
    "¡Vea pues! Ya tenemos los resultados. No nos dejamos cobrar ni un peso de más.",
    "Auditoría terminada con éxito. Aquí le dejo la información para que tome decisiones de una."
]

# Ajuste en el Webhook para ser directo y cálido
@app.post("/webhook")
async def webhook_sentinel(MediaUrl0: str = Form(None), From: str = Form(...), Body: str = Form(None)):
    twiml_ok = '<?xml version="1.0" encoding="UTF-8"?><Response></Response>'
    
    if MediaUrl0:
        # Respuesta inmediata y cálida
        enviar_whatsapp(From, random.choice(FRASES_ANALISIS))
        
        # ... (Aquí sigue su lógica de procesamiento de PDF/Audio) ...
        
        # Al finalizar el análisis:
        # enviar_whatsapp(From, f"✅ {random.choice(FRASES_EXITO)}\n{resultado_analisis}")
        
    elif Body:
        # Si la persona escribe "Hola" o cualquier cosa
        enviar_whatsapp(From, f"{random.choice(FRASES_BIENVENIDA)} Puede mandarme un PDF, un audio o escribirme su duda.")

    return Response(content=twiml_ok, media_type="application/xml")
