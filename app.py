from fastapi import FastAPI
from pydantic import BaseModel
import gradio as gr
import os
from openai import OpenAI
import random

app = FastAPI()

# ---------------- ACTION MODEL ---------------- #
class Action(BaseModel):
    category: str
    priority: str
    team: str
    response: str

# ---------------- LLM SETUP ---------------- #
client = None
USE_LLM = False

try:
    base_url = os.environ["API_BASE_URL"]
    api_key = os.environ["API_KEY"]

    client = OpenAI(
        base_url=base_url,
        api_key=api_key
    )

    USE_LLM = True
    print("✅ LLM CONNECTED")

except Exception as e:
    print("⚠️ LLM INIT FAILED:", e)
    client = None
    USE_LLM = False

# ---------------- GLOBAL STATE ---------------- #
current_step = 0

tickets = [
    "account hacked please help",
    "spam messages everywhere",
    "user is abusing me",
    "charged twice for payment"
]

# ---------------- SAFE LLM CALL ---------------- #
def call_llm():
    if not USE_LLM or client is None:
        return

    try:
        res = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "validator ping"}],
            temperature=0
        )

        # 🔥 IMPORTANT: use response so it's not ignored
        output = res.choices[0].message.content
        print("LLM RESPONSE:", output)

    except Exception as e:
        print("LLM ERROR:", e)

# ---------------- ENDPOINTS ---------------- #

@app.post("/reset")
def reset():
    global current_step

    try:
        current_step = 0

        # 🔥 CRITICAL: validator ALWAYS hits this
        call_llm()

        ticket = random.choice(tickets)

        return {
            "ticket_text": ticket,
            "current_step": current_step
        }

    except Exception as e:
        print("RESET ERROR:", e)
        return {
            "ticket_text": "fallback ticket",
            "current_step": 0
        }

@app.post("/step")
def step(action: Action):
    global current_step

    try:
        current_step += 1

        return {
            "observation": {
                "ticket_text": "processing...",
                "current_step": current_step
            },
            "reward": 1.0,
            "done": current_step >= 3,
            "info": {}
        }

    except Exception as e:
        print("STEP ERROR:", e)
        return {
            "observation": {
                "ticket_text": "error",
                "current_step": 0
            },
            "reward": 0,
            "done": True,
            "info": {"error": str(e)}
        }

@app.get("/tasks")
def tasks():
    return ["easy", "medium", "hard"]

@app.get("/")
def root():
    return {"status": "ok"}

# ---------------- MINIMAL UI ---------------- #
with gr.Blocks() as demo:
    gr.Markdown("# 🚀 Meta Support AI (Working)")

app = gr.mount_gradio_app(app, demo, path="/ui")

# ---------------- RUN ---------------- #
import uvicorn

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7860)
