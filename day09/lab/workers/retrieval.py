"""
workers/retrieval.py — Retrieval Worker
Sprint 2: Implement retrieval từ ChromaDB, trả về chunks + sources.

Input (từ AgentState):
    - task: câu hỏi cần retrieve
    - retrieval_top_k: số chunks cần lấy (default: 3)
    - retrieval_score_threshold: lọc chunk có score thấp (default: 0.0)

Output (vào AgentState):
    - retrieved_chunks: list of {"text", "source", "score", "metadata"}
    - retrieved_sources: list of source filenames (deduplicated)
    - worker_io_log: dict log input/output của worker này (singular, per-run)

Gọi độc lập để test:
    python workers/retrieval.py
"""

import os
import sys
from dotenv import load_dotenv
load_dotenv()

# ─────────────────────────────────────────────
# Worker Contract (xem contracts/worker_contracts.yaml)
# Input:  {"task": str, "top_k": int = 3}
# Output: {"retrieved_chunks": list, "retrieved_sources": list, "error": dict | None}
# ─────────────────────────────────────────────

WORKER_NAME = "retrieval_worker"
DEFAULT_TOP_K = 3
DEFAULT_SCORE_THRESHOLD = 0.0  # 0.0 = không lọc; tăng lên ~0.3 nếu muốn lọc noise


# ─────────────────────────────────────────────
# Embedding
# ─────────────────────────────────────────────

def _get_embedding_fn():
    """
    Trả về embedding function.
    Priority: OpenAI (1536 dims) → SentenceTransformers (384 dims) → random fallback.
    
    QUAN TRỌNG: Phải dùng cùng embedding model với lúc index.
    Collection hiện tại dùng OpenAI text-embedding-3-small (1536 dims).
    """
    # # Option A: OpenAI — PHẢI đặt trước để match collection 1536 dims
    # openai_key = os.getenv("OPENAI_API_KEY")
    # if openai_key:
    #     try:
    #         from openai import OpenAI
    #         client = OpenAI(api_key=openai_key)

    #         def embed(text: str) -> list:
    #             resp = client.embeddings.create(
    #                 input=text,
    #                 model="text-embedding-3-small",  # phải match lúc index
    #             )
    #             return resp.data[0].embedding

    #         return embed
    #     except Exception as e:
    #         print(f"[retrieval_worker] OpenAI embedding failed: {e}", file=sys.stderr)

    # Option B: SentenceTransformers — chỉ dùng nếu re-index lại với 384 dims
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer("all-MiniLM-L6-v2")
        print(
            "⚠️  WARNING: SentenceTransformers (384 dims) — "
            "chỉ dùng nếu collection đã được index với model này.",
            file=sys.stderr,
        )

        def embed(text: str) -> list:
            return model.encode([text])[0].tolist()

        return embed
    except ImportError:
        pass

    # Fallback: random (KHÔNG dùng production)
    import random
    print(
        "⚠️  WARNING: Using random embeddings (test only). "
        "Install openai hoặc sentence-transformers.",
        file=sys.stderr,
    )

    def embed(text: str) -> list:
        return [random.random() for _ in range(384)]

    return embed


# ─────────────────────────────────────────────
# ChromaDB
# ─────────────────────────────────────────────

def _get_collection():
    """
    Kết nối ChromaDB và trả về collection 'day09_docs'.
    Raise RuntimeError nếu collection rỗng để caller xử lý.
    """
    import chromadb

    client = chromadb.PersistentClient(path="./chroma_db")
    collection = client.get_or_create_collection(
        "day09_docs",
        metadata={"hnsw:space": "cosine"},
    )

    # Kiểm tra collection có data chưa
    if collection.count() == 0:
        raise RuntimeError(
            "Collection 'day09_docs' rỗng. "
            "Chạy index script trong README trước khi query."
        )

    return collection


# ─────────────────────────────────────────────
# Core retrieval logic
# ─────────────────────────────────────────────

def retrieve_dense(
    query: str,
    top_k: int = DEFAULT_TOP_K,
    score_threshold: float = DEFAULT_SCORE_THRESHOLD,
) -> list:
    """
    Dense retrieval: embed query → query ChromaDB → trả về top_k chunks.

    Args:
        query:           Câu hỏi cần retrieve
        top_k:           Số kết quả tối đa
        score_threshold: Chỉ giữ chunks có score >= threshold (cosine similarity)

    Returns:
        list of {
            "text":     str,
            "source":   str,
            "score":    float,   # cosine similarity [0, 1]
            "metadata": dict,
        }

    Raises:
        RuntimeError: nếu ChromaDB collection rỗng hoặc không kết nối được
    """
    embed = _get_embedding_fn()
    query_embedding = embed(query)

    collection = _get_collection()  # raises nếu rỗng

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=["documents", "distances", "metadatas"],
    )

    chunks = []
    for doc, dist, meta in zip(
        results["documents"][0],
        results["distances"][0],
        results["metadatas"][0],
    ):
        score = round(1.0 - dist, 4)  # cosine distance → similarity
        if score < score_threshold:
            continue  # lọc noise

        chunks.append({
            "text":     doc,
            "source":   meta.get("source", "unknown"),
            "score":    score,
            "metadata": meta,
        })

    # Sắp xếp theo score giảm dần (ChromaDB thường đã sort, nhưng chắc ăn)
    chunks.sort(key=lambda c: c["score"], reverse=True)
    return chunks


# ─────────────────────────────────────────────
# Worker entry point
# ─────────────────────────────────────────────

def run(state: dict) -> dict:
    """
    Worker entry point — gọi từ graph.py.

    Reads from state:
        task                    (str)   — câu hỏi
        retrieval_top_k         (int)   — số chunks, default 3
        retrieval_score_threshold (float) — ngưỡng lọc, default 0.0

    Writes to state:
        retrieved_chunks        list[dict]
        retrieved_sources       list[str]
        worker_io_log           dict  ← singular, ghi đè mỗi lần run
        worker_io_logs          list  ← append (audit trail)
        workers_called          list
        history                 list
    """
    task            = state.get("task", "")
    top_k           = state.get("retrieval_top_k", DEFAULT_TOP_K)
    score_threshold = state.get("retrieval_score_threshold", DEFAULT_SCORE_THRESHOLD)

    # Khởi tạo các list nếu chưa có
    state.setdefault("workers_called", [])
    state.setdefault("history", [])
    state.setdefault("worker_io_logs", [])

    state["workers_called"].append(WORKER_NAME)

    # Skeleton log — sẽ điền output hoặc error bên dưới
    worker_io = {
        "worker": WORKER_NAME,
        "input":  {"task": task, "top_k": top_k, "score_threshold": score_threshold},
        "output": None,
        "error":  None,
    }

    try:
        chunks  = retrieve_dense(task, top_k=top_k, score_threshold=score_threshold)
        # Deduplicate sources, giữ thứ tự xuất hiện
        seen, sources = set(), []
        for c in chunks:
            if c["source"] not in seen:
                seen.add(c["source"])
                sources.append(c["source"])

        # ── Ghi vào state ──────────────────────────────────────────────
        state["retrieved_chunks"]  = chunks
        state["retrieved_sources"] = sources

        worker_io["output"] = {
            "chunks_count": len(chunks),
            "sources":      sources,
            "top_score":    chunks[0]["score"] if chunks else None,
        }
        state["history"].append(
            f"[{WORKER_NAME}] retrieved {len(chunks)} chunks "
            f"(threshold={score_threshold}) from {sources}"
        )

    except Exception as e:
        error_payload = {"code": "RETRIEVAL_FAILED", "reason": str(e)}
        worker_io["error"] = error_payload

        # Ghi state an toàn — downstream workers không bị crash
        state["retrieved_chunks"]  = []
        state["retrieved_sources"] = []

        state["history"].append(f"[{WORKER_NAME}] ERROR: {e}")
        print(f"[{WORKER_NAME}] ⚠️  {e}", file=sys.stderr)

    # ── Ghi log (cả singular lẫn audit trail) ──────────────────────────
    state["worker_io_log"]  = worker_io          # singular — dễ đọc ngay
    state["worker_io_logs"].append(worker_io)    # list     — audit trail

    return state


# ─────────────────────────────────────────────
# Test độc lập
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 50)
    print("Retrieval Worker — Standalone Test")
    print("=" * 50)

    test_queries = [
        "SLA ticket P1 là bao lâu?",
        "Điều kiện được hoàn tiền là gì?",
        "Ai phê duyệt cấp quyền Level 3?",
    ]

    for query in test_queries:
        print(f"\n▶ Query: {query}")
        result = run({"task": query})

        chunks = result.get("retrieved_chunks", [])
        print(f"  Retrieved : {len(chunks)} chunks")
        for c in chunks[:2]:
            print(f"    [{c['score']:.3f}] {c['source']}: {c['text'][:80]}...")

        log = result.get("worker_io_log", {})
        if log.get("error"):
            print(f"  ❌ Error   : {log['error']}")
        else:
            print(f"  Sources   : {result.get('retrieved_sources', [])}")
            print(f"  Top score : {log['output'].get('top_score')}")

    print("\n✅ retrieval_worker test done.")