from langchain_core.prompts import ChatPromptTemplate

GENERIC_REPLY_PROMPT = ChatPromptTemplate.from_template("""
User message: {user_message}

Generate a polite and short reply indicating they should ask a data or analytics related question about their database.
""")
