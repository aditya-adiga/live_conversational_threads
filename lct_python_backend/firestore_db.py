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


def insert_conversation_metadata_test(metadata: dict) -> None:
    """
    metadata must contain: id, file_name, no_of_nodes, gcs_path, created_at, owner_uid
    """
    doc_ref = db.collection("conversations_test").document(str(metadata["id"]))
    doc_ref.set({
        "file_name"  : metadata["file_name"],
        "no_of_nodes": metadata["no_of_nodes"],
        "gcs_path"   : metadata["gcs_path"],
        "created_at" : metadata["created_at"],
        "owner_uid"  : metadata["owner_uid"],
    })


def get_all_conversations_test(owner_uid: str) -> list[dict]:
    """
    Get all conversations for a specific owner
    """
    docs = (
        db.collection("conversations_test")
          .where("owner_uid", "==", owner_uid)
          .order_by("created_at", direction=firestore.Query.DESCENDING)
          .stream()
    )
    return [{"id": doc.id, **(doc.to_dict() or {})} for doc in docs]


def get_conversation_gcs_path_test(conversation_id: str, owner_uid: str) -> str | None:
    """
    Get conversation GCS path only if the user is the owner or has shared access
    """
    snap = (
        db.collection("conversations_test")
          .document(conversation_id)
          .get()
    )
    if snap.exists:
        data = snap.to_dict() or {}
        # Check if user is owner or in shared_with list
        if data.get("owner_uid") == owner_uid or owner_uid in data.get("shared_with", []):
            return data.get("gcs_path")
    return None


def share_conversation_test(conversation_id: str, owner_uid: str, shared_uids: list[str]) -> bool:
    """
    Share a conversation with specified users by adding their UIDs to shared_with array
    Only the owner can share the conversation
    """
    doc_ref = db.collection("conversations_test").document(conversation_id)
    snap = doc_ref.get()
    
    if not snap.exists:
        return False
        
    data = snap.to_dict() or {}
    if data.get("owner_uid") != owner_uid:
        return False  # Only owner can share
    
    # Get existing shared_with list or create empty list
    current_shared = data.get("shared_with", [])
    
    # Add new UIDs to the list (avoiding duplicates)
    updated_shared = list(set(current_shared + shared_uids))
    
    # Update the document
    doc_ref.update({"shared_with": updated_shared})
    return True


def get_owned_conversations_test(user_uid: str) -> list[dict]:
    """
    Get all conversations owned by a specific user (without sorting)
    """
    docs = (
        db.collection("conversations_test")
          .where("owner_uid", "==", user_uid)
          .stream()
    )
    return [{"id": doc.id, **(doc.to_dict() or {})} for doc in docs]


def get_shared_conversations_test(user_uid: str) -> list[dict]:
    """
    Get all conversations shared with a specific user (without sorting)
    """
    docs = (
        db.collection("conversations_test")
          .where("shared_with", "array_contains", user_uid)
          .stream()
    )
    return [{"id": doc.id, **(doc.to_dict() or {})} for doc in docs]


def get_all_accessible_conversations_test(user_uid: str) -> list[dict]:
    """
    Get all conversations accessible to a user (owned + shared)
    """
    # Get owned and shared conversations using helper functions
    owned_conversations = get_owned_conversations_test(user_uid)
    shared_conversations = get_shared_conversations_test(user_uid)
    
    # Combine and deduplicate
    all_conversations = {}
    
    # Add owned conversations
    for conv in owned_conversations:
        conv["access_type"] = "owner"
        all_conversations[conv["id"]] = conv
    
    # Add shared conversations (avoid duplicates)
    for conv in shared_conversations:
        if conv["id"] not in all_conversations:
            conv["access_type"] = "shared"
            all_conversations[conv["id"]] = conv
    
    # Sort by created_at
    conversations_list = list(all_conversations.values())
    conversations_list.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    
    return conversations_list


def get_conversation_shared_users_test(conversation_id: str, owner_uid: str) -> list[str]:
    """
    Get the list of UIDs that a conversation is shared with
    Only the owner can see this information
    """
    snap = (
        db.collection("conversations_test")
          .document(conversation_id)
          .get()
    )
    
    if not snap.exists:
        return []
        
    data = snap.to_dict() or {}
    if data.get("owner_uid") != owner_uid:
        return []  # Only owner can see shared users
    
    return data.get("shared_with", [])


def remove_user_from_conversation_test(conversation_id: str, owner_uid: str, user_uid_to_remove: str) -> bool:
    """
    Remove a user from the shared_with list of a conversation
    Only the owner can remove users
    """
    doc_ref = db.collection("conversations_test").document(conversation_id)
    snap = doc_ref.get()
    
    if not snap.exists:
        return False
        
    data = snap.to_dict() or {}
    if data.get("owner_uid") != owner_uid:
        return False  # Only owner can remove users
    
    current_shared = data.get("shared_with", [])
    
    if user_uid_to_remove in current_shared:
        updated_shared = [uid for uid in current_shared if uid != user_uid_to_remove]
        doc_ref.update({"shared_with": updated_shared})
        return True
    
    return False  # User was not in the shared list