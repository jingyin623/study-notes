from fastapi import FastAPI
from llm_service.llm import LLMController
from fastapi.responses import StreamingResponse

app = FastAPI()
llm = LLMController()


@app.post("/chat")
def chat(user_text: str):
    return StreamingResponse(
        llm.chat(user_text),
        media_type="text/plain"
    )


@app.post("/interrupt")
def interrupt():
    llm.interrupt()
    return {"status": "interrupted"}
