import os
from fastapi import FastAPI, UploadFile, File, Form, Response
from twilio.rest import Client
from langchain_openai import ChatOpenAI

# 1. INICIALIZACIÓN
app = FastAPI()

# Configuración desde Render
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_TOKEN = os.getenv("TWILIO_TOKEN")

# EL NÚMERO QUE OBTUVIMOS (681) 263-1834
NUEVO_NUMERO_TWILIO = "+16812631834" 

client = Client(TWILIO_SID, TWILIO_TOKEN)
llm = ChatOpenAI(model="gpt-4o", api_key=OPENAI_API_KEY)

# 2. FUNCIONES DE COMUNICACIÓN
def enviar_whatsapp(to_number, mensaje):
    client.messages.create(
        from_=f"whatsapp:{NUEVO_NUMERO_TWILIO}",
        body=mensaje,
        to=to_number
    )

def enviar_reporte_voz(to_number, texto_resumen):
    clean_number = to_number.replace("whatsapp:", "")
    client.calls.create(
        twiml=f'<Response><Say language="es-MX" voice="Polly.Miguel">¡Qué más Arquitecto! Sentinel al habla. {texto_resumen}</Say></Response>',
        to=clean_number,
        from_=NUEVO_NUMERO_TWILIO
    )

# 3. WEBHOOK (EL PUENTE)
@app.post("/webhook")
async def webhook_sentinel(
    MediaUrl0: str = Form(None), 
    From: str = Form(...), 
    Body: str = Form(None)
):
    # Respuesta vacía legal para Twilio (Evita el silencio)
    twiml_response = '<?xml version="1.0" encoding="UTF-8"?><Response></Response>'
    
    if MediaUrl0:
        enviar_whatsapp(From, "¡Qué más, Arquitecto! Recibí el PDF. Revisando goles... 🕵️‍♂️")
        
        hallazgo = "Pillé un cobro de 'Seguro de Vida' por $18.500 en Bancolombia que no debería estar ahí. ¡Ojo!"
        
        enviar_whatsapp(From, f"🚨 ¡ALERTA DE GOL! 🚨\n{hallazgo}")
        
        try:
            enviar_reporte_voz(From, hallazgo)
        except Exception as e:
            print(f"Error en llamada: {e}")
            
    elif Body:
        # Esto despierta al WhatsApp si le escribes cualquier cosa
        enviar_whatsapp(From, "¡Epa! Aquí sigo patrullando su mina de oro. Mándeme el PDF y lo auditamos de una.")
    
    return Response(content=twiml_response, media_type="application/xml")
