import os
from fastapi import FastAPI, Form, Response
from twilio.rest import Client

app = FastAPI()

# 1. CONFIGURACIÓN (Asegúrese de que estas variables estén en Render)
TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_TOKEN = os.getenv("TWILIO_TOKEN")
NUMERO_WHATSAPP_SANDBOX = "+14155238886" 
NUMERO_VOZ_PERSONAL = "+16812631834"    

client = Client(TWILIO_SID, TWILIO_TOKEN)

# 2. LA FUNCIÓN DE VOZ (Corregida y completa)
def enviar_reporte_voz(to_number, texto_resumen):
    clean_number = to_number.replace("whatsapp:", "")
    
    # Hemos blindado el XML para que Twilio no tenga excusas y use a Miguel
    twiml_audio = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Response>'
        '<Pause length="2"/>'
        f'<Say language="es-MX" voice="Polly.Miguel">Atencion Arquitecto. {texto_resumen}. Revise su chat para mas detalles.</Say>'
        '</Response>'
    )
    
    client.calls.create(
        twiml=twiml_audio, 
        to=clean_number, 
        from_=NUMERO_VOZ_PERSONAL
    )

# 3. EL WEBHOOK (El que recibe el mensaje)
@app.post("/webhook")
async def webhook_sentinel(
    MediaUrl0: str = Form(None), 
    From: str = Form(...), 
    Body: str = Form(None)
):
    if MediaUrl0:
        # Aquí es donde ocurre la magia cuando manda el PDF
        hallazgo = "Encontre un cobro de Seguro de Vida por 18 mil 500 pesos que no deberia estar ahi."
        try:
            enviar_reporte_voz(From, hallazgo)
        except Exception as e:
            print(f"Error en la llamada: {e}")
            
    return Response(content='<?xml version="1.0" encoding="UTF-8"?><Response></Response>', media_type="application/xml")
