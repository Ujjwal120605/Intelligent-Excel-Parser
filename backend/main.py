from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
from mapping_engine import process_excel_file
from pydantic import BaseModel

app = FastAPI(title="LatSpace Data Mapping Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow localhost:3000 and any client
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "LatSpace Data Mapping Agent"}

@app.post("/parse")
async def parse_file(file: UploadFile = File(...)):
    if not file.filename.endswith(('.xlsx', '.csv', '.xls')):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload an Excel or CSV file.")

    # Save file temporarily
    temp_file_path = f"temp_{file.filename}"
    with open(temp_file_path, "wb") as buffer:
        buffer.write(await file.read())

    try:
        result = process_excel_file(temp_file_path)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
