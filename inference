import requests

BASE_URL = "http://localhost:7860"

def run_task(task):
    print(f"\nRunning task: {task}")

    # Reset
    r = requests.post(f"{BASE_URL}/reset")
    obs = r.json()

    done = False
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

        total_reward += data["reward"]
        done = data["done"]

    return total_reward


def main():
    tasks = ["easy", "medium", "hard"]
    results = {}

    for t in tasks:
        score = run_task(t)
        results[t] = score

    print("\nFinal Scores:")
    print(results)


if __name__ == "__main__":
    main()
