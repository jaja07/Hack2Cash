"""
ARIA — Extraction Tools
Supports: file (PDF, CSV, Excel, JSON, TXT, MD), database (SQLite/SQL), API (REST), web (HTML scrape).
"""

from __future__ import annotations
import json
import csv
import io
import os
import sqlite3
from typing import Any

import requests


# ══════════════════════════════════════════════════════════════
# TOOL 1 — extract_from_file
# ══════════════════════════════════════════════════════════════

def extract_from_file(source: dict) -> dict:
    """
    Extract content from a local file.

    Supported formats: pdf, csv, excel (xlsx/xls), json, txt, md, html
    """
    path        = source.get("path_or_url", "")
    data_format = source.get("data_format", "").lower()

    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")

    # ── Auto-detect format from extension ────────────────────
    if not data_format:
        ext = os.path.splitext(path)[1].lower().lstrip(".")
        data_format = ext

    # ── PDF ──────────────────────────────────────────────────
    if data_format == "pdf":
        try:
            import pdfplumber
            pages_text = []
            with pdfplumber.open(path) as pdf:
                for i, page in enumerate(pdf.pages):
                    text = page.extract_text() or ""
                    tables = page.extract_tables() or []
                    pages_text.append({
                        "page": i + 1,
                        "text": text.strip(),
                        "tables": tables,
                    })
            return {"format": "pdf", "path": path, "pages": pages_text,
                    "page_count": len(pages_text)}
        except ImportError:
            raise ImportError("pdfplumber is required: pip install pdfplumber")

    # ── CSV ──────────────────────────────────────────────────
    elif data_format == "csv":
        try:
            import pandas as pd
            df = pd.read_csv(path)
            return {
                "format":   "csv",
                "path":     path,
                "columns":  df.columns.tolist(),
                "rows":     df.to_dict(orient="records"),
                "shape":    {"rows": len(df), "cols": len(df.columns)},
                "dtypes":   {col: str(dtype) for col, dtype in df.dtypes.items()},
                "summary":  df.describe(include="all").fillna("").to_dict(),
            }
        except ImportError:
            raise ImportError("pandas is required: pip install pandas")

    # ── Excel ─────────────────────────────────────────────────
    elif data_format in ("xlsx", "xls", "excel"):
        try:
            import pandas as pd
            xl = pd.ExcelFile(path)
            sheets = {}
            for sheet in xl.sheet_names:
                df = xl.parse(sheet)
                sheets[sheet] = {
                    "columns": df.columns.tolist(),
                    "rows":    df.to_dict(orient="records"),
                    "shape":   {"rows": len(df), "cols": len(df.columns)},
                    "summary": df.describe(include="all").fillna("").to_dict(),
                }
            return {"format": "excel", "path": path, "sheets": sheets,
                    "sheet_names": xl.sheet_names}
        except ImportError:
            raise ImportError("pandas + openpyxl required: pip install pandas openpyxl")

    # ── JSON ─────────────────────────────────────────────────
    elif data_format == "json":
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {"format": "json", "path": path, "data": data,
                "keys": list(data.keys()) if isinstance(data, dict) else None,
                "count": len(data) if isinstance(data, list) else 1}

    # ── TXT / MD / HTML ──────────────────────────────────────
    elif data_format in ("txt", "md", "markdown", "html", "htm"):
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        return {"format": data_format, "path": path, "content": content,
                "char_count": len(content), "line_count": content.count("\n") + 1}

    else:
        # Fallback: read as plain text
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        return {"format": "unknown", "path": path, "content": content}


# ══════════════════════════════════════════════════════════════
# TOOL 2 — extract_from_database
# ══════════════════════════════════════════════════════════════

def extract_from_database(source: dict) -> dict:
    """
    Extract data from a database via a SQL query.

    source dict keys:
      - path_or_url : SQLite file path  OR  SQLAlchemy connection string
      - metadata.query : SQL SELECT query to run
      - metadata.table : fallback — SELECT * FROM table (optional)
    """
    connection_str = source.get("path_or_url", "")
    meta           = source.get("metadata", {})
    query          = meta.get("query", "")
    table          = meta.get("table", "")

    if not query and table:
        query = f"SELECT * FROM {table}"
    if not query:
        raise ValueError("No SQL query or table provided in metadata")

    # ── SQLite (file path) ───────────────────────────────────
    if connection_str.endswith(".db") or connection_str.endswith(".sqlite"):
        conn = sqlite3.connect(connection_str)
        conn.row_factory = sqlite3.Row
        cursor = conn.execute(query)
        rows = [dict(row) for row in cursor.fetchall()]
        columns = [d[0] for d in cursor.description] if cursor.description else []
        conn.close()
        return {"format": "sqlite", "query": query,
                "columns": columns, "rows": rows, "count": len(rows)}

    # ── Generic SQL via SQLAlchemy ────────────────────────────
    try:
        from sqlalchemy import create_engine, text
        engine = create_engine(connection_str)
        with engine.connect() as conn:
            result = conn.execute(text(query))
            rows   = [dict(row._mapping) for row in result.fetchall()]
            columns = list(result.keys())
        return {"format": "sql", "query": query,
                "columns": columns, "rows": rows, "count": len(rows)}
    except ImportError:
        raise ImportError("sqlalchemy required for non-SQLite databases: pip install sqlalchemy")


# ══════════════════════════════════════════════════════════════
# TOOL 3 — extract_from_api
# ══════════════════════════════════════════════════════════════

def extract_from_api(source: dict) -> dict:
    """
    Fetch data from a REST or GraphQL API endpoint.

    source dict keys:
      - path_or_url : full endpoint URL
      - metadata.method   : HTTP method (GET/POST), default GET
      - metadata.headers  : dict of request headers
      - metadata.params   : dict of query parameters
      - metadata.body     : dict payload for POST requests
      - metadata.auth     : {"type": "bearer", "token": "..."} | {"type": "basic", "user": "", "pass": ""}
    """
    url    = source.get("path_or_url", "")
    meta   = source.get("metadata", {})
    method = meta.get("method", "GET").upper()
    headers= meta.get("headers", {})
    params = meta.get("params", {})
    body   = meta.get("body", None)
    auth_cfg= meta.get("auth", {})

    # ── Auth ─────────────────────────────────────────────────
    auth = None
    if auth_cfg.get("type") == "bearer":
        headers["Authorization"] = f"Bearer {auth_cfg.get('token', '')}"
    elif auth_cfg.get("type") == "basic":
        auth = (auth_cfg.get("user", ""), auth_cfg.get("pass", ""))

    response = requests.request(
        method, url, headers=headers, params=params,
        json=body if body else None, auth=auth, timeout=30
    )
    response.raise_for_status()

    content_type = response.headers.get("Content-Type", "")
    if "application/json" in content_type:
        data = response.json()
    else:
        data = response.text

    return {
        "format":       "api",
        "url":          url,
        "method":       method,
        "status_code":  response.status_code,
        "data":         data,
        "content_type": content_type,
    }


# ══════════════════════════════════════════════════════════════
# TOOL 4 — extract_from_web
# ══════════════════════════════════════════════════════════════

def extract_from_web(source: dict) -> dict:
    """
    Scrape structured or unstructured content from a public web page.

    source dict keys:
      - path_or_url : page URL
      - metadata.selectors : list of CSS selectors to target (optional)
      - metadata.extract_tables : bool, extract HTML tables (default True)
    """
    url             = source.get("path_or_url", "")
    meta            = source.get("metadata", {})
    selectors       = meta.get("selectors", [])
    extract_tables  = meta.get("extract_tables", True)

    try:
        from bs4 import BeautifulSoup
    except ImportError:
        raise ImportError("beautifulsoup4 required: pip install beautifulsoup4 lxml")

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 Chrome/120.0 Safari/537.36"
        )
    }
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "lxml")

    result: dict[str, Any] = {
        "format": "web",
        "url":    url,
        "title":  soup.title.string.strip() if soup.title else "",
        "text":   soup.get_text(separator="\n", strip=True)[:10000],
    }

    # ── Targeted selectors ───────────────────────────────────
    if selectors:
        selected = {}
        for sel in selectors:
            elements = soup.select(sel)
            selected[sel] = [el.get_text(strip=True) for el in elements]
        result["selected"] = selected

    # ── Tables ───────────────────────────────────────────────
    if extract_tables:
        tables = []
        for tbl in soup.find_all("table"):
            rows = []
            for tr in tbl.find_all("tr"):
                cells = [td.get_text(strip=True) for td in tr.find_all(["td", "th"])]
                if cells:
                    rows.append(cells)
            if rows:
                tables.append(rows)
        result["tables"] = tables

    return result
