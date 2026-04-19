from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from pdfitdown.pdfconversion import Converter
import os
import shutil
import uuid
import json

app = FastAPI()

# CORS instellingen
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

converter = Converter()

# Google Drive instellingen (via environment variables)
DRIVE_FOLDER_ID = "1vJbJ2VczPr_PNk8oSoHjiqOpRGS-HMbU"
SERVICE_ACCOUNT_INFO = json.loads(os.environ.get("GOOGLE_CREDENTIALS", "{}"))

def upload_to_drive(file_path, filename):
    """Upload een bestand naar Google Drive"""
    if not SERVICE_ACCOUNT_INFO:
        return None
    
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload
        
        credentials = service_account.Credentials.from_service_account_info(
            SERVICE_ACCOUNT_INFO,
            scopes=["https://www.googleapis.com/auth/drive.file"]
        )
        drive_service = build("drive", "v3", credentials=credentials)
        
        file_metadata = {
            "name": filename,
            "parents": [DRIVE_FOLDER_ID]
        }
        media = MediaFileUpload(file_path, mimetype="application/pdf")
        file = drive_service.files().create(body=file_metadata, media_body=media, fields="id").execute()
        return file.get("id")
    except Exception as e:
        print(f"Drive upload failed: {e}")
        return None

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
        
        # Upload naar Google Drive (als credentials bestaan)
        upload_to_drive(output_path, f"{file.filename}.pdf")
        
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
