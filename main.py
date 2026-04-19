from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from pdfitdown.pdfconversion import Converter
import os
import shutil
import uuid

app = FastAPI()

# CORS instellingen
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

converter = Converter()

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
        
        # Stuur PDF terug
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
