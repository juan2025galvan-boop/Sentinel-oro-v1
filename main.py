import os
import fitz  # PyMuPDF
import requests
import sqlite3
from datetime import datetime
from fastapi import FastAPI, Form, Response
from twilio.rest import Client
from langchain_openai import ChatOpenAI

app = FastAPI()

# 1. CONFIGURACIÓN E INICIALIZACIÓN DE DB
DB_NAME = "sentinel_memoria.db"

def inicializar_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS hallazgos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT,
            detalle TEXT,
            monto TEXT
        )
    ''')
    conn.commit()
    conn.close()

inicializar_db()

# Variables de entorno
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_TOKEN = os.getenv("TWILIO_TOKEN")
NUMERO_WHATSAPP_SANDBOX = "+14155238886" 
NUMERO_VOZ_PERSONAL = "+16812631834"    

client = Client(TWILIO_SID, TWILIO_TOKEN)
llm = ChatOpenAI(model="gpt-4o", api_key=OPENAI_API_KEY)

# 2. LÓGICA DE MEMORIA
def guardar_hallazgo(detalle):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    fecha_hoy = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("INSERT INTO hallazgos (fecha, detalle) VALUES (?, ?)", (fecha_hoy, detalle))
    conn.commit()
    conn.close()

def obtener_historial():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT fecha, detalle FROM hallazgos ORDER BY id DESC LIMIT 3")
    filas = cursor.fetchall()
    conn.close()
    if not filas:
        return "No hay registros previos."
    return "\n".join([f"- {f[0]}: {f[1]}" for f in filas])

# 3. LÓGICA DE PROCESAMIENTO
def extraer_texto_pdf(url_media):
    response = requests.get(url_media)
    with open("temp.pdf", "wb") as f:
        f.write(response.content)
    texto = ""
    with fitz.open("temp.pdf") as doc:
        for pagina in doc:
            texto += pagina.get_text()
    return texto

@app.post("/webhook")
async def webhook_sentinel(MediaUrl0: str = Form(None), From: str = Form(...), Body: str = Form(None)):
    if MediaUrl0:
        # Extraer y Auditar
        texto_extraido = extraer_texto_pdf(MediaUrl0)
        
        historial = obtener_historial()
        prompt = f"Audita este extracto: {texto_extraido[:2000]}. Historial previo: {historial}. Resume hallazgos sospechosos."
        
        analisis = llm.invoke(prompt).content
        
        # GUARDAR EN MEMORIA
        guardar_hallazgo(analisis[:100]) # Guardamos resumen corto
        
        # Enviar (Esto fallará hasta que se resetee el límite de Twilio)
        try:
            client.messages.create(from_=f"whatsapp:{NUMERO_WHATSAPP_SANDBOX}", body=f"🚨 Auditoría:\n{analisis}", to=From)
        except:
            print("Límite de mensajes alcanzado, pero el hallazgo fue guardado en la base de datos.")

    return Response(content='<?xml version="1.0" encoding="UTF-8"?><Response></Response>', media_type="application/xml")
