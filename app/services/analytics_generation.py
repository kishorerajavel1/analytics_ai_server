from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from app.config import settings
from pydantic import BaseModel, Field
from typing import Any
import re
import json

from app.prompts.generate_analytics import GENERATE_ANALYTICS_PROMPT


class DatabaseInfo(BaseModel):
    schemas: Any = Field(...,
                         description="Table names with their columns and data types")
    relationships: Any = Field(..., description="Foreign key relationships")
    semantics: Any = Field(...,
                           description="Semantic information about tables/columns")
    db_type: str = Field(..., description="Database type")


class AnalyticsGenerationService:
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=settings.GEMINI_API_KEY,
            temperature=0.5,
            convert_system_message_to_human=True
        )

    def generateDashboardConfig(self, db_info: DatabaseInfo) -> Any:
        chain = GENERATE_ANALYTICS_PROMPT | self.llm
        result = chain.invoke({
            "schemas": db_info.schemas,
            "relationships": db_info.relationships,
            "semantics": db_info.semantics,
            "db_type": db_info.db_type
        })
        clean_json_str = re.sub(
            r"^```json|```$", "", result.content.strip(), flags=re.MULTILINE).strip()
        return json.loads(clean_json_str)
