from fastapi import FastAPI
from env.environment import SupportTriageEnv
from env.models import Action

app = FastAPI()
env = SupportTriageEnv(task="easy")

# ---------------- BASIC ENDPOINTS ---------------- #

@app.post("/reset")
def reset(task: str = "easy"):
    env.set_task(task)
    return env.reset()

@app.post("/step")
def step(action: Action):
    return env.step(action)

@app.get("/state")
def state():
    return env.state()

@app.get("/tasks")
def tasks():
    return ["easy", "medium", "hard"]


# ---------------- GRADER ENDPOINT ---------------- #

@app.get("/grader")
def grader():
    # last step score
    last_ticket = env.current_ticket
    if not last_ticket:
        return {"error": "Run episode first"}

    # simple deterministic grading
    return {
        "task": env.task,
        "score": "Check last /step response"
    }


# ---------------- BASELINE ENDPOINT ---------------- #

@app.get("/baseline")
def baseline():
    results = {}

    for task in ["easy", "medium", "hard"]:
        env.set_task(task)
        obs = env.reset()

        # simple heuristic agent
        action = {
            "category": "account_recovery",
            "priority": "high",
            "team": "support",
            "response": "We are reviewing your issue"
        }

        _, score, _, _ = env.step(Action(**action))

        results[task] = score

    return {
        "baseline_scores": results
    }