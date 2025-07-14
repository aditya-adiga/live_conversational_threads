from google.cloud import firestore

# synchronous
db = firestore.Client(project="live-conversational-threads",
                      database="lct-db") 


def insert_conversation_metadata(metadata: dict) -> None:
    """
    metadata must contain: id, file_name, no_of_nodes, gcs_path, created_at
    """
    doc_ref = db.collection("conversations").document(str(metadata["id"]))
    # .set() overwrites the doc if it already exists → behaves like
    # “INSERT … ON CONFLICT(id) DO UPDATE …” in Postgres
    doc_ref.set({
        "file_name"  : metadata["file_name"],
        "no_of_nodes": metadata["no_of_nodes"],
        "gcs_path"   : metadata["gcs_path"],
        "created_at" : metadata["created_at"],
    })


def get_all_conversations() -> list[dict]:
    docs = (
        db.collection("conversations")
          .order_by("created_at", direction=firestore.Query.DESCENDING)
          .stream()                                  # blocking iterator
    )
    return [{"id": doc.id, **(doc.to_dict() or {})} for doc in docs]


def get_conversation_gcs_path(conversation_id: str) -> str | None:
    snap = (
        db.collection("conversations")
          .document(conversation_id)
          .get()
    )
    if snap.exists:
        return (snap.to_dict() or {}).get("gcs_path")
    return None