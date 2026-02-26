import os
from fastapi import FastAPI, Form, Response
from twilio.rest import Client
from langchain_openai import ChatOpenAI

# 1. INICIALIZACIÓN DEL CEREBRO
app = FastAPI()

# Configuración desde Render (Variables de Entorno)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_TOKEN = os.getenv("TWILIO_TOKEN")

# --- CONFIGURACIÓN DE NÚMEROS (EL TABLERO ELÉCTRICO) ---
NUMERO_WHATSAPP_SANDBOX = "+14155238886"  # El de Twilio para mensajes
NUMERO_VOZ_PERSONAL = "+16812631834"     # Su número comprado para llamadas
# ------------------------------------------------------

client = Client(TWILIO_SID, TWILIO_TOKEN)
llm = ChatOpenAI(model="gpt-4o", api_key=OPENAI_API_KEY)

# 2. FUNCIÓN DE WHATSAPP (VISUAL)
def enviar_whatsapp(to_number, mensaje):
    client.messages.create(
        from_=f"whatsapp:{NUMERO_WHATSAPP_SANDBOX}",
        body=mensaje,
        to=to_number
    )

# 3. FUNCIÓN DE VOZ EN ESPAÑOL (ACCESIBILIDAD TOTAL)
def enviar_reporte_voz(to_number, texto_resumen):
    """Llama al usuario y le habla en español claro"""
    clean_number = to_number.replace("whatsapp:", "")
    
    # TwiML configurado con lenguaje es-MX y voz de Miguel
    twiml_audio = f'''<?xml version="1.0" encoding="UTF-8"?>
    <Response>
        <Pause length="1"/>
        <Say language="es-MX" voice="Polly.Miguel">
            ¡Qué más Arquitecto! Sentinel al habla. He revisado su documento y tengo un reporte importante. {texto_resumen} Repito. {texto_resumen}. ¡Estamos en contacto!
        </Say>
    </Response>'''
    
    client.calls.create(
        twiml=twiml_audio,
        to=clean_number,
        from_=NUMERO_VOZ_PERSONAL
    )

# 4. WEBHOOK (EL PUENTE DE COMUNICACIÓN)
@app.post("/webhook")
async def webhook_sentinel(
    MediaUrl0: str = Form(None), 
    From: str = Form(...), 
    Body: str = Form(None)
):
    # Respuesta XML requerida por Twilio
    twiml_response = '<?xml version="1.0" encoding="UTF-8"?><Response></Response>'
    
    if MediaUrl0:
        enviar_whatsapp(From, "¡Qué más, Arquitecto! Recibí el PDF. Déjeme le pego una revisada a esos números... 🕵️‍♂️")
        
        # Simulación del hallazgo (La IA auditando su mina de oro)
        hallazgo = "Pillé un cobro de Seguro de Vida por 18 mil 500 pesos en su extracto que no debería estar ahí. ¡No regalemos la platica!"
        
        # Alerta visual
        enviar_whatsapp(From, f"🚨 ¡ALERTA DE GOL! 🚨\n{hallazgo}")
        
        # Alerta auditiva (Voz en español)
        try:
            enviar_reporte_voz(From, hallazgo)
        except Exception as e:
            print(f"Error en la llamada de voz: {e}")
            
    elif Body:
        # Respuesta rápida para cualquier otro mensaje
        enviar_whatsapp(From, "¡Epa! Aquí sigo patrullando su mina de oro. Mándeme cualquier extracto en PDF y de una lo auditamos.")
    
    return Response(content=twiml_response, media_type="application/xml")
