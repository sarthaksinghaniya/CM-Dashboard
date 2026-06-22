from core_ai.vector_store import (
    ProductionComplaintVectorStore
)

store = ProductionComplaintVectorStore()


def ingest_complaint(
    complaint_text: str,
    category: str,
    department: str,
    status: str
):
    store.add_complaints(
        [
            {
                "text": complaint_text,
                "complaint": complaint_text,
                "decision": department,
                "outcome": status,
                "labels": [category]
            }
        ]
    )