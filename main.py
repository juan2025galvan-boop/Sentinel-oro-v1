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
TWILIO_NUMBER = "whatsapp:+14155238886" # Número Sandbox Twilio

client = Client(TWILIO_SID, TWILIO_TOKEN)
llm = ChatOpenAI(model="gpt-4o", api_key=OPENAI_API_KEY)

# 2. FUNCIÓN DE ENVÍO DE WHATSAPP (Visual e Inclusivo)
def enviar_whatsapp(to_number, mensaje):
    client.messages.create(
        from_=TWILIO_NUMBER,
        body=mensaje,
        to=to_number
    )

# 3. FUNCIÓN DE REPORTE DE VOZ (Accesibilidad Total)
def enviar_reporte_voz(to_number, texto_resumen):
    """Llama al usuario y le lee el hallazgo para inclusión visual"""
    # Limpiamos el número (quitamos 'whatsapp:')
    clean_number = to_number.replace("whatsapp:", "")
    client.calls.create(
        twiml=f'<Response><Say language="es-MX" voice="Polly.Miguel">¡Qué más Arquitecto! Sentinel al habla. {texto_resumen}</Say></Response>',
        to=clean_number,
        from_='+14155238886' # Asegúrese de que este sea su número de Twilio habilitado para voz
    )

# 4. RUTA MAESTRA (WEBHOOK)
@app.post("/webhook")
async def webhook_sentinel(
    MediaUrl0: str = Form(None), 
    From: str = Form(...), 
    Body: str = Form(None)
):
    # CASO A: EL ARQUITECTO ENVÍA UN PDF (AUDITORÍA)
    if MediaUrl0:
        # 1. Saludo inmediato
        enviar_whatsapp(From, "¡Qué más, Arquitecto! Recibí el documento. Déjeme le pego una revisada a ver qué 'goles' le están metiendo... 🕵️‍♂️")
        
        # 2. Lógica de Auditoría (Aquí simulamos el hallazgo del Agente)
        hallazgo = "Pillé un cobro de 'Seguro de Vida' por $18.500 en Bancolombia que no debería estar ahí. ¡No regalemos la platica!"
        
        # 3. Alerta Visual (WhatsApp)
        enviar_whatsapp(From, f"🚨 ¡ALERTA DE GOL! 🚨\n{hallazgo}")
        
        # 4. Alerta Auditiva (Inclusión)
        try:
            enviar_reporte_voz(From, hallazgo)
        except:
            print("Llamada de voz fallida (Revisar saldo de Twilio)")
            
    # CASO B: MENSAJE DE TEXTO (INTERACCIÓN)
    elif Body:
        respuesta = "¡Epa! Aquí sigo patrullando su mina de oro. Mándeme cualquier extracto o PDF y de una lo auditamos."
        enviar_whatsapp(From, respuesta)
    
    return Response(content="OK", media_type="text/xml")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
