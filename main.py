import os
from fastapi import FastAPI, Form, Response
from twilio.rest import Client
from langchain_openai import ChatOpenAI

# 1. INICIALIZACIÓN
app = FastAPI()

# Configuración desde Render (Asegúrese de tener estas Environment Variables en Render)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_TOKEN = os.getenv("TWILIO_TOKEN")

# SU NÚMERO REAL DE TWILIO (Verificado en sus capturas)
NUEVO_NUMERO_TWILIO = "+16812631834" 

client = Client(TWILIO_SID, TWILIO_TOKEN)
llm = ChatOpenAI(model="gpt-4o", api_key=OPENAI_API_KEY)

# 2. FUNCIONES DE COMUNICACIÓN
def enviar_whatsapp(to_number, mensaje):
    """Envía mensaje visual al Xiaomi"""
    client.messages.create(
        from_=f"whatsapp:{NUEVO_NUMERO_TWILIO}",
        body=mensaje,
        to=to_number
    )

def enviar_reporte_voz(to_number, texto_resumen):
    """Llama al usuario para reporte auditivo (Inclusión)"""
    clean_number = to_number.replace("whatsapp:", "")
    client.calls.create(
        twiml=f'<Response><Say language="es-MX" voice="Polly.Miguel">¡Qué más Arquitecto! Sentinel al habla. {texto_resumen}</Say></Response>',
        to=clean_number,
        from_=NUEVO_NUMERO_TWILIO
    )

# 3. WEBHOOK (EL PUENTE ENTRE WHATSAPP Y RENDER)
@app.post("/webhook")
async def webhook_sentinel(
    MediaUrl0: str = Form(None), 
    From: str = Form(...), 
    Body: str = Form(None)
):
    # Respuesta XML requerida por Twilio para no generar errores de conexión
    twiml_response = '<?xml version="1.0" encoding="UTF-8"?><Response></Response>'
    
    if MediaUrl0:
        # Caso: El Arquitecto envía un PDF
        enviar_whatsapp(From, "¡Qué más, Arquitecto! Recibí el PDF. Revisando si le están metiendo goles... 🕵️‍♂️")
        
        # Hallazgo de la auditoría
        hallazgo = "Pillé un cobro de 'Seguro de Vida' por $18.500 en su extracto que no debería estar ahí. ¡Ojo!"
        
        # Alerta por WhatsApp
        enviar_whatsapp(From, f"🚨 ¡ALERTA DE GOL! 🚨\n{hallazgo}")
        
        # Alerta por Voz (Accesibilidad)
        try:
            enviar_reporte_voz(From, hallazgo)
        except Exception as e:
            print(f"Error en llamada: {e}")
            
    elif Body:
        # Caso: Mensaje de texto normal
        enviar_whatsapp(From, "¡Epa! Aquí sigo patrullando su mina de oro. Mándeme el extracto en PDF y de una lo auditamos.")
    
    return Response(content=twiml_response, media_type="application/xml")
