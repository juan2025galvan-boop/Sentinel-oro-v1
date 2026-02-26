import os
from fastapi import FastAPI, Form, Response
from twilio.rest import Client

app = FastAPI()

# Variables de entorno
TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_TOKEN = os.getenv("TWILIO_TOKEN")
client = Client(TWILIO_SID, TWILIO_TOKEN)

@app.post("/webhook")
async def webhook(Body: str = Form(None), From: str = Form(...)):
    # Respuesta directa del "Parce"
    mensaje = "¡Qué más, Arquitecto! Aquí reportándose el Sentinel. El puente está firme. ¿En qué somos buenos hoy?"
    
    client.messages.create(
        body=mensaje,
        from_="whatsapp:+14155238886",
        to=From
    )
    return Response(content="OK", media_type="text/xml")
