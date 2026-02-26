import os
from fastapi import FastAPI, UploadFile, File, Form, Response
from twilio.rest import Client
from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI
import pdfplumber
import io

# 1. INICIALIZACIÓN DEL CEREBRO
app = FastAPI()

# Configuración de las llaves (Se cargan desde Render)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_TOKEN = os.getenv("TWILIO_TOKEN")
TWILIO_NUMBER = "whatsapp:+14155238886" # Número estándar del Sandbox

client = Client(TWILIO_SID, TWILIO_TOKEN)
llm = ChatOpenAI(model="gpt-4o", api_key=OPENAI_API_KEY)

# 2. DEFINICIÓN DEL AGENTE "SENTINEL" (Personalidad Paisa/Inclusiva)
analista_paisa = Agent(
    role='Sentinel Financiero',
    goal='Detectar cobros injustos y explicar ahorros de forma clara y accesible',
    backstory="""Eres un experto financiero en Colombia. Hablas con cercanía ('parce', 'bacán'), 
    pero eres implacable con los bancos. Tu prioridad es la inclusión: si detectas que el 
    usuario necesita claridad, eres muy descriptivo.""",
    llm=llm
)

# 3. RUTA DEL WEBHOOK (La puerta que conecta con WhatsApp)
@app.post("/webhook")
async def webhook_whatsapp(
    MediaUrl0: str = Form(None), 
    From: str = Form(...), 
    Body: str = Form(None)
):
    # CASO A: EL USUARIO ENVÍA UN PDF
    if MediaUrl0:
        respuesta_inicial = "¡Qué más, Arquitecto! Recibí el documento. Déjeme le pego una revisada con los muchachos (mis agentes) y ya le cuento qué encontré... 🧐"
        enviar_whatsapp(From, respuesta_inicial)
        
        # Aquí iría la lógica de descarga y lectura del PDF con pdfplumber
        # Por ahora, simulamos el análisis para la prueba inicial
        hallazgo = "Pillé un seguro de $18.500 en Bancolombia que no debería estar ahí. ¡No regalemos la platica! ¿Quiere que le redacte el reclamo de una?"
        enviar_whatsapp(From, hallazgo)
        
    # CASO B: EL USUARIO RESPONDE "HÁGALE" O "ENVÍE"
    elif Body and any(word in Body.lower() for word in ["hágale", "envíe", "listo", "mándelo"]):
        confirmacion = "¡De una! Ya mismo estoy redactando el correo para el banco con toda la de la ley (1328 de 2009). Se lo mando en un momentico para que lo revise."
        enviar_whatsapp(From, confirmacion)
    
    return Response(content="OK", media_type="text/xml")

# 4. FUNCIÓN AUXILIAR DE ENVÍO
def enviar_whatsapp(to_number, mensaje):
    client.messages.create(
        from_=TWILIO_NUMBER,
        body=mensaje,
        to=to_number
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
