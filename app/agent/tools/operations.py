"""
ARIA — Operation Tools
filter_data, aggregate_data, normalize_data, compare_data
"""

from __future__ import annotations
from typing import Any


def _extract_rows(rec) -> list:
    """
    Extrait une liste de dicts plats depuis n'importe quelle structure
    produite par le pipeline ARIA :
      - {"source_id":..., "data": {"rows":[...]}}  extractor wrapper
      - {"rows":[...], "columns":[...]}             outil dynamique direct
      - {"data":[...]}                              liste directe
      - {...}                                       dict plat
    """
    if not isinstance(rec, dict):
        return []
    data = rec.get("data") or rec.get("rows") or rec.get("pages")
    # Descendre d'un niveau si data est encore un dict avec "rows"
    if isinstance(data, dict):
        data = data.get("rows") or data.get("data") or data.get("pages") or data
    if isinstance(data, list):
        return [r for r in data if isinstance(r, dict)]
    if isinstance(data, dict):
        return [data]
    # Dict plat sans wrapper connu → l'enregistrement lui-même
    if not any(k in rec for k in ("data", "rows", "pages", "source_id", "extracted_at")):
        return [rec]
    return []



# ══════════════════════════════════════════════════════════════
# TOOL 5 — filter_data
# ══════════════════════════════════════════════════════════════

def filter_data(
    records: list[dict],
    conditions: dict | None = None,
    date_field: str | None = None,
    date_from:  str | None = None,
    date_to:    str | None = None,
    fields:     list[str] | None = None,
    **kwargs,
) -> list[dict]:
    """
    Filter a list of extracted data records.

    Args:
        records    : list of dicts (rows)
        conditions : {field: value} exact match filters
        date_field : name of the date column
        date_from  : ISO date string lower bound (inclusive)
        date_to    : ISO date string upper bound (inclusive)
        fields     : list of fields to keep (projection)
    """
    from datetime import datetime

    result = []

    for rec in records:
        rows = _extract_rows(rec)

        for row in rows:
            if not isinstance(row, dict):
                continue

            # ── Exact match conditions ────────────────────────
            if conditions:
                match = all(
                    str(row.get(k, "")).lower() == str(v).lower()
                    for k, v in conditions.items()
                )
                if not match:
                    continue

            # ── Date range ───────────────────────────────────
            if date_field and date_field in row:
                try:
                    row_date = datetime.fromisoformat(str(row[date_field])[:10])
                    if date_from and row_date < datetime.fromisoformat(date_from):
                        continue
                    if date_to and row_date > datetime.fromisoformat(date_to):
                        continue
                except (ValueError, TypeError):
                    pass

            # ── Field projection ─────────────────────────────
            if fields:
                row = {k: v for k, v in row.items() if k in fields}

            result.append(row)

    return result


# ══════════════════════════════════════════════════════════════
# TOOL 6 — aggregate_data
# ══════════════════════════════════════════════════════════════

def aggregate_data(
    records: list[dict],
    group_by:   str | None = None,
    metrics:    list[dict] | None = None,
    top_n:      int | None = None,
    sort_by:    str | None = None,
    sort_order: str = "desc",
    **kwargs,
) -> list[dict]:
    """
    Group and aggregate data records.

    Args:
        records    : list of flat dicts
        group_by   : field name to group on
        metrics    : [{"field": "revenue", "op": "sum|avg|count|min|max"}]
        top_n      : return only top N groups
        sort_by    : field to sort results by
        sort_order : "asc" or "desc"
    """
    from collections import defaultdict

    # Flatten wrapped records
    flat: list[dict] = []
    for rec in records:
        if isinstance(rec, str):
            continue
        flat.extend(_extract_rows(rec))

    if not flat:
        return []  # rien à agréger

    metrics = metrics or []

    # ── No grouping — compute global aggregates ───────────────
    if not group_by:
        agg: dict = {"_all": True}
        for m in metrics:
            field = m.get("field", "")
            op    = m.get("op", "sum")
            vals  = [float(r[field]) for r in flat if field in r and _is_numeric(r.get(field))]
            agg[f"{op}_{field}"] = _apply_op(op, vals)
        return [agg]

    # ── Group by field ────────────────────────────────────────
    groups: dict[Any, list[dict]] = defaultdict(list)
    for row in flat:
        key = row.get(group_by, "__unknown__")
        if isinstance(key, (list, dict)):
            key = str(key)
        groups[key].append(row)

    result = []
    for key, rows in groups.items():
        agg = {group_by: key, "count": len(rows)}
        for m in metrics:
            field = m.get("field", "")
            op    = m.get("op", "sum")
            vals  = [float(r[field]) for r in rows if field in r and _is_numeric(r.get(field))]
            agg[f"{op}_{field}"] = _apply_op(op, vals)
        result.append(agg)

    # ── Sort ──────────────────────────────────────────────────
    if sort_by and result:
        reverse = sort_order.lower() != "asc"
        result.sort(key=lambda x: x.get(sort_by, 0), reverse=reverse)

    # ── Top N ─────────────────────────────────────────────────
    if top_n:
        result = result[:top_n]

    return result


def _apply_op(op: str, vals: list[float]) -> float | int | None:
    if not vals:
        return None
    if op == "sum":   return round(sum(vals), 4)
    if op == "avg":   return round(sum(vals) / len(vals), 4)
    if op == "count": return len(vals)
    if op == "min":   return min(vals)
    if op == "max":   return max(vals)
    return sum(vals)


# ══════════════════════════════════════════════════════════════
# TOOL 7 — normalize_data
# ══════════════════════════════════════════════════════════════

def normalize_data(
    records: list[dict],
    method:       str = "minmax",
    numeric_fields: list[str] | None = None,
    date_format:  str | None = None,
    rename_map:   dict | None = None,
    **kwargs,
) -> list[dict]:
    """
    Normalize and standardize data records.

    Args:
        records        : list of dicts
        method         : "minmax" (0-1 scale) | "zscore" | "none"
        numeric_fields : fields to normalize (auto-detected if None)
        date_format    : parse dates in this format and convert to ISO
        rename_map     : {"old_name": "new_name"} column renames
    """
    # Flatten
    flat: list[dict] = []
    for rec in records:
        if isinstance(rec, str):
            continue
        flat.extend(dict(r) for r in _extract_rows(rec))

    if not flat:
        return records

    # ── Rename columns ────────────────────────────────────────
    if rename_map:
        flat = [
            {rename_map.get(k, k): v for k, v in row.items()}
            for row in flat
        ]

    # ── Detect numeric fields ─────────────────────────────────
    if numeric_fields is None:
        numeric_fields = [
            k for k in flat[0].keys()
            if all(_is_numeric(r.get(k)) for r in flat if k in r)
        ]

    # ── Numeric normalization ─────────────────────────────────
    if method in ("minmax", "zscore") and numeric_fields:
        for field in numeric_fields:
            vals = [float(r[field]) for r in flat if _is_numeric(r.get(field))]
            if not vals:
                continue
            mn, mx = min(vals), max(vals)
            mean_v = sum(vals) / len(vals)
            std_v  = (sum((v - mean_v) ** 2 for v in vals) / len(vals)) ** 0.5 or 1

            for row in flat:
                if _is_numeric(row.get(field)):
                    v = float(row[field])
                    if method == "minmax":
                        row[field] = round((v - mn) / (mx - mn), 6) if mx != mn else 0.0
                    else:
                        row[field] = round((v - mean_v) / std_v, 6)

    # ── Date normalization ────────────────────────────────────
    if date_format:
        from datetime import datetime
        for row in flat:
            for k, v in row.items():
                if isinstance(v, str):
                    try:
                        dt = datetime.strptime(v, date_format)
                        row[k] = dt.isoformat()
                    except ValueError:
                        pass

    return flat


def _is_numeric(val: Any) -> bool:
    try:
        float(val)
        return True
    except (TypeError, ValueError):
        return False


# ══════════════════════════════════════════════════════════════
# TOOL 8 — compare_data
# ══════════════════════════════════════════════════════════════

def compare_data(
    records: list[dict],
    targets:    dict | None = None,
    baseline:   list[dict] | None = None,
    fields:     list[str] | None = None,
    **kwargs,
) -> list[dict]:
    """
    Benchmark records against targets or historical baseline.

    Args:
        records  : current period data (list of dicts)
        targets  : {field: target_value} KPI targets
        baseline : historical records to compare against
        fields   : fields to compare (all numeric if None)
    """
    flat: list[dict] = []
    for rec in records:
        if isinstance(rec, str):
            continue
        flat.extend(dict(r) for r in _extract_rows(rec))

    if not flat:
        return records

    compared = []
    for row in flat:
        enriched = dict(row)

        # ── vs Targets ───────────────────────────────────────
        if targets:
            for field, target in targets.items():
                if _is_numeric(row.get(field)) and _is_numeric(target):
                    actual = float(row[field])
                    tgt    = float(target)
                    delta  = actual - tgt
                    pct    = round((delta / tgt) * 100, 2) if tgt != 0 else None
                    enriched[f"{field}_target"]  = tgt
                    enriched[f"{field}_delta"]   = round(delta, 4)
                    enriched[f"{field}_delta_pct"] = pct
                    enriched[f"{field}_status"]  = (
                        "above_target" if delta > 0
                        else "on_target" if delta == 0
                        else "below_target"
                    )

        # ── vs Baseline average ───────────────────────────────
        if baseline:
            baseline_flat: list[dict] = []
            for brec in baseline:
                baseline_flat.extend(_extract_rows(brec))

            check_fields = fields or [
                k for k in row.keys() if _is_numeric(row.get(k))
            ]
            for field in check_fields:
                b_vals = [
                    float(r[field]) for r in baseline_flat
                    if _is_numeric(r.get(field))
                ]
                if b_vals and _is_numeric(row.get(field)):
                    b_avg  = sum(b_vals) / len(b_vals)
                    actual = float(row[field])
                    delta  = actual - b_avg
                    pct    = round((delta / b_avg) * 100, 2) if b_avg != 0 else None
                    enriched[f"{field}_baseline_avg"]   = round(b_avg, 4)
                    enriched[f"{field}_vs_baseline_pct"] = pct

        compared.append(enriched)

    return compared