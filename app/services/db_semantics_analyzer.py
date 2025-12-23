from typing import List
from pydantic import BaseModel, Field
from app.config import settings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import PydanticOutputParser

import json

from app.prompts.semantics_generation_prompt import SEMANTICS_GENERATION_PROMPT


class ColumnSemantics(BaseModel):
    """Simplified semantic information for a database column"""
    column_name: str = Field(..., description="Name of the column")
    semantic_description: str = Field(
        ..., description="Concise semantic description of the column")


class TableSemantics(BaseModel):
    """Simplified semantic information for a database table"""
    table_name: str = Field(..., description="Name of the table")
    semantic_description: str = Field(
        ..., description="Concise semantic description of the table")
    columns: List[ColumnSemantics] = Field(
        default_factory=list, description="Semantic information for columns")


class SchemaSemantics(BaseModel):
    """Simplified semantic information for the database schema"""
    tables: List[TableSemantics] = Field(
        ..., description="Simplified semantic information for each table")


class DBSemanticsAnalyzer:
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=settings.GEMINI_API_KEY,
            temperature=0,
            convert_system_message_to_human=True
        )
        self.parser = PydanticOutputParser(pydantic_object=SchemaSemantics)
        self.prompt = SEMANTICS_GENERATION_PROMPT

    def analyze_semantics(self, schema):
        chain = self.prompt | self.llm | self.parser

        try:
            result = chain.invoke({
                "schema": json.dumps(schema, indent=2),
                "format_instructions": self.parser.get_format_instructions()
            })
            return result
        except Exception as e:
            # Fallback: try without parser if JSON parsing fails
            chain_without_parser = self.prompt | self.llm
            response = chain_without_parser.invoke({
                "schema": json.dumps(schema, indent=2),
                "format_instructions": self.parser.get_format_instructions()
            })

            # Try to parse the response manually
            content = response.content
            # Remove markdown code blocks if present
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            data = json.loads(content)

            # Handle both array and object formats
            if isinstance(data, list):
                # If LLM returned an array, wrap it in the expected structure
                return SchemaSemantics(tables=data)
            else:
                # If LLM returned an object, use it directly
                return SchemaSemantics(**data)
