import os
import fitz  # PyMuPDF para los PDFs
import requests
import sqlite3
import random
from datetime import datetime
from fastapi import FastAPI, Form, Response
from twilio.rest import Client
from langchain_openai import ChatOpenAI
from openai import OpenAI

app = FastAPI()

# --- 1. CONFIGURACIÓN Y BASE DE DATOS ---
DB_NAME = "sentinel_memoria.db"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_TOKEN = os.getenv("TWILIO_TOKEN")
NUMERO_WHATSAPP_SANDBOX = "+14155238886" 
NUMERO_VOZ_PERSONAL = "+16812631834"    

client = Client(TWILIO_SID, TWILIO_TOKEN)
llm = ChatOpenAI(model="gpt-4o", api_key=OPENAI_API_KEY)
ai_client = OpenAI(api_key=OPENAI_API_KEY)

def inicializar_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS hallazgos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT,
            detalle TEXT,
            monto REAL
        )
    ''')
    conn.commit()
    conn.close()

inicializar_db()

# --- 2. DICCIONARIO DE PERSONALIDAD CÁLIDA (NEUTRAL) ---
FRASES_BIENVENIDA = [
    "¡Qué alegría saludarle! Aquí sigo firme patrullando para cuidar su plata. ¿Qué tenemos para revisar hoy?",
    "¡Epa! Reciba un saludo muy especial. El Sentinel está activo. ¿Algún extracto o duda que revisemos de una?",
    "¡Hola, hola! Todo listo por acá para seguir cuidando su mina de oro. ¿Cómo le puedo ayudar?",
    "¡Qué más! Aquí reportándose su guardián financiero. Mándeme ese documento y lo auditamos sin rodeos."
]

FRASES_ANALISIS = [
    "¡De una! Déjeme le pego una ojeada a esos números para ver que todo esté en orden...",
    "Hágale pues, voy a revisar con lupa para que no le vayan a meter ningún gol.",
    "Listo. Deme un momentico mientras audito ese documento para darle noticias claras.",
    "¡Recibido! Me pongo manos a la obra ahora mismo para que su platica esté a salvo."
]

# --- 3. FUNCIONES DE APOYO ---
def enviar_whatsapp(to_number, mensaje):
    try:
        client.messages.create(from_=f"whatsapp:{NUMERO_WHATSAPP_SANDBOX}", body=mensaje, to=to_number)
    except Exception as e:
        print(f"Error Twilio: {e}")

def extraer_texto_pdf(url_media):
    response = requests.get(url_media)
    with open("temp.pdf", "wb") as f:
        f.write(response.content)
    texto = ""
    with fitz.open("temp.pdf") as doc:
        for pagina in doc:
            texto += pagina.get_text()
    return texto

def transcribir_audio(url_audio):
    audio_data = requests.get(url_audio, auth=(TWILIO_SID, TWILIO_TOKEN))
    with open("temp_audio.ogg", "wb") as f:
        f.write(audio_data.content)
    with open("temp_audio.ogg", "rb") as audio_file:
        transcripcion = ai_client.audio.transcriptions.create(model="whisper-1", file=audio_file)
    return transcripcion.text

# --- 4. WEBHOOK MAESTRO ---
@app.post("/webhook")
async def webhook_sentinel(
    MediaUrl0: str = Form(None), 
    MediaContentType0: str = Form(None),
    From: str = Form(...), 
    Body: str = Form(None)
):
    twiml_ok = '<?xml version="1.0" encoding="UTF-8"?><Response></Response>'
    
    # CASO A: RECIBIMOS ARCHIVOS (PDF O AUDIO)
    if MediaUrl0:
        # 1. Es un AUDIO
        if MediaContentType0 and "audio" in MediaContentType0:
            enviar_whatsapp(From, "👂 Escuchando su mensaje...")
            texto_voz = transcribir_audio(MediaUrl0)
            respuesta_ia = llm.invoke(f"Usuario dice: {texto_voz}. Responde directo y cálido en español colombiano.").content
            enviar_whatsapp(From, f"Usted dijo: \"{texto_voz}\"\n\n🤖 {respuesta_ia}")

        # 2. Es un PDF
        else:
            enviar_whatsapp(From, random.choice(FRASES_ANALISIS))
            texto_pdf = extraer_texto_pdf(MediaUrl0)
            
            # Consultar historial para comparar
            conn = sqlite3.connect(DB_NAME)
            ultimo = conn.execute("SELECT detalle FROM hallazgos ORDER BY id DESC LIMIT 1").fetchone()
            conn.close()
            
            contexto_previo = f"Historial anterior: {ultimo[0]}" if ultimo else "No hay registros previos."
            prompt = f"Compara este extracto con el anterior. Busca aumentos de seguros o comisiones: {contexto_previo}. Texto actual: {texto_pdf[:2000]}"
            
            analisis = llm.invoke(prompt).content
            
            # Guardar en memoria
            conn = sqlite3.connect(DB_NAME)
            conn.execute("INSERT INTO hallazgos (fecha, detalle) VALUES (?, ?)", (datetime.now().strftime("%Y-%m-%d"), analisis[:200]))
            conn.commit()
            conn.close()
            
            enviar_whatsapp(From, f"✅ Auditoría terminada:\n{analisis}")
            
            # Llamada de aviso
            client.calls.create(
                twiml=f'<Response><Pause length="2"/><Say language="es-MX" voice="Polly.Miguel">Hola, su auditoria esta lista. Revise los detalles en su chat para proteger su dinero.</Say></Response>',
                to=From.replace("whatsapp:", ""),
                from_=NUMERO_VOZ_PERSONAL
            )

    # CASO B: RECIBIMOS TEXTO (COMANDOS O SALUDOS)
    elif Body:
        cmd = Body.lower().strip()
        if "historial" in cmd:
            conn = sqlite3.connect(DB_NAME)
            filas = conn.execute("SELECT fecha, detalle FROM hallazgos ORDER BY id DESC LIMIT 3").fetchall()
            conn.close()
            msg = "\n".join([f"📅 {f[0]}: {f[1]}" for f in filas]) if filas else "Aun no tengo registros guardados."
            enviar_whatsapp(From, f"📜 Esto es lo que he encontrado últimamente:\n{msg}")
        else:
            enviar_whatsapp(From, f"{random.choice(FRASES_BIENVENIDA)} Puede mandarme un PDF para auditar, un audio con su duda o escribir 'Historial'.")

    return Response(content=twiml_ok, media_type="application/xml")
