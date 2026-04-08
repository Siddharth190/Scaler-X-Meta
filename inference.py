import requests

BASE_URL = "http://localhost:7860"

def run_task(task):
    print(f"[START] task={task}", flush=True)

    r = requests.post(f"{BASE_URL}/reset")
    done = False
    step = 0
    total_reward = 0

    while not done:
        action = {
            "category": "account_recovery",
            "priority": "high",
            "team": "support",
            "response": "We are reviewing your issue"
        }

        r = requests.post(f"{BASE_URL}/step", json=action)
        data = r.json()

        reward = data["reward"]
        done = data["done"]

        step += 1
        total_reward += reward

        print(f"[STEP] step={step} reward={reward}", flush=True)

    score = total_reward / step if step > 0 else 0

    print(f"[END] task={task} score={score} steps={step}", flush=True)


def main():
    tasks = ["easy", "medium", "hard"]

    for t in tasks:
        run_task(t)


if __name__ == "__main__":
    main()
