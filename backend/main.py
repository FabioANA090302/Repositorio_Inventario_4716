from fastapi import FastAPI, Query, Body
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
from config import RUTA_EXCEL
import smtplib
from email.message import EmailMessage
import random
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/", StaticFiles(directory="dist", html=True), name="frontend")

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

    # Agregar id único por fila
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
    """
    pedido = {
        "laboratorio": "Lab 1",
        "items": [
            {"id": 0, "DESCRIPCIÓN": "Taladro", "CANT": 2, "UBICACIÓN": "Bodega 1"},
            {"id": 1, "DESCRIPCIÓN": "Martillo", "CANT": 1, "UBICACIÓN": "Bodega 2"}
        ]
    }
    """
    try:
        ticket_id = random.randint(1000, 9999)
        email_msg = EmailMessage()
        email_msg["Subject"] = f"Pedido de Herramientas - Ticket #{ticket_id}"
        email_msg["From"] = os.environ.get("SMTP_USER")       # Reemplaza con tu email real
        email_msg["To"] = os.environ.get("SMTP_TO") 

        # Formatear mensaje
        mensaje = f"Ticket #{ticket_id}\nLaboratorio: {pedido.get('laboratorio')}\n\nDetalle del pedido:\n"
        for item in pedido.get("items", []):
            cantidad = item.get("CANT", 1)
            descripcion = item.get("DESCRIPCIÓN", "")
            ubicacion = item.get("UBICACIÓN", "")
            mensaje += f"- {cantidad} x {descripcion} (Ubicación: {ubicacion})\n"

        email_msg.set_content(mensaje)

        # Configuración SMTP (Gmail como ejemplo)
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        smtp_user = os.environ.get("SMTP_USER")     # Reemplaza con tu correo
        smtp_password = os.environ.get("SMTP_PASS")     # Usa contraseña de aplicación

        with smtplib.SMTP(smtp_server, smtp_port) as smtp:
            smtp.starttls()
            smtp.login(smtp_user, smtp_password)
            smtp.send_message(email_msg)

        return {"ok": True, "ticket_id": ticket_id, "mensaje": "Pedido enviado por correo"}

    except Exception as e:
        return {"ok": False, "error": str(e)}
