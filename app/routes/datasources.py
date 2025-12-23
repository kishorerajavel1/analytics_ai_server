from fastapi import APIRouter, HTTPException, Request
from loguru import logger

from app.constants.dbTables import USER_DATASOURCE_CONNECTIONS
from app.managers.db import DBManager
from app.managers.mindsdb import MindsDBManager
from app.schemas.datasourceSchemas import DataSourceCreateSchema, GetDataSourceSchemas
from app.services.db_relationships_analyzer import DBRelationshipsAnalyzer

from app.services.mindsdb_service import MindsDBService

from app.services.db_semantics_analyzer import DBSemanticsAnalyzer
from pydantic import BaseModel

router = APIRouter()


@router.post("/create")
async def create_datasource(request: Request, payload: DataSourceCreateSchema):
    try:
        minds_db: MindsDBManager = request.app.state.minds_db_manager
        db: DBManager = request.app.state.db_manager

        logger.info(f"Creating datasource for user {request.state.user}")
        user_id = request.state.user_id

        result = minds_db.create_datasource(name=payload.metadata.name,
                                            engine=payload.metadata.engine,
                                            connection_data=payload.connection_data)

        db_result = db.client.table(USER_DATASOURCE_CONNECTIONS).insert(
            payload.metadata.model_dump() | {"user_id": user_id}).execute()

        return {
            "status": "success",
            "message": "Datasource created successfully",
            "data": db_result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{id}")
async def delete_datasource(request: Request, id: str):
    try:
        minds_db: MindsDBManager = request.app.state.minds_db_manager
        db: DBManager = request.app.state.db_manager

        resp = db.client.table(USER_DATASOURCE_CONNECTIONS).delete().eq(
            "id", id).execute()

        deleted_row = resp.data[0]
        if not deleted_row:
            return {
                "status": "success",
                "message": "Datasource deleted successfully"
            }
        else:
            minds_db.delete_datasource(deleted_row["name"])
            return {
                "status": "success",
                "message": "Datasource deleted successfully"
            }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/")
async def get_user_datasources(request: Request):
    try:
        db: DBManager = request.app.state.db_manager
        return db.client.table(USER_DATASOURCE_CONNECTIONS).select("id, name, label, engine, description, integration_id, created_at, master_datasource_connections(label, icon)").execute()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/schemas/{name}")
async def get_user_datasource_schemas(request: Request, name: str):
    try:
        minds_db: MindsDBManager = request.app.state.minds_db_manager
        return minds_db.get_datasources_tables_and_schemas_by_names([name])
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/schemas")
async def get_datasource_schemas(request: Request, payload: GetDataSourceSchemas):
    try:
        minds_db: MindsDBManager = request.app.state.minds_db_manager
        db: DBManager = request.app.state.db_manager

        name = payload.name
        response = minds_db.get_datasources_tables_and_schemas_by_names([name])
        db.client.table(USER_DATASOURCE_CONNECTIONS).update(
            {"schemas": response[name]}).eq("name", name).execute()

        return {
            "status": "success",
            "message": "Datasource schemas updated successfully",
            "data": response[name]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/generate-relationships")
async def generate_relationships(request: Request, payload: GetDataSourceSchemas):
    try:
        # minds_db: MindsDBManager = request.app.state.minds_db_manager
        name = payload.name
        db: DBManager = request.app.state.db_manager
        connection = db.client.table(USER_DATASOURCE_CONNECTIONS).select(
            "schemas").eq("name", name).execute()

        if (connection is None):
            raise HTTPException(status_code=400, detail="Datasource not found")

        schema = connection.data[0].get("schemas", None)

        if (schema is None):
            raise HTTPException(
                status_code=400, detail="Datasource schemas not found")

        analyzer = DBRelationshipsAnalyzer()
        relationships = analyzer.analyze_relationships(schema)

        if (relationships is None):
            raise HTTPException(
                status_code=400, detail="Relationships not found")
        elif (relationships):
            db_relationships = [r.model_dump()
                                for r in relationships.relationships]
            db.client.table(USER_DATASOURCE_CONNECTIONS).update(
                {"relationships": db_relationships}).eq("name", name).execute()

        return {
            "status": "success",
            "message": "Relationships generated successfully",
            "data": db_relationships,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/generate-semantics")
async def generate_semantics(request: Request, payload: GetDataSourceSchemas):
    try:
        # minds_db: MindsDBManager = request.app.state.minds_db_manager
        name = payload.name
        db: DBManager = request.app.state.db_manager

        connection = db.client.table(USER_DATASOURCE_CONNECTIONS).select(
            "schemas").eq("name", name).execute()

        if (connection is None):
            raise HTTPException(status_code=400, detail="Datasource not found")

        schema = connection.data[0].get("schemas", None)

        if (schema is None):
            raise HTTPException(
                status_code=400, detail="Datasource schemas not found")

        analyzer = DBSemanticsAnalyzer()
        semantics = analyzer.analyze_semantics(schema)

        if (semantics is None):
            raise HTTPException(
                status_code=400, detail="Semantics not found")
        elif (semantics):
            db_semantics = [r.model_dump()
                            for r in semantics.tables]
            db.client.table(USER_DATASOURCE_CONNECTIONS).update(
                {"semantics": db_semantics}).eq("name", name).execute()

        return {
            "status": "success",
            "message": "Semantics generated successfully",
            "data": db_semantics,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class QueryRequest(BaseModel):
    name: str
    query: str


@router.post("/query")
async def query(request: Request, payload: QueryRequest):
    try:
        minds_db: MindsDBManager = request.app.state.minds_db_manager
        service = MindsDBService(minds_db)

        result = service.query(payload.name, payload.query)

        return {
            "status": "success",
            "message": "Query executed successfully",
            "data": result
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
