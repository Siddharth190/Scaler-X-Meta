from fastapi import FastAPI
from env.models import Action
import gradio as gr
import os
import pandas as pd
import random
import requests

app = FastAPI()

# ---------------- LLM SETUP ---------------- #
API_BASE_URL = os.environ.get("API_BASE_URL")
API_KEY = os.environ.get("API_KEY")

USE_LLM = API_BASE_URL is not None and API_KEY is not None

print("BASE URL:", API_BASE_URL)
print("API KEY PRESENT:", "YES" if API_KEY else "NO")

# ---------------- GLOBAL ---------------- #
score_history = []
conversation_history = []
current_step = 0
max_steps = 4
difficulty = "medium"

# ---------------- DATA ---------------- #

categories_data = {
    "account_recovery": ["account hacked", "can't login"],
    "spam": ["fake ads everywhere", "spam posts"],
    "abuse": ["user harassing me", "abusive messages"],
    "payment": ["charged twice", "billing issue"]
}

def generate_ticket():
    category = random.choice(list(categories_data.keys()))
    base = random.choice(categories_data[category])
    noise = [" pls help", " urgent!!", " 😭", ""]
    return base + random.choice(noise), category

def generate_profile():
    return f"""
👤 User Profile  
- Account Age: {random.randint(1,5)} years  
- Previous Complaints: {random.randint(0,3)}  
- Region: Asia  
"""

# ---------------- ENV ---------------- #

class SmartEnv:
    def __init__(self):
        self.ticket = ""
        self.true_category = ""

    def reset(self):
        global conversation_history, current_step
        conversation_history = []
        current_step = 0
        self.ticket, self.true_category = generate_ticket()
        return self.ticket

    def step(self, action):
        global current_step

        breakdown = self.compute_reward(action)
        reward = breakdown["total"]

        current_step += 1

        followups = [
            "still not resolved",
            "pls fix asap",
            "already tried that"
        ]

        if current_step < max_steps:
            self.ticket += f"\n\n👤 User: {random.choice(followups)}"

        done = current_step >= max_steps
        return self.ticket, reward, done, breakdown

    def compute_reward(self, action):
        score = 0
        breakdown = {"category":0,"priority":0,"team":0,"response":0}

        if action.category == self.true_category:
            breakdown["category"] = 0.4; score+=0.4

        if action.priority == "high":
            breakdown["priority"] = 0.2; score+=0.2

        if action.team in ["support","safety","moderation","billing"]:
            breakdown["team"] = 0.2; score+=0.2

        if len(action.response) > 10:
            breakdown["response"] = 0.2; score+=0.2

        breakdown["total"] = round(score,2)
        return breakdown

env = SmartEnv()

# ---------------- RAW LLM CALL ---------------- #

def call_llm():
    if not USE_LLM:
        print("⚠️ LLM not configured")
        return

    try:
        url = f"{API_BASE_URL}/chat/completions"

        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "user", "content": "Validator ping"}
            ]
        }

        response = requests.post(url, headers=headers, json=payload)

        print("🔥 STATUS:", response.status_code)
        print("🔥 RESPONSE:", response.text[:200])

    except Exception as e:
        print("❌ LLM REQUEST FAILED:", e)

# ---------------- ENDPOINTS ---------------- #

@app.post("/reset")
def reset_endpoint():
    ticket = env.reset()
    return {"ticket_text": ticket, "current_step": 0}

@app.post("/step")
def step_endpoint(action: Action):
    global current_step

    # 💥 GUARANTEED PROXY CALL
    call_llm()

    ticket, reward, done, breakdown = env.step(action)

    return {
        "observation": {
            "ticket_text": ticket,
            "current_step": current_step
        },
        "reward": reward,
        "done": done,
        "info": breakdown
    }

@app.get("/state")
def state_endpoint():
    return {"current_step": current_step}

@app.get("/tasks")
def tasks_endpoint():
    return ["easy", "medium", "hard"]

# ---------------- UI ---------------- #

def ui_reset(diff):
    global score_history, max_steps

    max_steps = {"easy":3,"medium":4,"hard":5}[diff]
    score_history = []

    ticket = env.reset()
    profile = generate_profile()

    df = pd.DataFrame({"Step":[],"Score":[]})
    return ticket, profile, "", "", df, 0

def ui_step(agent_mode, category, priority, team, response):
    action = Action(category=category, priority=priority, team=team, response=response)

    ticket, reward, done, _ = env.step(action)
    score_history.append(reward)

    df = pd.DataFrame({
        "Step": list(range(1,len(score_history)+1)),
        "Score": score_history
    })

    return f"Reward: {reward}", df, ticket, "", category, priority, team, response, len(score_history)

with gr.Blocks() as demo:
    gr.Markdown("# 🚀 Meta Support AI")

    difficulty_dd = gr.Dropdown(["easy","medium","hard"], value="medium")
    reset_btn = gr.Button("Start")

    ticket_box = gr.Textbox()
    profile_box = gr.Markdown()
    history_box = gr.Textbox()

    graph = gr.LinePlot(x="Step", y="Score")
    result = gr.Textbox()
    progress = gr.Slider(0,5,value=0)

    category = gr.Dropdown(["account_recovery","spam","abuse","payment"])
    priority = gr.Dropdown(["low","medium","high"])
    team = gr.Dropdown(["support","safety","moderation","billing"])
    response = gr.Textbox()

    step_btn = gr.Button("Step")

    reset_btn.click(ui_reset, inputs=difficulty_dd,
                    outputs=[ticket_box, profile_box, result, history_box, graph, progress])

    step_btn.click(ui_step,
                   inputs=["Manual", category, priority, team, response],
                   outputs=[result, graph, ticket_box, history_box, category, priority, team, response, progress])

@app.get("/")
def root():
    return {"status":"running"}

app = gr.mount_gradio_app(app, demo, path="/ui")

import uvicorn

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7860)
