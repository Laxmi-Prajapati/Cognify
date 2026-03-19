from typing import List, Dict, Any


SEVERITY_LEVELS = {
    "critical": (0.75, 1.0),
    "high":     (0.5,  0.75),
    "medium":   (0.25, 0.5),
    "low":      (0.0,  0.25),
}


def compute_severity(
    ml_score: float,
    rule_violations: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Combines ML anomaly score with rule-based violations to produce
    a final severity label and composite score.

    Args:
        ml_score: normalized IsolationForest score [0, 1]
        rule_violations: list of triggered policy dicts from rule_engine

    Returns:
        dict with keys: score (float), level (str), contributing_factors (list)
    """
    # Base: ML score weighted at 40%
    composite = ml_score * 0.4

    # Rule violations weighted at 60% — use max severity_range midpoint
    if rule_violations:
        rule_scores = []
        for v in rule_violations:
            lo, hi = v.get("severity_range", [0.3, 0.5])
            rule_scores.append((lo + hi) / 2)
        composite += max(rule_scores) * 0.6
    
    composite = round(min(composite, 1.0), 4)

    # Map to level
    level = "low"
    for lvl, (lo, hi) in SEVERITY_LEVELS.items():
        if lo <= composite <= hi:
            level = lvl
            break

    # Build contributing factors list
    factors = []
    if ml_score > 0.5:
        factors.append(f"ML model flagged as anomalous (score: {ml_score:.2f})")
    for v in rule_violations:
        factors.append(v.get("policy_name", "Unknown policy"))

    return {
        "score": composite,
        "level": level,
        "contributing_factors": factors,
    }
