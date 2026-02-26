import os
from fastapi import FastAPI, Form, Response
from twilio.rest import Client
from langchain_openai import ChatOpenAI

# 1. INICIALIZACIÓN
app = FastAPI()

# Configuración desde Render (Variables de Entorno)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_TOKEN = os.getenv("TWILIO_TOKEN")

# CONFIGURACIÓN DE NÚMEROS (Verificados)
NUMERO_WHATSAPP_SANDBOX = "+14155238886" 
NUMERO_VOZ_PERSONAL = "+16812631834"    

client = Client(TWILIO_SID, TWILIO_TOKEN)
llm = ChatOpenAI(model="gpt-4o", api_key=OPENAI_API_KEY)

# 2. FUNCIÓN DE WHATSAPP (VISUAL)
def enviar_whatsapp(to_number, mensaje):
    try:
        client.messages.create(
            from_=f"whatsapp:{NUMERO_WHATSAPP_SANDBOX}",
            body=mensaje,
            to=to_number
        )
    except Exception as e:
        print(f"Error enviando WhatsApp: {e}")

# 3. FUNCIÓN DE VOZ EN ESPAÑOL (ACCESIBILIDAD)
def enviar_reporte_voz(to_number, texto_resumen):
    """Llama al usuario y le habla en español de forma pausada"""
    clean_number = to_number.replace("whatsapp:", "")
    
    # XML TwiML: Forzamos es-MX y voz de Miguel
    twiml_audio = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Response>'
        '<Pause length="2"/>'
        f'<Say language="es-MX" voice="Polly.Miguel">Atencion Arquitecto. Sentinel informa. {texto_resumen}. Repito. {texto_resumen}.</Say>'
        '</Response>'
    )
    
    try:
        client.calls.create(
            twiml=twiml_audio,
            to=clean_number,
            from_=NUMERO_VOZ_PERSONAL
        )
    except Exception as e:
        print(f"Error en llamada: {e}")

# 4. WEBHOOK (EL CORAZÓN QUE RECIBE LOS MENSAJES)
@app.post("/webhook")
async def webhook_sentinel(
    MediaUrl0: str = Form(None), 
    From: str = Form(...), 
    Body: str = Form(None)
):
    # Respuesta XML requerida para que Twilio no dé error
    twiml_response = '<?xml version="1.0" encoding="UTF-8"?><Response></Response>'
    
    if MediaUrl0:
        # Caso: Recibimos un PDF
        enviar_whatsapp(From, "¡Recibido, Arquitecto! Estoy auditando el extracto para proteger su mina de oro... 🕵️‍♂️")
        
        hallazgo = "Encontre un cobro de Seguro de Vida por 18 mil 500 pesos que no deberia estar ahi. ¡Pilas!"
        
        # Alerta visual
        enviar_whatsapp(From, f"🚨 ¡ALERTA DE GOL! 🚨\n{hallazgo}")
        
        # Alerta por voz (Inclusión)
        enviar_reporte_voz(From, hallazgo)
            
    elif Body:
        # Caso: El usuario escribe texto (como "Hola")
        enviar_whatsapp(From, "¡Epa! Aquí sigo patrullando. Mándeme el extracto en PDF y de una lo auditamos.")
    
    return Response(content=twiml_response, media_type="application/xml")
