from typing import List, Optional
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI

from app.config import settings
from app.prompts.generate_relationships_prompt import GENERATE_RELATIONSHIPS_PROMPT

import json


class Relationship(BaseModel):
    """Model for database table relationship"""
    source_table: str = Field(..., description="Source table name")
    source_column: str = Field(..., description="Source column name")
    target_table: str = Field(..., description="Target table name")
    target_column: str = Field(..., description="Target column name")
    relationship_type: str = Field(
        ...,
        description="Type of relationship: one-to-many, many-to-one, one-to-one"
    )
    description: Optional[str] = Field(
        None, description="Relationship description")


class SchemaRelationships(BaseModel):
    """Model for complete schema relationship analysis"""
    relationships: List[Relationship] = Field(
        ..., description="List of relationships")
    summary: str = Field(..., description="Summary of database structure")


class DBRelationshipsAnalyzer:
    def __init__(self):
        self.model = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            api_key=settings.GEMINI_API_KEY,
            temperature=0,
            convert_system_message_to_human=True
        )
        self.parser = PydanticOutputParser(pydantic_object=SchemaRelationships)
        self.prompt = GENERATE_RELATIONSHIPS_PROMPT

    def analyze_relationships(self, schema):
        chain = self.prompt | self.model | self.parser

        try:
            result = chain.invoke({
                "schema": json.dumps(schema, indent=2),
                "format_instructions": self.parser.get_format_instructions()
            })
            return result
        except Exception as e:
            # Fallback: try without parser if JSON parsing fails
            chain_without_parser = self.prompt | self.model
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
            return SchemaRelationships(**data)
