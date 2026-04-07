def grade_easy(ticket, action):
    return 1.0 if action.category == ticket["category"] else 0.0

def grade_medium(ticket, action):
    score = 0
    if action.category == ticket["category"]:
        score += 0.4
    if action.priority == ticket["priority"]:
        score += 0.3
    if action.team == ticket["team"]:
        score += 0.3
    return score

def grade_hard(ticket, action):
    score = 0
    if action.category == ticket["category"]:
        score += 0.25
    if action.priority == ticket["priority"]:
        score += 0.25
    if action.team == ticket["team"]:
        score += 0.25
    if action.response and ticket["response"].lower() in action.response.lower():
        score += 0.25
    return score
