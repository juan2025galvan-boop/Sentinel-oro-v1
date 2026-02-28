import os
import fitz  # PyMuPDF
import requests
import random
import traceback # Para ver el error exacto
from datetime import datetime
from fastapi import FastAPI, Form, Response
from twilio.rest import Client
from langchain_openai import ChatOpenAI
from openai import OpenAI
from supabase import create_client, Client as SupabaseClient

app = FastAPI()

# --- 1. CONFIGURACIÓN ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_TOKEN = os.getenv("TWILIO_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

NUMERO_WHATSAPP_SANDBOX = "+14155238886" 
NUMERO_VOZ_PERSONAL = "+16812631834"    

# --- 2. CLIENTES ---
client = Client(TWILIO_SID, TWILIO_TOKEN)
llm = ChatOpenAI(model="gpt-4o", api_key=OPENAI_API_KEY)
ai_client = OpenAI(api_key=OPENAI_API_KEY)
supabase: SupabaseClient = create_client(SUPABASE_URL, SUPABASE_KEY)

FRASES_BIENVENIDA = [
    "¡Qué alegría saludarle! Aquí sigo firme patrullando para cuidar su plata. ¿Qué tenemos para revisar hoy?",
    "¡Epa! Reciba un saludo muy especial. El Sentinel está activo.",
    "¡Hola, hola! Todo listo por acá para seguir cuidando su mina de oro."
]

def enviar_whatsapp(to_number, mensaje):
    try:
        client.messages.create(from_=f"whatsapp:{NUMERO_WHATSAPP_SANDBOX}", body=mensaje, to=to_number)
    except Exception as e:
        print(f"Error de conexión con Twilio: {e}")

def extraer_texto_pdf(url_media):
    # SOLUCIÓN 1: Le pasamos las llaves de Twilio para que deje descargar el PDF real
    response = requests.get(url_media, auth=(TWILIO_SID, TWILIO_TOKEN))
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

def guardar_hallazgo_en_nube(detalle, monto):
    # Quitamos el pass para que nos diga si la tabla falla
    data = {
        "fecha": datetime.now().strftime("%Y-%m-%d"),
        "detalle": detalle,
        "monto": float(monto)
    }
    supabase.table("hallazgos").insert(data).execute()

# --- 5. WEBHOOK MAESTRO ---
@app.post("/webhook")
async def webhook_sentinel(
    MediaUrl0: str = Form(None), 
    MediaContentType0: str = Form(None),
    From: str = Form(...), 
    Body: str = Form(None)
):
    twiml_ok = '<?xml version="1.0" encoding="UTF-8"?><Response></Response>'
    
    # SOLUCIÓN 2: Envolvemos TODO en un Try-Except que le avisa al WhatsApp si algo estalla
    try:
        if MediaUrl0:
            if MediaContentType0 and "audio" in MediaContentType0:
                enviar_whatsapp(From, "👂 Escuchando su mensaje...")
                texto_voz = transcribir_audio(MediaUrl0)
                respuesta_ia = llm.invoke(f"Usuario dice: {texto_voz}. Responde corto y cálido en español de Colombia.").content
                enviar_whatsapp(From, f"Usted dijo: \"{texto_voz}\"\n\n🤖 {respuesta_ia}")

            else:
                enviar_whatsapp(From, "¡Recibido! Déjeme le pego una ojeada a esos números...")
                texto_pdf = extraer_texto_pdf(MediaUrl0)
                
                prompt = f"Analiza este extracto: {texto_pdf[:3000]}. Identifica cobros injustos y dime el monto total. Responde: 'Concepto: [desc] | Monto: [solo numero]'."
                analisis = llm.invoke(prompt).content
                
                monto_final = 0
                try:
                    if "Monto:" in analisis:
                        monto_final = float(''.join(filter(str.isdigit, analisis.split("Monto:")[1])))
                except: pass

                guardar_hallazgo_en_nube(analisis[:100], monto_final)
                enviar_whatsapp(From, f"✅ Auditoría lista:\n{analisis}")
                
                try:
                    client.calls.create(
                        twiml=f'<Response><Pause length="2"/><Say language="es-MX">Hola, el Sentinel ha terminado su auditoria. Revise su WhatsApp.</Say></Response>',
                        to=From.replace("whatsapp:", ""),
                        from_=NUMERO_VOZ_PERSONAL
                    )
                except Exception as error_llamada:
                    enviar_whatsapp(From, f"⚠️ El análisis se guardó, pero falló la llamada. Error: {str(error_llamada)}")

        elif Body:
            cmd = Body.lower().strip()
            if "ahorro" in cmd or "cuanto" in cmd:
                res = supabase.table("hallazgos").select("monto").execute()
                total = sum(item['monto'] for item in res.data) if res.data else 0
                enviar_whatsapp(From, f"💰 Llevamos un ahorro total de ${total:,.0f} pesos. ¡No regalamos nada!")
            else:
                enviar_whatsapp(From, f"{random.choice(FRASES_BIENVENIDA)} Mándeme un PDF o un audio.")

    except Exception as e:
        # SI ALGO FALLA, EL SENTINEL LE GRITA AL WHATSAPP
        print(traceback.format_exc())
        enviar_whatsapp(From, f"🚨 ALERTA ROJA 🚨\nJefe, el sistema se frenó en seco. Este es el error técnico:\n\n{str(e)}")

    return Response(content=twiml_ok, media_type="application/xml")
