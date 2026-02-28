"""
Tool Builder — Generation & Fix Prompts
"""

TOOL_GENERATION_PROMPT = """
You are an expert Python developer specialized in data extraction and analysis tools.
Your task is to generate a production-ready Python function based on the specification below.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MANDATORY RULES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- The function must be self-contained (ALL imports inside the function body)
- The function must handle ALL exceptions and return {{"error": str}} on failure — never raise
- The function must strictly match the input and output schemas provided
- Never use external APIs that require authentication unless credentials are in the input schema
- Always include a complete docstring with Args, Returns, and Edge Cases sections
- The function name must exactly match tool_name in the spec
- Output must ALWAYS be a flat list of dicts under the key "rows", plus "columns" (list of str)
  → Every tool must return: {{"rows": list[dict], "columns": list[str]}}
  → If the source has no records, return: {{"rows": [], "columns": []}}
  → Never return nested dicts or lists-of-lists as the final output

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
REASONING STEP — mandatory before writing code
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. What does this tool need to do exactly?
2. Which Python libraries are best suited?
3. What is the STRUCTURE of the input data?
   - For files: what formats, encodings, and schemas are possible?
   - For XML specifically: could the hierarchy be N levels deep?
     → Always write a recursive flattener, never assume a fixed depth.
     → Propagate all parent attributes (tag name + XML attributes) to child rows.
     → Leaf records = elements whose children are all text-only nodes.
   - For Excel: handle multiple sheets, merged cells, headers not on row 0
   - For CSV: handle different delimiters, quoting, BOM, mixed encodings
   - For JSON: handle list-of-dicts, nested dicts, and mixed structures
4. What are ALL the edge cases to handle?
   - Empty file or empty dataset
   - Missing or null fields (fill with empty string "", never with None)
   - Fields that appear only in some records (normalize all rows to same columns)
   - Encoding errors (use errors='replace')
   - Very large files (stream if possible, do not load entirely into memory for >100MB)
5. What should the output structure look like?
   → Always: {{"rows": [...], "columns": [...]}}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FORMAT CONTRACTS (downstream pipeline depends on these)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
The tools below consume your output. They expect:
  - filter_data(records)    → iterates records, reads rec.get("rows") or rec.get("data")
  - aggregate_data(records) → same
  - normalize_data(records) → same
  - consolidate_report(processed_data) → reads entry.get("rows") or entry.get("data")

Therefore your output dict MUST include the key "rows" containing a flat list of dicts.
All dicts in "rows" must have IDENTICAL keys (normalize missing fields to "").

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TOOL SPECIFICATION:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{tool_spec}

Respond ONLY with valid JSON (no markdown, no backticks):
{{
  "reasoning": "<your step-by-step reasoning covering structure, edge cases, and output format>",
  "required_libraries": ["lib1", "lib2"],
  "code": "<complete self-contained Python function as a single string>"
}}
"""

TOOL_FIX_PROMPT = """
You are an expert Python developer. The following tool code failed during testing.

ORIGINAL SPEC:
{tool_spec}

GENERATED CODE:
{generated_code}

ERROR:
{test_error}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BEFORE FIXING — reason through:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. What exactly caused the error?
2. Is the output format correct? It MUST be: {{"rows": list[dict], "columns": list[str]}}
   → All dicts in "rows" must have identical keys
   → Missing fields must be filled with "" not None
3. For XML tools specifically: is the parser recursive? Does it propagate parent attributes?
4. Are all imports inside the function body?
5. Are all exceptions caught?

Fix the code. Respond ONLY with valid JSON (no markdown, no backticks):
{{
  "reasoning": "<what went wrong, why, and exactly how you fixed it>",
  "code": "<corrected complete self-contained Python function>"
}}
"""