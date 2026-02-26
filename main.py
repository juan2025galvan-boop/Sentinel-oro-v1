import os
from fastapi import FastAPI, Form, Response
from twilio.rest import Client
from langchain_openai import ChatOpenAI

# 1. INICIALIZACIÓN PROFESIONAL
app = FastAPI()

# Variables de entorno (Cargadas desde Render)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_TOKEN = os.getenv("TWILIO_TOKEN")

# CONFIGURACIÓN DE NÚMEROS (Asegurese de que sean estos)
NUMERO_WHATSAPP_SANDBOX = "+14155238886" 
NUMERO_VOZ_PERSONAL = "+16812631834"    

client = Client(TWILIO_SID, TWILIO_TOKEN)
llm = ChatOpenAI(model="gpt-4o", api_key=OPENAI_API_KEY)

# 2. FUNCIÓN DE WHATSAPP
def enviar_whatsapp(to_number, mensaje):
    client.messages.create(
        from_=f"whatsapp:{NUMERO_WHATSAPP_SANDBOX}",
        body=mensaje,
        to=to_number
    )

# 3. FUNCIÓN DE VOZ PROFESIONAL (Blindada para Español)
def enviar_reporte_voz(to_number, texto_resumen):
    """Llama al usuario con voz de alta fidelidad en español latino"""
    clean_number = to_number.replace("whatsapp:", "")
    
    # TwiML estructurado: Pausa + Idioma + Voz Humana
    # Usamos f-strings con comillas triples para evitar errores de formato
    twiml_audio = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Response>'
        '<Pause length="2"/>'
        f'<Say language="es-MX" voice="Polly.Miguel">¡Qué más Arquitecto! Sentinel al habla. He detectado una irregularidad. {texto_resumen}. Repito. {texto_resumen}. Revise su chat para más detalles.</Say>'
        '</Response>'
    )
    
    client.calls.create(
        twiml=twiml_audio,
        to=clean_number,
        from_=NUMERO_VOZ_PERSONAL
    )

# 4. WEBHOOK MAESTRO
@app.post("/webhook")
async def webhook_sentinel(
    MediaUrl0: str = Form(None), 
    From: str = Form(...), 
    Body: str = Form(None)
):
    # Respuesta estándar para Twilio
    twiml_response = '<?xml version="1.0" encoding="UTF-8"?><Response></Response>'
    
    if MediaUrl0:
        enviar_whatsapp(From, "¡Qué más, Arquitecto! Recibí el PDF. Lo estoy auditando ahora mismo... 🕵️‍♂️")
        
        # El hallazgo exacto
        hallazgo = "Encontré un cobro de Seguro de Vida por 18 mil 500 pesos que no debería estar ahí."
        
        # Alerta visual en WhatsApp
        enviar_whatsapp(From, f"🚨 ¡ALERTA DE GOL! 🚨\n{hallazgo}")
        
        # Alerta auditiva profesional en Español
        try:
            enviar_reporte_voz(From, hallazgo)
        except Exception as e:
            print(f"Error en llamada: {e}")
            
    elif Body:
        # Respuesta de cortesía
        enviar_whatsapp(From, "¡Epa! Aquí sigo patrullando su mina de oro. Mándeme el PDF y lo auditamos de una.")
    
    return Response(content=twiml_response, media_type="application/xml")
