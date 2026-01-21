
def analyze_project(project):
    score = 0
    reasons = []

    # Simple heuristics for MVP
    if len(project["name"]) >= 5:
        score += 25
        reasons.append("Strong branding")

    if project["symbol"].isupper():
        score += 25
        reasons.append("Exchange-friendly ticker")

    score += 30  # Trending bonus

    verdict = "Buy" if score >= 70 else "Watch"

    return {
        "score": score,
        "verdict": verdict,
        "reasons": ", ".join(reasons)
    }
