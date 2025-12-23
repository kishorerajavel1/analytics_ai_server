from langchain_core.prompts import ChatPromptTemplate

MESSAGE_CLASSIFIER_PROMPT = ChatPromptTemplate.from_template("""
Classify the user message into one of:
- generic
- analytical
- data_specific

User message: {user_message}

Return ONLY the label.
""")
