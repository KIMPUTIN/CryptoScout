


def score_project(project):
    score = 50
    reasons = []

    if project["website"]:
        score += 10
        reasons.append("Website available")

    if len(project["name"]) > 3:
        score += 5
        reasons.append("Proper naming")

    verdict = "WATCH"
    if score >= 70:
        verdict = "INVEST"
    elif score < 50:
        verdict = "AVOID"

    return score, verdict, ", ".join(reasons)