# test_tool_builder.py (à mettre dans app/)
from agent.sub_agents.tool_builder.graph import run_tool_builder

tool_spec = {
    "tool_name": "extract_from_excel_advanced",
    "description": "Extract data from Excel with multiple sheets and apply filters",
    "input_schema": {
        "path": "str",
        "sheet_name": "str",
        "filter_column": "str",
        "filter_value": "str"
    },
    "output_schema": {
        "rows": "list",
        "columns": "list",
        "filtered_count": "int"
    },
    "example_usage": "extract_from_excel_advanced({'path': 'data.xlsx', 'sheet_name': 'Sheet1', 'filter_column': 'status', 'filter_value': 'active'})"
}

result = run_tool_builder(tool_spec)
print(result)