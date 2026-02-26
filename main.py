import os
import fitz  # PyMuPDF para leer el PDF
import requests
from fastapi import FastAPI, Form, Response
from twilio.rest import Client
from langchain_openai import ChatOpenAI

app = FastAPI()

# Configuración
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_TOKEN = os.getenv("TWILIO_TOKEN")
NUMERO_WHATSAPP_SANDBOX = "+14155238886" 
NUMERO_VOZ_PERSONAL = "+16812631834"    

client = Client(TWILIO_SID, TWILIO_TOKEN)
llm = ChatOpenAI(model="gpt-4o", api_key=OPENAI_API_KEY)

def analizar_con_ia(texto_pdf):
    """La IA revisa el texto y busca cobros sospechosos"""
    prompt = f"Eres un auditor financiero experto. Revisa este extracto y dime si hay cobros de seguros, comisiones o gastos inusuales. Resumen muy corto para WhatsApp: {texto_pdf}"
    respuesta = llm.invoke(prompt)
    return respuesta.content

def extraer_texto_pdf(url_media):
    """Descarga el PDF y saca las letras"""
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
        # 1. Avisar que estamos trabajando
        client.messages.create(from_=f"whatsapp:{NUMERO_WHATSAPP_SANDBOX}", body="🔍 Leyendo su extracto... un momento.", to=From)
        
        # 2. Procesar el PDF real
        texto_extraido = extraer_texto_pdf(MediaUrl0)
        analisis = analizar_con_ia(texto_extraido)
        
        # 3. Enviar el resultado real
        client.messages.create(from_=f"whatsapp:{NUMERO_WHATSAPP_SANDBOX}", body=f"✅ Auditoría lista:\n{analisis}", to=From)
        
        # 4. Llamada de alerta (Inclusión)
        client.calls.create(
            twiml=f'<Response><Pause length="2"/><Say language="es-MX" voice="man">Arquitecto, auditoria terminada. Revise su guasap. Encontre novedades en su extracto.</Say></Response>',
            to=From.replace("whatsapp:", ""),
            from_=NUMERO_VOZ_PERSONAL
        )

    return Response(content='<?xml version="1.0" encoding="UTF-8"?><Response></Response>', media_type="application/xml")
