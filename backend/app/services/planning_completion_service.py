"""Vollständigkeitsprüfung der Planungsschritte (Idee + 10 Artefakte)."""

from app.services.planning_constants import ARTIFACT_LABELS, ARTIFACT_ORDER

PROJECT_IDEA_KEY = "project_idea"
PROJECT_IDEA_LABEL = "Projektidee"


def assess_planning_completion(project_idea: str, artifacts: list[dict]) -> dict:
    """Ermittelt Fortschritt, fehlende Schritte und Freigabe-Status."""
    artifact_by_slug = {a["slug"]: a for a in artifacts}
    steps: list[dict] = []
    missing_labels: list[str] = []

    idea_filled = bool(project_idea.strip())
    steps.append(
        {
            "key": PROJECT_IDEA_KEY,
            "label": PROJECT_IDEA_LABEL,
            "filled": idea_filled,
            "status": "draft" if idea_filled else "pending",
        }
    )
    if not idea_filled:
        missing_labels.append(PROJECT_IDEA_LABEL)

    filled_artifacts = 0
    approved_artifacts = 0

    for slug in ARTIFACT_ORDER:
        label = ARTIFACT_LABELS.get(slug, slug)
        item = artifact_by_slug.get(slug)
        filled = bool(item and item.get("has_content"))
        art_status = item.get("status", "pending") if item else "pending"

        if filled:
            filled_artifacts += 1
        else:
            missing_labels.append(label)
        if art_status == "approved" and filled:
            approved_artifacts += 1

        steps.append(
            {
                "key": slug,
                "label": label,
                "filled": filled,
                "status": art_status if filled else "pending",
            }
        )

    total_artifacts = len(ARTIFACT_ORDER)
    filled_count = (1 if idea_filled else 0) + filled_artifacts
    total_count = 1 + total_artifacts
    approved_count = (1 if idea_filled else 0) + approved_artifacts
    is_complete = filled_count == total_count
    is_fully_approved = approved_count == total_count

    return {
        "has_project_idea": idea_filled,
        "filled_count": filled_count,
        "total_count": total_count,
        "artifact_filled": filled_artifacts,
        "artifact_total": total_artifacts,
        "approved_count": approved_count,
        "is_complete": is_complete,
        "is_fully_approved": is_fully_approved,
        "missing_labels": missing_labels,
        "steps": steps,
    }
