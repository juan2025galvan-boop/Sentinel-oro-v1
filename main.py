import os
from fastapi import FastAPI, Form, Response
from twilio.rest import Client
from langchain_openai import ChatOpenAI

app = FastAPI()

# Configuración (Asegúrate de tener estas variables en Render)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_TOKEN = os.getenv("TWILIO_TOKEN")

# IMPORTANTE: Para llamadas de voz, Twilio usa números normales, NO el de WhatsApp.
# Si no tienes un número comprado, usa el número de prueba que Twilio te dio para VOZ.
TWILIO_WHATSAPP_NUMBER = "whatsapp:+14155238886"
TWILIO_VOICE_NUMBER = "+14155238886" # <-- Verifica que este número tenga permisos de VOZ en Twilio

client = Client(TWILIO_SID, TWILIO_TOKEN)

# FUNCIÓN DE WHATSAPP
def enviar_whatsapp(to_number, mensaje):
    client.messages.create(
        from_=TWILIO_WHATSAPP_NUMBER,
        body=mensaje,
        to=to_number
    )

# FUNCIÓN DE VOZ CORREGIDA
def enviar_reporte_voz(to_number, texto_resumen):
    # 1. Aseguramos el formato internacional con el '+'
    clean_number = to_number.replace("whatsapp:", "")
    if not clean_number.startswith('+'):
        clean_number = '+' + clean_number
    
    # 2. Intentamos la llamada
    client.calls.create(
        twiml=f'<Response><Pause length="1"/><Say language="es-MX" voice="Polly.Miguel">¡Qué más Arquitecto! Soy Sentinel. Pillé lo siguiente: {texto_resumen}</Say></Response>',
        to=clean_number,
        from_=TWILIO_VOICE_NUMBER 
    )

@app.post("/webhook")
async def webhook_sentinel(
    MediaUrl0: str = Form(None), 
    From: str = Form(...), 
    Body: str = Form(None)
):
    if MediaUrl0:
        enviar_whatsapp(From, "¡Qué más, Arquitecto! Recibí el PDF. Espere un tiento que ya estoy cazando goles... 🕵️‍♂️")
        
        hallazgo = "Pillé un cobro de 'Seguro de Vida' por 18 mil 500 pesos en su extracto que no debería estar ahí. ¡Pilas pues!"
        
        # Alerta WhatsApp
        enviar_whatsapp(From, f"🚨 ¡ALERTA DE GOL! 🚨\n{hallazgo}")
        
        # Alerta de Voz (Inclusión)
        try:
            enviar_reporte_voz(From, hallazgo)
        except Exception as e:
            # Esto nos dirá en Render exactamente qué pasó
            print(f"Error técnico en la llamada: {e}")
            enviar_whatsapp(From, "Arquitecto, intenté llamarlo pero no pude. Revise los permisos de voz en Twilio.")
            
    elif Body:
        enviar_whatsapp(From, "¡Epa! Aquí sigo patrullando. Mándeme el extracto cuando quiera.")
    
    return Response(content="OK", media_type="text/xml")
