"""
ARIA — Visualizations
Generates charts from the final report dict.
Requires: pip install matplotlib plotly
"""

from __future__ import annotations

import os
from datetime import datetime


OUTPUT_DIR = "outputs/charts"


def _ensure_dir() -> str:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    return OUTPUT_DIR


def _ts() -> str:
    return datetime.utcnow().strftime("%Y%m%d_%H%M%S")


def render_charts(report: dict) -> list[str]:
    """
    Generate charts from the report and return a list of file paths.
    Tries matplotlib first, falls back gracefully if unavailable.
    """
    paths = []
    try:
        import matplotlib
        matplotlib.use("Agg")  # non-interactive backend
        import matplotlib.pyplot as plt
    except ImportError:
        return []

    out_dir = _ensure_dir()
    ts      = _ts()

    # ── Chart 1 — KPI Overview (bar chart) ───────────────────
    kpi_data = report.get("2_data_summary", {}).get(
        "consolidated_dataset", {}
    ).get("kpi_data", {})

    if kpi_data:
        labels = list(kpi_data.keys())
        avgs   = [kpi_data[k].get("avg", 0) for k in labels]

        fig, ax = plt.subplots(figsize=(10, 5))
        bars = ax.bar(labels, avgs, color="#2c7bb6", edgecolor="white")
        ax.set_title("KPI Overview — Averages", fontsize=14, fontweight="bold")
        ax.set_ylabel("Average Value")
        ax.set_xlabel("KPI")
        ax.bar_label(bars, fmt="%.2f", padding=3)
        plt.xticks(rotation=30, ha="right")
        plt.tight_layout()
        path = os.path.join(out_dir, f"kpi_overview_{ts}.png")
        plt.savefig(path, dpi=150)
        plt.close()
        paths.append(path)

    # ── Chart 2 — Confidence Score (gauge-style horizontal bar) ─
    confidence = report.get("6_confidence", {}).get("score", 0.0)
    fig, ax = plt.subplots(figsize=(6, 2))
    color = "#2ecc71" if confidence >= 0.70 else "#e67e22" if confidence >= 0.40 else "#e74c3c"
    ax.barh(["Confidence"], [confidence], color=color, height=0.4)
    ax.barh(["Confidence"], [1.0], color="#ecf0f1", height=0.4, zorder=0)
    ax.set_xlim(0, 1)
    ax.set_title(f"Analysis Confidence: {confidence * 100:.1f}%", fontsize=12, fontweight="bold")
    ax.axvline(x=0.70, color="#2c3e50", linestyle="--", linewidth=1, label="Threshold 70%")
    ax.legend(loc="lower right", fontsize=8)
    ax.set_xlabel("Score")
    plt.tight_layout()
    path = os.path.join(out_dir, f"confidence_{ts}.png")
    plt.savefig(path, dpi=150)
    plt.close()
    paths.append(path)

    # ── Chart 3 — TRIZ Contradictions (horizontal bar) ───────
    triz          = report.get("3_triz_analysis", {})
    contradictions = triz.get("contradictions", [])

    if contradictions:
        labels  = [f"#{i+1} {c.get('type','').upper()}" for i, c in enumerate(contradictions)]
        values  = [1] * len(labels)
        colors  = ["#e74c3c" if c.get("type") == "technical" else "#9b59b6" for c in contradictions]

        fig, ax = plt.subplots(figsize=(8, max(3, len(labels) * 0.8)))
        ax.barh(labels, values, color=colors, height=0.5)
        ax.set_xlim(0, 1.5)
        ax.set_title("TRIZ — Identified Contradictions", fontsize=12, fontweight="bold")
        ax.set_xticks([])
        for i, c in enumerate(contradictions):
            ax.text(0.05, i, f"{c.get('improving_parameter','')} ↑  vs  {c.get('degrading_parameter','')} ↓",
                    va="center", fontsize=8, color="white", fontweight="bold")
        plt.tight_layout()
        path = os.path.join(out_dir, f"contradictions_{ts}.png")
        plt.savefig(path, dpi=150)
        plt.close()
        paths.append(path)

    # ── Chart 4 — Recommendations by Priority (pie chart) ────
    recs = report.get("5_recommendations", [])
    if recs:
        priority_counts: dict = {"High": 0, "Medium": 0, "Low": 0}
        for r in recs:
            p = r.get("priority", "Medium")
            priority_counts[p] = priority_counts.get(p, 0) + 1

        counts = [v for v in priority_counts.values() if v > 0]
        labels = [k for k, v in priority_counts.items() if v > 0]
        colors = {"High": "#e74c3c", "Medium": "#e67e22", "Low": "#2ecc71"}
        pie_colors = [colors[l] for l in labels]

        fig, ax = plt.subplots(figsize=(5, 5))
        ax.pie(counts, labels=labels, colors=pie_colors,
               autopct="%1.0f%%", startangle=90, pctdistance=0.8)
        ax.set_title("Recommendations by Priority", fontsize=12, fontweight="bold")
        plt.tight_layout()
        path = os.path.join(out_dir, f"recommendations_{ts}.png")
        plt.savefig(path, dpi=150)
        plt.close()
        paths.append(path)

    return paths