import sys
from pathlib import Path

_main_dir = str(Path(__file__).resolve().parent)
_parent_dir = str(Path(__file__).resolve().parent.parent)

if _main_dir not in sys.path:
    sys.path.insert(0, _main_dir)

try:
    from routes import router
except ImportError:
    if _parent_dir not in sys.path:
        sys.path.insert(0, _parent_dir)
    from api.routes import router

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Home Automation - Device Gateway",
    description="Central FastAPI server for ESP32-C3 home automation nodes. "
                "Handles device registration, WebSocket real-time control, "
                "and relay state management.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/", summary="Root health check")
async def root():
    return {
        "service": "Home Automation Gateway",
        "status": "running",
        "docs": "/docs",
    }


if __name__ == "__main__":
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)
