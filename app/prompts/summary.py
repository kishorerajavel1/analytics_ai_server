from langchain_core.prompts import ChatPromptTemplate

SUMMARY_PROMPT = ChatPromptTemplate.from_template("""
User request:
{user_message}

SQL executed:
{sql_query}

Data:
{data}

Write a breif summary and insights about the response.
It can be detailed if User request is demanding.
""")
