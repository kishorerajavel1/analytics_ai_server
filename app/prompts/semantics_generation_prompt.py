from langchain_core.prompts import ChatPromptTemplate

SEMANTICS_GENERATION_PROMPT = ChatPromptTemplate.from_template("""
You are a database documentation expert. Generate concise semantic descriptions for the following database schema.

Database Schema:
{schema}

Instructions:
1. For each table, provide a single concise semantic_description (one sentence, around 15-25 words)
2. The description should explain the table's purpose and business value
3. For each column in the table, provide a concise semantic_description (one sentence, around 10-15 words)
4. Focus on business meaning, not technical details

Return the data in this EXACT JSON format:
{{
  "tables": [
    {{
      "table_name": "table1",
      "semantic_description": "Brief description of table purpose and business value",
      "columns": [
        {{
          "column_name": "column1",
          "semantic_description": "Brief description of column purpose"
        }},
        {{
          "column_name": "column2",
          "semantic_description": "Brief description of column purpose"
        }}
      ]
    }},
    {{
      "table_name": "table2",
      "semantic_description": "Brief description of table purpose and business value",
      "columns": [
        {{
          "column_name": "column1",
          "semantic_description": "Brief description of column purpose"
        }}
      ]
    }}
  ]
}}

Generate descriptions for ALL tables and ALL columns in the schema.
Return ONLY the JSON object with a "tables" array, no additional text or markdown.
""")
