import os
import fitz  # PyMuPDF
import requests
import sqlite3
import random
import re
from datetime import datetime
from fastapi import FastAPI, Form, Response
from twilio.rest import Client
from langchain_openai import ChatOpenAI
from openai import OpenAI

# 1. INICIALIZACIÓN Y CONFIGURACIÓN
app = FastAPI()
DB_NAME = "sentinel_memoria.db"

# Variables de entorno (Asegúrese de tenerlas en Render)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_TOKEN = os.getenv("TWILIO_TOKEN")
NUMERO_WHATSAPP_SANDBOX = "+14155238886" 
NUMERO_VOZ_PERSONAL = "+16812631834"    

# Clientes
client = Client(TWILIO_SID, TWILIO_TOKEN)
llm = ChatOpenAI(model="gpt-4o", api_key=OPENAI_API_KEY, temperature=0)
ai_client = OpenAI(api_key=OPENAI_API_KEY)

def inicializar_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS hallazgos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT,
            detalle TEXT,
            monto REAL DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

inicializar_db()

# 2. PERSONALIDAD Y ACCESIBILIDAD
FRASES_BIENVENIDA = [
    "¡Qué alegría saludarle! Aquí sigo firme patrullando para cuidar su plata. ¿Qué tenemos para revisar hoy?",
    "¡Epa! Reciba un saludo muy especial. El Sentinel está activo. ¿Algún extracto para auditar?",
    "¡Hola, hola! Todo listo por acá para seguir cuidando su mina de oro. ¿Cómo le puedo ayudar?"
]

# 3. FUNCIONES DE SERVICIO
def enviar_whatsapp(to_number, mensaje):
    try:
        client.messages.create(from_=f"whatsapp:{NUMERO_WHATSAPP_SANDBOX}", body=mensaje, to=to_number)
    except Exception as e:
        print(f"Error enviando WhatsApp: {e}")

def extraer_monto(texto):
    """Extrae solo los números de la respuesta de la IA para sumar al ahorro"""
    numeros = re.findall(r'\d+', texto.replace('.', '').replace(',', ''))
    if numeros:
        return float(numeros[-1]) # Toma el último número mencionado (asumiendo que es el total)
    return 0

# 4. WEBHOOK PRINCIPAL
@app.post("/webhook")
async def webhook_sentinel(
    MediaUrl0: str = Form(None), 
    MediaContentType0: str = Form(None),
    From: str = Form(...), 
    Body: str = Form(None)
):
    # Respuesta inmediata a Twilio para evitar errores 500
    twiml_ok = '<?xml version="1.0" encoding="UTF-8"?><Response></Response>'
    
    # --- PROCESAMIENTO DE ARCHIVOS (PDF/AUDIO) ---
    if MediaUrl0:
        # Detectar Audio
        if MediaContentType0 and "audio" in MediaContentType0:
            enviar_whatsapp(From, "👂 Escuchando su mensaje... deme un segundito.")
            try:
                audio_data = requests.get(MediaUrl0, auth=(TWILIO_SID, TWILIO_TOKEN))
                with open("temp_audio.ogg", "wb") as f: f.write(audio_data.content)
                with open("temp_audio.ogg", "rb") as audio_file:
                    transcripcion = ai_client.audio.transcriptions.create(model="whisper-1", file=audio_file).text
                
                respuesta_ia = llm.invoke(f"El usuario dice: {transcripcion}. Responde como Sentinel (Asistente financiero colombiano).").content
                enviar_whatsapp(From, f"🤖 *Sentinel informa:*\n{respuesta_ia}")
            except Exception as e:
                enviar_whatsapp(From, "¡Ay caramba! No pude procesar el audio. ¿Me lo repite?")

        # Detectar PDF
        else:
            enviar_whatsapp(From, "¡Recibido! Déjeme le pego una ojeada a esos números para ver que todo esté en orden...")
            try:
                # Descarga y lectura
                res = requests.get(MediaUrl0)
                with open("temp.pdf", "wb") as f: f.write(res.content)
                texto_pdf = ""
                with fitz.open("temp.pdf") as doc:
                    for pagina in doc: texto_pdf += pagina.get_text()
                
                # Análisis de Auditoría
                prompt = f"Eres Sentinel. Audita este extracto: {texto_pdf[:3500]}. Identifica cobros sospechosos (seguros, comisiones). Al final de tu respuesta pon exactamente: 'MONTO: [valor]'."
                analisis = llm.invoke(prompt).content
                
                # Guardar en Memoria
                monto = extraer_monto(analisis)
                conn = sqlite3.connect(DB_NAME)
                conn.execute("INSERT INTO hallazgos (fecha, detalle, monto) VALUES (?, ?, ?)", 
                             (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), analisis[:250], monto))
                conn.commit()
                conn.close()

                # Reportar Resultados
                enviar_whatsapp(From, f"✅ *Auditoría Terminada:*\n{analisis}")
                
                # Llamada de Alerta (Independiente)
                try:
                    num_call = From.replace("whatsapp:", "").strip()
                    client.calls.create(
                        twiml=f'<Response><Pause length="2"/><Say language="es-MX" voice="Polly.Miguel">¡Hola! Habla el Sentinel. Ya termine de revisar su extracto. Entre al guasap que le deje los detalles importantes. ¡Pilas pues!</Say></Response>',
                        to=num_call, from_=NUMERO_VOZ_PERSONAL
                    )
                except: print("Llamada fallida - Posible límite de Twilio o permisos.")

            except Exception as e:
                enviar_whatsapp(From, "¡Vea pues! Tuve un problema leyendo el PDF. Verifique que no tenga contraseña.")

    # --- COMANDOS DE TEXTO ---
    elif Body:
        msg = Body.lower().strip()
        if "ahorro" in msg or "cuanto" in msg:
            conn = sqlite3.connect(DB_NAME)
            res = conn.execute("SELECT SUM(monto) FROM hallazgos").fetchone()[0] or 0
            conn.close()
            enviar_whatsapp(From, f"💰 *Reporte de Mina de Oro:*\nHasta ahora le hemos salvado ${res:,.0f} pesos. ¡Esa platica no se regala!")
        elif "historial" in msg:
            conn = sqlite3.connect(DB_NAME)
            filas = conn.execute("SELECT fecha, detalle FROM hallazgos ORDER BY id DESC LIMIT 3").fetchall()
            conn.close()
            h_msg = "\n".join([f"📅 {f[0][:10]}: {f[1]}" for f in filas]) if filas else "Aún no tengo registros."
            enviar_whatsapp(From, f"📜 *Últimos Hallazgos:*\n{h_msg}")
        else:
            enviar_whatsapp(From, f"{random.choice(FRASES_BIENVENIDA)} Puede mandarme un PDF, un audio o escribir 'Ahorro'.")

    return Response(content=twiml_ok, media_type="application/xml")
