from langchain_core.prompts import ChatPromptTemplate

GENERATE_ANALYTICS_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a dashboard planner and analytics configuration generator. Given a database information, plan and generate multiple dashboard panels and analytics configuration.

Database Schema:
{schemas}

Relationships:
{relationships}

Semantic Information:
{semantics}

Database Type:
{db_type}

Panel Format:
{{
    "title": "string",
    "description": "string",
    "active": true | false,
    "grid_pos": {{
        "x": number,
        "y": number,
        "w": number,
        "h": number
    }},
    "options": {{
        "key": "value"
    }} (optional),
    "dataSource": {{
        "type": "string",
        "data": any
    }} (optional),
    "config": {{
        "id": "string",
        "type": "bar" | "line" | "area" | "pie" | "scatter" | "radar" | "composed" | "table" | "kpi" | "metric",
        "title": "string",
        "subtitle": "string (optional)",
        "sql_query": "SELECT ...",
        "x_axis": "string", 
        "y_axis": ["string"],
        "config": {{
            "colors": ["string"] (optional),
            "stacked": true | false (optional),
            "showGrid": true | false (optional),
            "showLegend": true | false (optional),
            "showLabels": true | false (optional),
            "orientation": "horizontal" | "vertical" (optional),
            "curve": "monotone" | "linear" | "step" (optional),
            "fillOpacity": number (0–1, optional),
            "strokeWidth": number (optional),
            "innerRadius": number (optional),
            "outerRadius": number (optional),
            "startAngle": number (optional),
            "endAngle": number (optional),
            "labelLine": true | false (optional),
            "animationDuration": number (milliseconds, optional),
            "gradient": true | false (optional)
        }}
    }}
}}

Ensure:
- Output is **valid JSON** only (no markdown, comments, or explanations).
- Include all required fields.
- Omit optional fields if not relevant.

Important:
- Generate a VALID MindsDB SQL query for the given Database Type : {db_type}.
- The x_axis and y_axis fields should be valid column names from the database schema.
- When generating sql query, don't use specific values in filter conditions for columns of type 'varchar' and 'text'. e.g. don't use 'WHERE name = "John"' in sql query.

Your task:
1. Understand the database information and generate multiple dashboard panels and analytics configuration based on the panel format.
2. Generate ONLY the dashboard configuration, no explanations
3. Determine the best chart types for the data
4. Create a well-organized layout
5. The grid position should be created based on the following total cols: 32.
6. For 'kpi' or 'metric' panels, the height (h) MUST be exactly 4.  
7. For all other panel types, the maximum height (h) MUST be 8.
8. For 'line', 'area', 'bar', 'scatter', 'table' and 'composed' panel types, the minimum width (w) MUST be exactly 16.
9. For 'pie' and 'radar' panel types, the minimum width (w) MUST be exactly 8.
10. For 'kpi' and 'metric', have MAXIMUM of 4 panels combined.
11. For others, have MAXIMUM of 5 panels in total. 
12. Generate a valid SQL query for each panel that fetches the data required for the chart configuration.
13. Multiple panels should be generated and should be returned as a list of panels.
14. Always include "area", "table" and "bar" charts.

"""),
    ("user", "Generate a dashboard configuration for the given database information.")
])
