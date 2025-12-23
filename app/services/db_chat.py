import json
from langchain_core.runnables import RunnableBranch, RunnableLambda, RunnableSerializable
from app.config import settings
from pydantic import SecretStr

from app.managers.mindsdb import MindsDBManager

from typing import Any, cast
from typing_extensions import AsyncIterator, TypedDict

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import StrOutputParser

from app.prompts.generic_reply import GENERIC_REPLY_PROMPT
from app.prompts.message_classifier import MESSAGE_CLASSIFIER_PROMPT
from app.prompts.sql_generator import SQL_GENERATOR_PROMPT
from app.prompts.summary import SUMMARY_PROMPT

import re


class ClassifierInput(TypedDict):
    user_message: str


class GenericReplyInput(TypedDict):
    user_message: str


class ColumnSemantic(TypedDict):
    column_name: str
    semantic_description: str


class TableSemantic(TypedDict):
    table_name: str
    semantic_description: str
    columns: list[ColumnSemantic]


class ChatInput(TypedDict):
    user_message: str
    db_type: str
    tables: dict[str, dict[str, str]]
    relationships: list[dict[str, str]]
    semantics: list[TableSemantic]
    db_name: str


class AnalyticalInput(TypedDict):
    user_message: str
    db_type: str
    tables: dict[str, dict[str, str]]
    relationships: list[dict[str, str]]
    semantics: list[TableSemantic]
    intent: str


class SummaryInput(TypedDict):
    user_message: str
    sql_query: str
    data: str


class DBChatService:
    llm: ChatGoogleGenerativeAI

    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            api_key=SecretStr(settings.GEMINI_API_KEY),
            model="gemini-2.5-flash",
            temperature=0.5,
            convert_system_message_to_human=True
        )
        self.classifier_chain = self._build_classifier()
        self.generic_chain = self._build_generic_reply()
        self.sql_chain = self._build_sql_generator()
        self.summary_chain = self._build_summary()
        self.pipeline = self._build_pipeline()

    def _build_classifier(self) -> RunnableSerializable[ClassifierInput, str]:
        prompt = cast(
            RunnableSerializable[ClassifierInput, str], MESSAGE_CLASSIFIER_PROMPT)
        return prompt | self.llm | StrOutputParser()

    def _build_generic_reply(self) -> RunnableSerializable[GenericReplyInput, str]:
        prompt = cast(
            RunnableSerializable[GenericReplyInput, str], GENERIC_REPLY_PROMPT)
        return prompt | self.llm | StrOutputParser()

    def _build_sql_generator(self) -> RunnableSerializable[ChatInput, str]:
        prompt = cast(
            RunnableSerializable[ChatInput, str], SQL_GENERATOR_PROMPT)
        return prompt | self.llm | StrOutputParser() | RunnableLambda(self._clean_sql)

    def _build_summary(self) -> RunnableSerializable[SummaryInput, str]:
        prompt = cast(
            RunnableSerializable[SummaryInput, str], SUMMARY_PROMPT)
        return prompt | self.llm | StrOutputParser()

    #
    @staticmethod
    def _clean_sql(sql: str) -> str:
        sql = re.sub(r'^```(?:sql)?\s*\n?', '',
                     sql.strip(), flags=re.IGNORECASE)
        sql = re.sub(r'\n?```\s*$', '', sql.strip())
        sql = sql.replace('`', '')

        sql = sql.strip()
        return sql

    def _execute_sql(self, inputs: dict[str, Any]) -> dict[str, Any]:
        sql = inputs["sql"]
        executor = MindsDBManager()
        data = executor.execute_query(
            sql_query=sql, database_name=inputs["db_name"])
        return {
            "sql": sql,
            "data": data,
            "user_message": inputs["user_message"]
        }

    # BUILD PIPELINE

    def _build_pipeline(self):

        def add_intent(x: ChatInput):
            return {
                **x,
                "intent": self.classifier_chain.invoke({"user_message": x["user_message"]})
            }

        with_intent = RunnableLambda(add_intent)

        def handle_generic(x):
            message = self.generic_chain.invoke(
                {"user_message": x["user_message"]})
            return {
                "type": "generic_reply",
                "message": message
            }

        generic_branch = RunnableLambda(handle_generic)

        def handle_analytical(x):
            sql = self.sql_chain.invoke({
                "user_message": x["user_message"],
                "tables": x["tables"],
                "relationships": x["relationships"],
                "semantics": x["semantics"],
                "db_type": x["db_type"],
                "db_name": x["db_name"]
            })

            data = self._execute_sql({
                "sql": sql,
                "user_message": x["user_message"],
                "db_name": x["db_name"]
            })

            summary = self.summary_chain.invoke({
                "user_message": x["user_message"],
                "sql_query": sql,
                "data": data["data"]
            })

            return {
                "type": "data_response",
                "summary": summary,
                "data": data["data"],
                "sql": sql
            }

        analytical_branch = RunnableLambda(handle_analytical)

        router = RunnableBranch(
            (lambda x: cast(AnalyticalInput, x)[
             "intent"] == "generic", generic_branch),
            analytical_branch
        )

        return with_intent | router

    # STREAMING

    async def stream_response(self, payload: ChatInput) -> AsyncIterator[str]:
        try:
            yield self._format_sse("status", {"content": "Classifying query..."})
            intent = await self.classifier_chain.ainvoke({
                "user_message": payload["user_message"]
            })

            yield self._format_sse("intent", {"content": intent})

            if intent == "generic":
                yield self._format_sse("status", {"content": "Generating response..."})

                # Stream the generic response
                generic_response = ""
                async for chunk in self.generic_chain.astream({
                    "user_message": payload["user_message"]
                }):
                    generic_response += chunk
                    yield self._format_sse("generic_chunk", {"content": chunk})

                yield self._format_sse("generic_complete", {"content": generic_response})

            else:
                yield self._format_sse("status", {"content": "Gnerating SQL query..."})

                sql_chunks: list[str] = []

                async for chunk in self.sql_chain.astream({
                    "user_message": payload["user_message"],
                    "tables": payload["tables"],
                    "relationships": payload["relationships"],
                    "semantics": payload["semantics"],
                    "db_type": payload["db_type"],
                    "db_name": payload["db_name"]
                }):
                    sql_chunks.append(chunk)
                    yield self._format_sse("sql_chunk", {"content": chunk})

                sql = "".join(sql_chunks)
                yield self._format_sse("sql_complete", {"content": sql})

                yield self._format_sse("status", {"content": "Executing SQL query..."})
                data = self._execute_sql({
                    "sql": self._clean_sql(sql),
                    "user_message": payload["user_message"],
                    "db_name": payload["db_name"]
                })
                yield self._format_sse("data", {"content": data["data"], "data": data["data"]})

                yield self._format_sse("status", {"content": "Generating summary..."})

                summary_chunks: list[str] = []
                async for chunk in self.summary_chain.astream({
                    "user_message": payload["user_message"],
                    "sql_query": sql,
                    "data": data["data"]
                }):
                    summary_chunks.append(chunk)
                    yield self._format_sse("summary_chunk", {"content": chunk})

                summary = "".join(summary_chunks)
                yield self._format_sse("summary_complete", {"content": summary})

        except Exception as e:
            yield self._format_sse("error", {"content": str(e)})

    #

    @staticmethod
    def _format_sse(event_type: str, data: dict[str, Any]) -> str:
        """Format data as Server-Sent Event."""
        jsonObj = json.dumps({"event": event_type, "data": data})
        return jsonObj + "\n\n"

    def invoke(self, payload: ChatInput) -> dict[str, Any]:
        return self.pipeline.invoke(payload)

    def classify(self, user_message: str) -> str:
        # return self._build_classifier().invoke({"user_message": user_message})
        return self._build_generic_reply().invoke({"user_message": user_message})

    def generateSQL(self, payload: ChatInput) -> str:
        return self._build_sql_generator().invoke(payload)
