import os
from fastapi import FastAPI, UploadFile, File, Form, Response
from twilio.rest import Client
from langchain_openai import ChatOpenAI
import pdfplumber

# 1. INICIALIZACIÓN DEL CEREBRO
app = FastAPI()

# Configuración de las llaves (Se cargan desde Render)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_TOKEN = os.getenv("TWILIO_TOKEN")

# --- ¡OJO ARQUITECTO! PONGA SU NUEVO NÚMERO AQUÍ ---
# El número que acaba de obtener en Twilio (ejemplo: +1234567890)
NUEVO_NUMERO_TWILIO = "+1234567890" 
# --------------------------------------------------

client = Client(TWILIO_SID, TWILIO_TOKEN)
llm = ChatOpenAI(model="gpt-4o", api_key=OPENAI_API_KEY)

# 2. FUNCIÓN DE ENVÍO DE WHATSAPP
def enviar_whatsapp(to_number, mensaje):
    client.messages.create(
        from_=f"whatsapp:{NUEVO_NUMERO_TWILIO}",
        body=mensaje,
        to=to_number
    )

# 3. FUNCIÓN DE REPORTE DE VOZ (Inclusión Total)
def enviar_reporte_voz(to_number, texto_resumen):
    """Llama al usuario y le lee el hallazgo para inclusión visual"""
    clean_number = to_number.replace("whatsapp:", "")
    client.calls.create(
        twiml=f'<Response><Say language="es-MX" voice="Polly.Miguel">¡Qué más Arquitecto! Sentinel al habla. {texto_resumen}</Say></Response>',
        to=clean_number,
        from_=NUEVO_NUMERO_TWILIO  # Aquí usamos el número sin el "whatsapp:"
    )

# 4. RUTA MAESTRA (WEBHOOK)
@app.post("/webhook")
async def webhook_sentinel(
    MediaUrl0: str = Form(None), 
    From: str = Form(...), 
    Body: str = Form(None)
):
    if MediaUrl0:
        enviar_whatsapp(From, "¡Qué más, Arquitecto! Recibí el documento. Déjeme le pego una revisada a ver qué 'goles' le están metiendo... 🕵️‍♂️")
        
        # Simulación de hallazgo (El agente trabajando por su ahorro)
        hallazgo = "Pillé un cobro de 'Seguro de Vida' por $18.500 en Bancolombia que no debería estar ahí. ¡No regalemos la platica!"
        
        enviar_whatsapp(From, f"🚨 ¡ALERTA DE GOL! 🚨\n{hallazgo}")
        
        try:
            enviar_reporte_voz(From, hallazgo)
        except Exception as e:
            print(f"Error en llamada: {e}")
            
    elif Body:
        respuesta = "¡Epa! Aquí sigo patrullando su mina de oro. Mándeme cualquier extracto y de una lo auditamos."
        enviar_whatsapp(From, respuesta)
    
    return Response(content="OK", media_type="text/xml")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
