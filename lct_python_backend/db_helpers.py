# from db import db
from lct_python_backend.db import db
# import json
# from datetime import datetime
# from typing import Optional, List, Dict, Any

async def insert_conversation_metadata(metadata: dict):
    query = """
    INSERT INTO conversations (id, file_name, no_of_nodes, gcs_path, created_at)
    VALUES (:id, :file_name, :no_of_nodes, :gcs_path, :created_at)
    ON CONFLICT (id) DO UPDATE SET
        file_name = EXCLUDED.file_name,
        no_of_nodes = EXCLUDED.no_of_nodes,
        gcs_path = EXCLUDED.gcs_path,
        created_at = EXCLUDED.created_at
    """
    await db.execute(query, values=metadata)

async def get_all_conversations():
    query = "SELECT * FROM conversations ORDER BY created_at DESC"
    return await db.fetch_all(query)

async def get_conversation_gcs_path(conversation_id: str) -> str:
    query = "SELECT gcs_path FROM conversations WHERE id = :id"
    result = await db.fetch_one(query, values={"id": conversation_id})
    if result:
        return result["gcs_path"]
    return None

# async def save_fact_check_results(conversation_id: str, node_name: str, results_json: str):
#     query = """
#         INSERT INTO fact_checks (conversation_id, node_name, results, created_at)
#         VALUES (:conversation_id, :node_name, :results, :created_at)
#         ON CONFLICT (conversation_id, node_name) 
#         DO UPDATE SET results = :results, created_at = :created_at;
#     """
#     values = {
#         "conversation_id": conversation_id,
#         "node_name": node_name,
#         "results": results_json,
#         "created_at": datetime.utcnow()
#     }
#     await db.execute(query=query, values=values)

# async def get_fact_check_results(conversation_id: str, node_name: str) -> Optional[List[Dict[str, Any]]]:
#     query = """
#         SELECT results FROM fact_checks
#         WHERE conversation_id = :conversation_id AND node_name = :node_name
#         ORDER BY created_at DESC
#         LIMIT 1;
#     """
#     values = {"conversation_id": conversation_id, "node_name": node_name}
    
#     result = await db.fetch_one(query=query, values=values)
    
#     if result and result["results"]:
#         return json.loads(result["results"])
#     return None
