import requests

BASE_URL = "http://localhost:7860"

def run_task(task):
    print(f"Running {task}")
    requests.post(f"{BASE_URL}/reset")

    action = {
        "category": "account_recovery",
        "priority": "high",
        "team": "support",
        "response": "We are looking into your issue"
    }

    res = requests.post(f"{BASE_URL}/step", json=action)
    print(res.json())

if __name__ == "__main__":
    for t in ["easy", "medium", "hard"]:
        run_task(t)
