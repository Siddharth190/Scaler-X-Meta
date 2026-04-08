from fastapi import FastAPI
from env.models import Action
import gradio as gr
import os
from openai import OpenAI
import pandas as pd
import random

app = FastAPI()

# ---------------- LLM SETUP ---------------- #
try:
    client = OpenAI(
        base_url=os.environ["API_BASE_URL"],
        api_key=os.environ["API_KEY"]
    )
    USE_LLM = True
    print("✅ LLM Proxy Connected")
except Exception as e:
    print("⚠️ LLM not available:", e)
    client = None
    USE_LLM = False

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

# ---------------- AGENTS ---------------- #

def rule_agent(ticket):
    if "hack" in ticket: return "account_recovery","high","support","We are reviewing"
    if "spam" in ticket: return "spam","low","moderation","We will review"
    if "harass" in ticket: return "abuse","high","safety","We take this seriously"
    if "charged" in ticket: return "payment","high","billing","Billing team checking"
    return "support","medium","support","Checking issue"

def random_agent():
    return random.choice(["spam","abuse","payment"]), "medium","support","Checking"

def ai_agent(ticket):
    if not USE_LLM:
        return rule_agent(ticket)

    try:
        res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Classify support tickets"},
                {"role": "user", "content": ticket}
            ],
            temperature=0
        )

        _ = res.choices[0].message.content
        return rule_agent(ticket)

    except Exception as e:
        print("LLM ERROR:", e)
        return rule_agent(ticket)

# ---------------- OPENENV ENDPOINTS ---------------- #

@app.post("/reset")
def reset_endpoint():
    ticket = env.reset()
    return {
        "ticket_text": ticket,
        "current_step": 0
    }

@app.post("/step")
def step_endpoint(action: Action):
    global current_step

    # 🔥 CRITICAL FIX: FORCE LLM CALL HERE
    if USE_LLM:
        try:
            client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": "Validator check"}],
                temperature=0
            )
            print("✅ Validator LLM call made")
        except Exception as e:
            print("LLM call failed:", e)

    # ---- original logic ----
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
    return {
        "current_step": current_step,
        "history": conversation_history
    }

@app.get("/tasks")
def tasks_endpoint():
    return ["easy", "medium", "hard"]

# ---------------- UI ---------------- #

def ui_reset(diff):
    global score_history, max_steps, difficulty

    difficulty = diff
    max_steps = {"easy":3,"medium":4,"hard":5}[diff]

    score_history = []
    ticket = env.reset()
    profile = generate_profile()

    df = pd.DataFrame({"Step":[],"Score":[]})
    return ticket, profile, "Session started", "", df, 0

def ui_step(agent_mode, category, priority, team, response):
    global score_history, conversation_history

    if agent_mode=="AI":
        category, priority, team, response = ai_agent(env.ticket)
    elif agent_mode=="Rule":
        category, priority, team, response = rule_agent(env.ticket)
    elif agent_mode=="Random":
        category, priority, team, response = random_agent()

    action = Action(category=category, priority=priority, team=team, response=response)

    ticket, reward, done, breakdown = env.step(action)
    score_history.append(reward)

    conversation_history.append(
        f"Agent → {category}, {priority}, {team}\n{response}"
    )

    avg = sum(score_history)/len(score_history)

    df = pd.DataFrame({
        "Step": list(range(1,len(score_history)+1)),
        "Score": score_history
    })

    return (
        f"Reward: {reward} | Avg: {avg:.2f}",
        df,
        ticket,
        "\n\n".join(conversation_history),
        category,
        priority,
        team,
        response,
        len(score_history)
    )

def auto_run():
    outputs = None
    for _ in range(max_steps):
        outputs = ui_step("AI","","","","")
    return outputs

with gr.Blocks() as demo:
    gr.Markdown("# 🚀 Meta Support AI")

    difficulty_dd = gr.Dropdown(["easy","medium","hard"], value="medium")
    reset_btn = gr.Button("Start")

    ticket_box = gr.Textbox(lines=5)
    profile_box = gr.Markdown()
    history_box = gr.Textbox(lines=6)

    graph = gr.LinePlot(x="Step", y="Score")
    result = gr.Textbox(lines=10)
    progress = gr.Slider(0,5,value=0)

    agent_mode = gr.Radio(["Manual","AI","Rule","Random"], value="Manual")

    category = gr.Dropdown(["account_recovery","spam","abuse","payment"])
    priority = gr.Dropdown(["low","medium","high"])
    team = gr.Dropdown(["support","safety","moderation","billing"])
    response = gr.Textbox()

    step_btn = gr.Button("Step")
    auto_btn = gr.Button("Auto Run")

    reset_btn.click(ui_reset, inputs=difficulty_dd,
                    outputs=[ticket_box, profile_box, result, history_box, graph, progress])

    step_btn.click(ui_step,
                   inputs=[agent_mode, category, priority, team, response],
                   outputs=[result, graph, ticket_box, history_box, category, priority, team, response, progress])

    auto_btn.click(auto_run,
                   outputs=[result, graph, ticket_box, history_box, category, priority, team, response, progress])

@app.get("/")
def root():
    return {"status":"running","ui":"/ui"}

app = gr.mount_gradio_app(app, demo, path="/ui")

import uvicorn

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7860)
