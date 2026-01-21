
def analyze_project(project):
    score = 0
    reasons = []

    # Simple heuristics for MVP
    if len(project["name"]) > 4:
        score += 20
        reasons.append("Strong branding")

    if project["symbol"].isupper():
        score += 20
        reasons.append("Exchange friendly ticker")

    score += 40  # Trending bonus

    verdict = "Buy" if score >= 70 else "Watch"

    return {
        "score": score,
        "verdict": verdict,
        "reasons": ", ".join(reasons)
    }
