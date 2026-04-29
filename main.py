from fastapi import FastAPI , HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import analyser
app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:3000","https://fraudshield-frontend.vercel.app/","https://fraudshield-frontend.vercel.app"], allow_methods=["*"], allow_headers=["*"])
@app.get("/")
def health_check():
    return {"status": "FraudShield backend is running"}
@app.post("/analyse")
async def analyze_screenshot(file : UploadFile = File(...)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload an image.")
    image_bytes = await file.read()
    result = analyser.analyze(image_bytes, file.content_type)
    return result