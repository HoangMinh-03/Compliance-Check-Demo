import uvicorn
import logging
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from src.api.routes import router as compliance_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Compliance Checker API")

# Mount static files (CSS, JS) from main_app
app.mount("/static", StaticFiles(directory="main_app"), name="static")

# Include compliance routes
app.include_router(compliance_router)

@app.get("/", response_class=HTMLResponse)
async def get_index():
    return FileResponse("main_app/index.html")

@app.get("/style.css")
async def get_style():
    return FileResponse("main_app/style.css")

if __name__ == "__main__":
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
