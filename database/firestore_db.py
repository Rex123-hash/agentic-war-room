import os
from typing import Any, Dict, List, Optional

from google.cloud import firestore
from dotenv import load_dotenv

load_dotenv()

PROJECT_ID = os.getenv("FIRESTORE_PROJECT_ID") or os.getenv("GOOGLE_CLOUD_PROJECT")
DATABASE_ID = os.getenv("FIRESTORE_DATABASE_ID", "(default)")
USE_FIRESTORE = os.getenv("USE_FIRESTORE", "false").lower() == "true"

_client: Optional[firestore.Client] = None


def is_firestore_enabled() -> bool:
    return USE_FIRESTORE and bool(PROJECT_ID)


def get_firestore_client() -> firestore.Client:
    global _client

    if _client is None:
        if not PROJECT_ID:
            raise ValueError("FIRESTORE_PROJECT_ID or GOOGLE_CLOUD_PROJECT is not set.")

        _client = firestore.Client(
            project=PROJECT_ID,
            database=DATABASE_ID,
        )

    return _client


def upsert_document(collection_name: str, doc_id: str, data: Dict[str, Any]) -> None:
    client = get_firestore_client()
    client.collection(collection_name).document(doc_id).set(data, merge=True)


def add_document(collection_name: str, data: Dict[str, Any]) -> str:
    client = get_firestore_client()
    doc_ref = client.collection(collection_name).document()
    doc_ref.set(data)
    return doc_ref.id


def get_document(collection_name: str, doc_id: str) -> Optional[Dict[str, Any]]:
    client = get_firestore_client()
    doc = client.collection(collection_name).document(doc_id).get()
    if doc.exists:
        result = doc.to_dict()
        result["id"] = doc.id
        return result
    return None


def list_documents(collection_name: str, order_by: Optional[str] = None) -> List[Dict[str, Any]]:
    client = get_firestore_client()
    query = client.collection(collection_name)

    if order_by:
        query = query.order_by(order_by)

    docs = query.stream()
    results = []

    for doc in docs:
        item = doc.to_dict()
        item["id"] = doc.id
        results.append(item)

    return results


def delete_document(collection_name: str, doc_id: str) -> None:
    client = get_firestore_client()
    client.collection(collection_name).document(doc_id).delete()