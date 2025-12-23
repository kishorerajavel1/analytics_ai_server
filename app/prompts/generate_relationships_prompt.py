from langchain_core.prompts import ChatPromptTemplate

GENERATE_RELATIONSHIPS_PROMPT = ChatPromptTemplate.from_template("""
You are a database architect expert. Analyze the following database schema and identify all relationships between tables.

Database Schema:
{schema}

Instructions:
1. Identify foreign key relationships (columns ending with _id typically reference the 'id' column of another table)
2. Determine the relationship type:
   - "one-to-many": One record in source can relate to many in target
   - "many-to-one": Many records in source relate to one in target
   - "one-to-one": One record in source relates to one in target
3. Provide a brief description of each relationship
4. Create a summary of the overall database structure

{format_instructions}

Analyze carefully and provide comprehensive relationship mapping. Return ONLY valid JSON, no additional text.
""")
