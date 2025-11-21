from fastapi import FastAPI, Query, Body
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import os
import smtplib
from email.message import EmailMessage
import random

from config import RUTA_EXCEL  # Asegúrate de tener config.py con RUTA_EXCEL

app = FastAPI()

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

        # Configuración desde variables de entorno
        smtp_user = os.environ.get("SMTP_USER")
        smtp_pass = os.environ.get("SMTP_PASS")
        smtp_to = os.environ.get("SMTP_TO")

        if not smtp_user or not smtp_pass or not smtp_to:
            return {"ok": False, "error": "Variables SMTP no configuradas"}

        email_msg = EmailMessage()
        email_msg["Subject"] = f"Pedido de Herramientas - Ticket #{ticket_id}"
        email_msg["From"] = smtp_user
        email_msg["To"] = smtp_to

        mensaje = f"Ticket #{ticket_id}\nLaboratorio: {pedido.get('laboratorio')}\n\nDetalle del pedido:\n"
        for item in pedido.get("items", []):
            cantidad = int(item.get("CANT", 1))
            descripcion = item.get("DESCRIPCIÓN", "")
            ubicacion = item.get("UBICACIÓN", "")
            mensaje += f"- {cantidad} x {descripcion} (Ubicación: {ubicacion})\n"

        email_msg.set_content(mensaje)

        # SMTP
        with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
            smtp.starttls()
            smtp.login(smtp_user, smtp_pass)
            smtp.send_message(email_msg)

        return {"ok": True, "ticket_id": ticket_id}

    except Exception as e:
        print("Error al enviar pedido:", e)
        return {"ok": False, "error": str(e)}
