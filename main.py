import os
import fitz  # PyMuPDF
import requests
import sqlite3
import random
from datetime import datetime
from fastapi import FastAPI, Form, Response
from twilio.rest import Client
from langchain_openai import ChatOpenAI
from openai import OpenAI

app = FastAPI()

# --- 1. CONFIGURACIÓN ---
DB_NAME = "sentinel_memoria.db"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_TOKEN = os.getenv("TWILIO_TOKEN")
NUMERO_WHATSAPP_SANDBOX = "+14155238886" 
NUMERO_VOZ_PERSONAL = "+16812631834"    

client = Client(TWILIO_SID, TWILIO_TOKEN)
llm = ChatOpenAI(model="gpt-4o", api_key=OPENAI_API_KEY)
ai_client = OpenAI(api_key=OPENAI_API_KEY)

# --- 2. BASE DE DATOS ---
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

# --- 3. PERSONALIDAD COLOMBIANA ---
FRASES_BIENVENIDA = [
    "¡Qué alegría saludarle! Aquí sigo firme patrullando para cuidar su plata.",
    "¡Epa! Reciba un saludo muy especial. El Sentinel está activo.",
    "¡Hola, hola! Todo listo por acá para seguir cuidando su mina de oro."
]

# --- 4. FUNCIONES TÉCNICAS (LOS "SENTIDOS") ---
def enviar_whatsapp(to_number, mensaje):
    try:
        client.messages.create(from_=f"whatsapp:{NUMERO_WHATSAPP_SANDBOX}", body=mensaje, to=to_number)
    except:
        print("Aviso: Límite de mensajes de Twilio alcanzado hoy.")

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

# --- 5. WEBHOOK MAESTRO ---
@app.post("/webhook")
async def webhook_sentinel(
    MediaUrl0: str = Form(None), 
    MediaContentType0: str = Form(None),
    From: str = Form(...), 
    Body: str = Form(None)
):
    twiml_ok = '<?xml version="1.0" encoding="UTF-8"?><Response></Response>'
    
    if MediaUrl0:
        # CASO AUDIO
        if MediaContentType0 and "audio" in MediaContentType0:
            enviar_whatsapp(From, "👂 Escuchando su mensaje...")
            texto_voz = transcribir_audio(MediaUrl0)
            respuesta_ia = llm.invoke(f"Usuario dice: {texto_voz}. Responde corto y cálido en español de Colombia.").content
            enviar_whatsapp(From, f"Usted dijo: \"{texto_voz}\"\n\n🤖 {respuesta_ia}")

        # CASO PDF
        else:
            enviar_whatsapp(From, "¡Recibido! Déjeme le pego una ojeada a esos números...")
            texto_pdf = extraer_texto_pdf(MediaUrl0)
            
            # IA ANALIZA Y EXTRAE MONTO (Lógica de extracción real)
            prompt = f"Analiza este extracto: {texto_pdf[:3000]}. Identifica cobros injustos y dime el monto total de ahorro potencial. Responde en este formato: 'Hallazgo: [descripción] | Monto: [solo numero]'."
            analisis = llm.invoke(prompt).content
            
            # Guardar en DB (Intentamos extraer el número del texto de la IA)
            monto_detectado = 0
            try:
                if "Monto:" in analisis:
                    monto_detectado = float(''.join(filter(str.isdigit, analisis.split("Monto:")[1])))
            except: pass

            conn = sqlite3.connect(DB_NAME)
            conn.execute("INSERT INTO hallazgos (fecha, detalle, monto) VALUES (?, ?, ?)", 
                         (datetime.now().strftime("%Y-%m-%d"), analisis[:200], monto_detectado))
            conn.commit()
            conn.close()
            
            enviar_whatsapp(From, f"✅ Auditoría terminada:\n{analisis}")
            
            # Celebración si hay ahorro acumulado
            conn = sqlite3.connect(DB_NAME)
            total = conn.execute("SELECT SUM(monto) FROM hallazgos").fetchone()[0] or 0
            conn.close()
            
            if total >= 100000:
                enviar_whatsapp(From, f"🎉 ¡Epa! ¡Ya le hemos ahorrado ${total:,.0f} pesos! Esa platica se queda en la mina de oro.")

            # Llamada de aviso
            client.calls.create(
                twiml=f'<Response><Pause length="2"/><Say language="es-MX" voice="Polly.Miguel">Hola, su auditoria esta lista. Revise los detalles en su chat para proteger su dinero.</Say></Response>',
                to=From.replace("whatsapp:", ""),
                from_=NUMERO_VOZ_PERSONAL
            )

    elif Body:
        cmd = Body.lower().strip()
        if "ahorro" in cmd or "cuanto" in cmd:
            conn = sqlite3.connect(DB_NAME)
            total = conn.execute("SELECT SUM(monto) FROM hallazgos").fetchone()[0] or 0
            conn.close()
            enviar_whatsapp(From, f"💰 Llevamos un ahorro total de ${total:,.0f} pesos. ¡No regalamos ni un centavo!")
        elif "historial" in cmd:
            conn = sqlite3.connect(DB_NAME)
            filas = conn.execute("SELECT fecha, detalle FROM hallazgos ORDER BY id DESC LIMIT 3").fetchall()
            conn.close()
            msg = "\n".join([f"📅 {f[0]}: {f[1]}" for f in filas]) if filas else "Aun no tengo registros."
            enviar_whatsapp(From, f"📜 Esto he encontrado:\n{msg}")
        else:
            enviar_whatsapp(From, f"{random.choice(FRASES_BIENVENIDA)} Mándeme el PDF para auditar o un audio con su duda.")

    return Response(content=twiml_ok, media_type="application/xml")
