import requests
import json

OLLAMA_URL = "http://192.168.100.20:11434/api/chat"
MODEL = "qwen2.5:7b"

class LLMController:
    def __init__(self):
        self.current_response = None
        self.messages = []

    def chat(self, user_text):
        self.messages.append({"role": "user", "content": user_text})

        payload = {
            "model": MODEL,
            "messages": self.messages,
            "stream": True
        }

        self.current_response = requests.post(
            OLLAMA_URL,
            json=payload,
            stream=True,
            timeout=None
        )

        answer = ""
        try:
            for line in self.current_response.iter_lines():
                if not line:
                    continue
                data = json.loads(line.decode())
                if "message" in data:
                    token = data["message"]["content"]
                    answer += token
                    yield token
        except Exception:
            return

        self.messages.append({"role": "assistant", "content": answer})

    def interrupt(self):
        if self.current_response:
            self.current_response.close()
            self.current_response = None
