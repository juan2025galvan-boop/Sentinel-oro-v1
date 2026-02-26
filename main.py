import os
from fastapi import FastAPI, Form, Response
from twilio.rest import Client
from langchain_openai import ChatOpenAI

app = FastAPI()

# Configuración desde Render
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_TOKEN = os.getenv("TWILIO_TOKEN")

# --- LOS DOS NÚMEROS CLAVE ---
NUMERO_WHATSAPP_SANDBOX = "+14155238886"  # El que recibe los mensajes
NUMERO_VOZ_PERSONAL = "+16812631834"     # El que hace las llamadas

client = Client(TWILIO_SID, TWILIO_TOKEN)
llm = ChatOpenAI(model="gpt-4o", api_key=OPENAI_API_KEY)

def enviar_whatsapp(to_number, mensaje):
    # IMPORTANTE: Aquí usamos el número del Sandbox (+1415...)
    client.messages.create(
        from_=f"whatsapp:{NUMERO_WHATSAPP_SANDBOX}",
        body=mensaje,
        to=to_number
    )

def enviar_reporte_voz(to_number, texto_resumen):
    # IMPORTANTE: Aquí usamos su número personal (+1681...)
    clean_number = to_number.replace("whatsapp:", "")
    client.calls.create(
        twiml=f'<Response><Say language="es-MX" voice="Polly.Miguel">¡Qué más Arquitecto! Sentinel al habla. {texto_resumen}</Say></Response>',
        to=clean_number,
        from_=NUMERO_VOZ_PERSONAL
    )

@app.post("/webhook")
async def webhook_sentinel(MediaUrl0: str = Form(None), From: str = Form(...), Body: str = Form(None)):
    twiml_response = '<?xml version="1.0" encoding="UTF-8"?><Response></Response>'
    
    if MediaUrl0:
        enviar_whatsapp(From, "¡Qué más, Arquitecto! Recibí el PDF. Revisando goles... 🕵️‍♂️")
        hallazgo = "Pillé un cobro de 'Seguro de Vida' por 18 mil 500 pesos que no debería estar ahí. ¡Pilas!"
        enviar_whatsapp(From, f"🚨 ¡ALERTA DE GOL! 🚨\n{hallazgo}")
        try:
            enviar_reporte_voz(From, hallazgo)
        except Exception as e:
            print(f"Error en voz: {e}")
            
    elif Body:
        enviar_whatsapp(From, "¡Epa! Aquí sigo patrullando su mina de oro. Mándeme el PDF y lo auditamos.")
    
    return Response(content=twiml_response, media_type="application/xml")
