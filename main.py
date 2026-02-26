import os
import fitz  # PyMuPDF
import requests
import sqlite3
from datetime import datetime
from fastapi import FastAPI, Form, Response
from twilio.rest import Client
from langchain_openai import ChatOpenAI

app = FastAPI()

# 1. BASE DE DATOS Y MEMORIA
DB_NAME = "sentinel_memoria.db"

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

# CONFIGURACIÓN
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_TOKEN = os.getenv("TWILIO_TOKEN")
NUMERO_WHATSAPP_SANDBOX = "+14155238886" 
NUMERO_VOZ_PERSONAL = "+16812631834"    

client = Client(TWILIO_SID, TWILIO_TOKEN)
llm = ChatOpenAI(model="gpt-4o", api_key=OPENAI_API_KEY)

# 2. FUNCIONES DE APOYO
def enviar_whatsapp(to_number, mensaje):
    try:
        client.messages.create(from_=f"whatsapp:{NUMERO_WHATSAPP_SANDBOX}", body=mensaje, to=to_number)
    except:
        print("Límite de mensajes o error en Twilio.")

def transcribir_audio(url_audio):
    """Convierte el audio de WhatsApp a texto usando OpenAI Whisper"""
    audio_data = requests.get(url_audio, auth=(TWILIO_SID, TWILIO_TOKEN))
    with open("temp_audio.ogg", "wb") as f:
        f.write(audio_data.content)
    
    # Aquí usaríamos el SDK de OpenAI para Whisper
    from openai import OpenAI
    ai_client = OpenAI(api_key=OPENAI_API_KEY)
    with open("temp_audio.ogg", "rb") as audio_file:
        transcripcion = ai_client.audio.transcriptions.create(model="whisper-1", file=audio_file)
    return transcripcion.text

def extraer_texto_pdf(url_media):
    response = requests.get(url_media)
    with open("temp.pdf", "wb") as f:
        f.write(response.content)
    texto = ""
    with fitz.open("temp.pdf") as doc:
        for pagina in doc:
            texto += pagina.get_text()
    return texto

# 3. WEBHOOK MAESTRO
@app.post("/webhook")
async def webhook_sentinel(
    MediaUrl0: str = Form(None), 
    MediaContentType0: str = Form(None),
    From: str = Form(...), 
    Body: str = Form(None)
):
    # Respuesta rápida para Twilio
    twiml_ok = '<?xml version="1.0" encoding="UTF-8"?><Response></Response>'
    
    # CASO A: RECIBIMOS UN ARCHIVO (PDF O AUDIO)
    if MediaUrl0:
        # Si es un AUDIO
        if "audio" in MediaContentType0:
            enviar_whatsapp(From, "👂 Escuchando su mensaje, Arquitecto...")
            texto_voz = transcribir_audio(MediaUrl0)
            enviar_whatsapp(From, f"Usted dijo: \"{texto_voz}\"")
            # Procesar la pregunta del usuario con la IA
            respuesta_ia = llm.invoke(f"El usuario dice: {texto_voz}. Responde como el Sentinel.").content
            enviar_whatsapp(From, respuesta_ia)

        # Si es un PDF
        elif "pdf" in MediaContentType0 or MediaUrl0.endswith(".pdf"):
            enviar_whatsapp(From, "🔍 Auditando extracto y comparando con el mes pasado...")
            texto_pdf = extraer_texto_pdf(MediaUrl0)
            
            # Consultar historial para comparar
            conn = sqlite3.connect(DB_NAME)
            ultimo = conn.execute("SELECT detalle FROM hallazgos ORDER BY id DESC LIMIT 1").fetchone()
            conn.close()
            
            contexto = f"Historial previo: {ultimo[0] if ultimo else 'No hay'}. Analiza este nuevo texto: {texto_pdf[:2000]}"
            analisis = llm.invoke(f"Eres un auditor. Compara y busca cobros nuevos o aumentos injustos: {contexto}").content
            
            # Guardar en memoria
            conn = sqlite3.connect(DB_NAME)
            conn.execute("INSERT INTO hallazgos (fecha, detalle) VALUES (?, ?)", (datetime.now().strftime("%Y-%m-%d"), analisis[:200]))
            conn.commit()
            conn.close()
            
            enviar_whatsapp(From, f"🚨 REPORTE DE AUDITORÍA:\n{analisis}")
            
    # CASO B: RECIBIMOS TEXTO (COMANDOS)
    elif Body:
        cmd = Body.lower()
        if "historial" in cmd:
            conn = sqlite3.connect(DB_NAME)
            filas = conn.execute("SELECT fecha, detalle FROM hallazgos LIMIT 5").fetchall()
            conn.close()
            msg = "\n".join([f"📅 {f[0]}: {f[1]}" for f in filas]) if filas else "No hay historial."
            enviar_whatsapp(From, f"📜 Memoria del Sentinel:\n{msg}")
        else:
            enviar_whatsapp(From, "¡Epa Arquitecto! Mandeme un PDF, un audio o escriba 'Historial'.")

    return Response(content=twiml_ok, media_type="application/xml")
