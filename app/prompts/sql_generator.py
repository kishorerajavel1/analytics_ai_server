from langchain_core.prompts import ChatPromptTemplate

SQL_GENERATOR_PROMPT = ChatPromptTemplate.from_template("""
You are an expert in MindsDB SQL generation.

Database type: {db_type}
Tables:
{tables}

Relationships:
{relationships}

Semantics:
{semantics}

User request:
{user_message}

Generate a VALID MindsDB SQL query for the given database type.

FORMATTING REQUIREMENTS:
1. Return ONLY the raw SQL query
2. NO markdown formatting, code fences, or backticks
3. NO ```sql or ``` tags
4. NO explanations or comments
5. Each SQL clause (SELECT, FROM, JOIN, WHERE, GROUP BY, ORDER BY, LIMIT) must be on a NEW LINE
6. Proper indentation with 4 spaces for nested clauses
7. Always add a NEWLINE before keywords: FROM, JOIN, ON, WHERE, GROUP BY, HAVING, ORDER BY, LIMIT
8. Ensure proper spacing around operators (=, <, >, AND, OR)
9. Add a blank line between major query sections for readability 
""")
