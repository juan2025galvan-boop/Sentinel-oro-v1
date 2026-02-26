import os
from fastapi import FastAPI, Form, Response
from twilio.rest import Client

app = FastAPI()

# 1. CONFIGURACIÓN
TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_TOKEN = os.getenv("TWILIO_TOKEN")
NUMERO_WHATSAPP_SANDBOX = "+14155238886" 
NUMERO_VOZ_PERSONAL = "+16812631834"    

client = Client(TWILIO_SID, TWILIO_TOKEN)

# 2. FUNCIÓN DE WHATSAPP
def enviar_whatsapp(to_number, mensaje):
    try:
        client.messages.create(
            from_=f"whatsapp:{NUMERO_WHATSAPP_SANDBOX}",
            body=mensaje,
            to=to_number
        )
    except Exception as e:
        print(f"Error WhatsApp: {e}")

# 3. FUNCIÓN DE VOZ (SIN AUDIO MUDO)
def enviar_reporte_voz(to_number, texto_resumen):
    clean_number = to_number.replace("whatsapp:", "")
    # Usamos la voz estandar para asegurar compatibilidad total y evitar llamadas mudas
    twiml_audio = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Response>'
        '<Pause length="3"/>'
        f'<Say language="es-MX" voice="man">Atencion Arquitecto. {texto_resumen}</Say>'
        '</Response>'
    )
    try:
        client.calls.create(twiml=twiml_audio, to=clean_number, from_=NUMERO_VOZ_PERSONAL)
    except Exception as e:
        print(f"Error Voz: {e}")

# 4. WEBHOOK (EL ARREGLO PARA QUE EL CHAT RESPONDA)
@app.post("/webhook")
async def webhook_sentinel(MediaUrl0: str = Form(None), From: str = Form(...), Body: str = Form(None)):
    # IMPORTANTE: Twilio necesita este XML vacio para saber que recibimos el mensaje
    twiml_ok = '<?xml version="1.0" encoding="UTF-8"?><Response></Response>'
    
    if MediaUrl0:
        enviar_whatsapp(From, "¡PDF Recibido! Buscando fugas de dinero... 🕵️‍♂️")
        hallazgo = "Encontre un cobro de Seguro por 18 mil 500 pesos. ¡Pilas!"
        enviar_whatsapp(From, f"🚨 ALERTA: {hallazgo}")
        enviar_reporte_voz(From, hallazgo)
    elif Body:
        # Esto hara que responda al "Hola"
        enviar_whatsapp(From, "¡Sentinel activo! Mandeme el PDF para auditarlo, Arquitecto.")
    
    return Response(content=twiml_ok, media_type="application/xml")
