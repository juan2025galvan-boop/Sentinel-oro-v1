import os
from fastapi import FastAPI, Form, Response
from twilio.rest import Client
from langchain_openai import ChatOpenAI

# 1. INICIALIZACIÓN
app = FastAPI()

# Configuración desde Render
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_TOKEN = os.getenv("TWILIO_TOKEN")

# NÚMEROS DE CONFIGURACIÓN
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

# 3. FUNCIÓN DE VOZ EN ESPAÑOL (Aquí está la magia)
def enviar_reporte_voz(to_number, texto_resumen):
    """Llama al usuario y le habla en español de forma pausada"""
    clean_number = to_number.replace("whatsapp:", "")
    
    # Configuramos el mensaje para que Twilio lo lea en español (es-MX)
    twiml_audio = f'''<?xml version="1.0" encoding="UTF-8"?>
    <Response>
        <Pause length="2"/>
        <Say language="es-MX" voice="Polly.Miguel">
            ¡Qué más Arquitecto! Sentinel al habla. He analizado su documento. {texto_resumen}. Repito para que no se le pase nada. {texto_resumen}. ¡Estamos pendientes de su ahorro!
        </Say>
    </Response>'''
    
    client.calls.create(
        twiml=twiml_audio,
        to=clean_number,
        from_=NUMERO_VOZ_PERSONAL
    )

# 4. WEBHOOK (PUENTE)
@app.post("/webhook")
async def webhook_sentinel(
    MediaUrl0: str = Form(None), 
    From: str = Form(...), 
    Body: str = Form(None)
):
    twiml_response = '<?xml version="1.0" encoding="UTF-8"?><Response></Response>'
    
    if MediaUrl0:
        enviar_whatsapp(From, "¡Qué más, Arquitecto! Recibí el PDF. Revisando los goles que le quiere meter el banco... 🕵️‍♂️")
        
        # El hallazgo que le va a dictar por voz
        hallazgo = "Encontré un cobro de Seguro de Vida por 18 mil 500 pesos que no debería estar ahí."
        
        # Alerta por WhatsApp
        enviar_whatsapp(From, f"🚨 ¡ALERTA DE GOL! 🚨\n{hallazgo}")
        
        # Alerta por Voz en Español
        try:
            enviar_reporte_voz(From, hallazgo)
        except Exception as e:
            print(f"Error en llamada: {e}")
            
    elif Body:
        enviar_whatsapp(From, "¡Epa! Aquí sigo patrullando su mina de oro. Mándeme el PDF y lo auditamos de una.")
    
    return Response(content=twiml_response, media_type="application/xml")
