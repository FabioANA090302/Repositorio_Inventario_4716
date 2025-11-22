from fastapi import FastAPI, Query, Body
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import os
import random
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from config import RUTA_EXCEL  # Debes tener config.py con RUTA_EXCEL

app = FastAPI()

# Habilitar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🔹 Endpoint 1: obtener lista de laboratorios
@app.get("/laboratorios")
def obtener_labs():
    xls = pd.ExcelFile(RUTA_EXCEL)
    return {"laboratorios": xls.sheet_names}

# 🔹 Endpoint 2: cargar una hoja específica
@app.get("/laboratorio")
def obtener_laboratorio(nombre: str = Query(...)):
    try:
        df = pd.read_excel(RUTA_EXCEL, sheet_name=nombre, header=None)
        encabezados = df.iloc[8]  
        df = df.iloc[9:]          
        df.columns = encabezados
        df = df.dropna(axis=1, how='all')
        df = df.dropna(how='all')
    except Exception as e:
        return {"error": f"No se pudo leer la hoja: {str(e)}"}

    filas = df.fillna("").to_dict(orient="records")
    for idx, fila in enumerate(filas):
        fila["id"] = idx
    return {
        "laboratorio": nombre,
        "columnas": list(df.columns),
        "filas": filas
    }

# 🔹 Endpoint 3: pedir herramientas
@app.post("/pedir")
def pedir_herramientas(pedido: dict = Body(...)):
    try:
        print("POST recibido en /pedir:", pedido)
        ticket_id = random.randint(1000, 9999)

        # Variables de entorno para SendGrid
        sendgrid_api_key = os.environ.get("SENDGRID_API_KEY")
        smtp_user = os.environ.get("SMTP_USER")
        smtp_to = os.environ.get("SMTP_TO")

        if not sendgrid_api_key or not smtp_user or not smtp_to:
            return {"ok": False, "error": "Variables SendGrid/Sender no configuradas"}

        # Crear mensaje
        mensaje_texto = f"Ticket #{ticket_id}\nLaboratorio: {pedido.get('laboratorio')}\n\nDetalle del pedido:\n"
        for item in pedido.get("items", []):
            cantidad = int(item.get("CANT", 1))
            descripcion = item.get("DESCRIPCIÓN", "")
            ubicacion = item.get("UBICACIÓN", "")
            mensaje_texto += f"- {cantidad} x {descripcion} (Ubicación: {ubicacion})\n"

        mail = Mail(
            from_email=smtp_user,
            to_emails=smtp_to,
            subject=f"Pedido de Herramientas - Ticket #{ticket_id}",
            plain_text_content=mensaje_texto
        )

        sg = SendGridAPIClient(sendgrid_api_key)
        sg.send(mail)

        return {"ok": True, "ticket_id": ticket_id, "mensaje": "Pedido enviado por correo"}

    except Exception as e:
        print("Error al enviar pedido:", e)
        return {"ok": False, "error": str(e)}
