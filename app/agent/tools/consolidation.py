"""
ARIA — Consolidation Tool
Merges all processed data + RAG context into one unified dataset.
"""

from __future__ import annotations
from datetime import datetime


def consolidate_report(
    processed_data:  list[dict],
    rag_context:     list[str],
    domain:          str = "",
    kpis:            list[str] | None = None,
    reporting_period: str = "",
) -> dict:
    """
    Merge processed data records and RAG context into a single
    unified dataset ready for TRIX analysis.

    Returns:
        dict with keys: domain, period, kpis, records, rag_context,
                        stats, consolidated_at
    """
    kpis = kpis or []

    # ── Flatten all processed records ─────────────────────────
    all_records: list[dict] = []
    source_summary: list[dict] = []

    for entry in processed_data:
        if isinstance(entry, list):
            all_records.extend([r for r in entry if isinstance(r, dict)])
            source_summary.append({"type": "list", "count": len(entry)})
        elif isinstance(entry, dict):
            data = entry.get("data") or entry.get("rows") or entry.get("pages")
            if isinstance(data, list):
                all_records.extend([r for r in data if isinstance(r, dict)])
                source_summary.append({
                    "source_id":   entry.get("source_id", "unknown"),
                    "source_type": entry.get("source_type", "unknown"),
                    "count":       len(data),
                })
            elif isinstance(data, dict):
                all_records.append(data)
                source_summary.append({
                    "source_id":   entry.get("source_id", "unknown"),
                    "source_type": entry.get("source_type", "unknown"),
                    "count":       1,
                })
            else:
                # Flat dict record
                all_records.append(entry)
                source_summary.append({"type": "flat", "count": 1})

    # ── Compute basic stats on numeric fields ─────────────────
    stats: dict = {}
    if all_records:
        sample = all_records[0]
        for field in sample:
            vals = []
            for rec in all_records:
                v = rec.get(field)
                try:
                    vals.append(float(v))
                except (TypeError, ValueError):
                    pass
            if vals:
                stats[field] = {
                    "count": len(vals),
                    "sum":   round(sum(vals), 4),
                    "avg":   round(sum(vals) / len(vals), 4),
                    "min":   min(vals),
                    "max":   max(vals),
                }

    # ── KPI extraction from records ───────────────────────────
    kpi_data: dict = {}
    for kpi in kpis:
        kpi_lower = kpi.lower().replace(" ", "_")
        vals = [
            float(rec[k]) for rec in all_records
            for k in rec if kpi_lower in k.lower()
            and _is_numeric(rec[k])
        ]
        if vals:
            kpi_data[kpi] = {
                "avg": round(sum(vals) / len(vals), 4),
                "sum": round(sum(vals), 4),
                "min": min(vals),
                "max": max(vals),
            }

    return {
        "domain":           domain,
        "reporting_period": reporting_period,
        "kpis":             kpis,
        "kpi_data":         kpi_data,
        "records":          all_records,
        "record_count":     len(all_records),
        "source_summary":   source_summary,
        "stats":            stats,
        "rag_context":      rag_context,
        "rag_chunks_used":  len(rag_context),
        "consolidated_at":  datetime.utcnow().isoformat(),
    }


def _is_numeric(val) -> bool:
    try:
        float(val)
        return True
    except (TypeError, ValueError):
        return False
