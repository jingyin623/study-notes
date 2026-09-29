from fastapi import FastAPI
import threading
from vad_service.vad import listen

app = FastAPI()

@app.on_event("startup")
def start_vad():
    threading.Thread(target=listen, daemon=True).start()
