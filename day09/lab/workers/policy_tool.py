"""
workers/policy_tool.py — Policy & Tool Worker
Sprint 2+3: Kiểm tra policy dựa vào context, gọi MCP tools khi cần.

Input (từ AgentState):
    - task: câu hỏi
    - retrieved_chunks: context từ retrieval_worker
    - needs_tool: True nếu supervisor quyết định cần tool call

Output (vào AgentState):
    - policy_result: {"policy_applies", "policy_name", "exceptions_found", "source", "rule"}
    - mcp_tools_used: list of tool calls đã thực hiện
    - worker_io_log: log

Gọi độc lập để test:
    python workers/policy_tool.py
"""

import os
import json
from dotenv import load_dotenv
load_dotenv(override=True)

WORKER_NAME = "policy_tool_worker"


def _normalize_policy_result(raw: dict, sources: list[str]) -> dict:
    """Chuẩn hóa output policy_result theo contract, kể cả khi LLM trả thiếu field."""
    raw = raw or {}

    exceptions = raw.get("exceptions_found", [])
    if not isinstance(exceptions, list):
        exceptions = []

    applies = raw.get("policy_applies")
    if not isinstance(applies, bool):
        applies = len(exceptions) == 0

    normalized_sources = raw.get("source", sources)
    if isinstance(normalized_sources, str):
        normalized_sources = [normalized_sources]
    if not isinstance(normalized_sources, list):
        normalized_sources = sources

    return {
        "policy_applies": applies,
        "policy_name": raw.get("policy_name", "refund_policy_v4"),
        "exceptions_found": exceptions,
        "source": normalized_sources,
        "policy_version_note": raw.get("policy_version_note", ""),
        "explanation": raw.get(
            "explanation",
            "Không phát hiện ngoại lệ chính sách trong context hiện có."
            if applies else
            "Phát hiện ngoại lệ chính sách, yêu cầu hoàn tiền không được áp dụng.",
        ),
    }


# ─────────────────────────────────────────────
# MCP Client — Sprint 3: Thay bằng real MCP call
# ─────────────────────────────────────────────

def _call_mcp_tool(tool_name: str, tool_input: dict) -> dict:
    """
    Gọi MCP tool.

    Sprint 3 TODO: Implement bằng cách import mcp_server hoặc gọi HTTP.

    Hiện tại: Import trực tiếp từ mcp_server.py (trong-process mock).
    """
    try:
        # Standard mock MCP call envelope from mcp_server.py
        from mcp_server import call_tool
        return call_tool(tool_name, tool_input)
    except Exception as e:
        from datetime import datetime
        return {
            "tool": tool_name,
            "input": tool_input,
            "output": None,
            "error": {"code": "MCP_CALL_FAILED", "reason": str(e)},
            "timestamp": datetime.now().isoformat(),
        }


# ─────────────────────────────────────────────
# Policy Analysis Logic
# ─────────────────────────────────────────────

def analyze_policy(task: str, chunks: list) -> dict:
    """
    Phân tích policy dựa trên context chunks bằng OpenAI LLM.
    """
    openai_key = os.getenv("OPENAI_API_KEY")

    # Chuẩn bị dữ liệu context từ các chunks
    context_text = "\n".join([
        f"- Nguồn {c.get('source', 'unknown')}: {c.get('text', '')}" 
        for c in chunks
    ])
    
    # Danh sách các nguồn tài liệu để trả về trong output
    sources = list({c.get("source", "unknown") for c in chunks if c})

    # System Prompt định nghĩa luật chơi cho LLM
    system_prompt = """
    Bạn là một Policy Analyst chuyên nghiệp. Nhiệm vụ của bạn là kiểm tra yêu cầu hoàn tiền của khách hàng dựa trên tài liệu (Context).
    
    CÁC QUY TẮC CẦN KIỂM TRA (Exceptions):
    1. Flash Sale: Đơn hàng Flash Sale không được hoàn tiền (Điều 3, V4).
    2. Digital Product: License key, subscription, sản phẩm kỹ thuật số không được hoàn tiền.
    3. Activated: Sản phẩm đã kích hoạt hoặc sử dụng không được hoàn tiền.
    4. Date Check: Nếu đơn hàng đặt trước ngày 01/02/2026, áp dụng chính sách V3 (Lưu ý: hiện tại không có docs cho V3, hãy đánh dấu lại).

    YÊU CẦU ĐẦU RA:
    Trả về định dạng JSON với các trường:
    - policy_applies (bool): True nếu có thể hoàn tiền, False nếu vi phạm exception.
    - policy_name (string): "refund_policy_v4" hoặc "refund_policy_v3".
    - exceptions_found (list): Danh sách các vi phạm tìm thấy. Mỗi phần tử gồm {type, rule, source}.
    - policy_version_note (string): Ghi chú về phiên bản chính sách (đặc biệt là nếu trước 01/02/2026).
    - explanation (string): Giải thích ngắn gọn lý do.
    """

    user_content = f"""
    TASK: {task}
    ---
    CONTEXT:
    {context_text}
    """

    if openai_key:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=openai_key)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                response_format={"type": "json_object"},
                temperature=0,
            )
            analysis = json.loads(response.choices[0].message.content)
            analysis["source"] = sources
            return _normalize_policy_result(analysis, sources)
        except Exception as e:
            print(f"Error in analyze_policy (LLM): {e}")

    # Rule-based fallback để worker chạy độc lập ngay cả khi thiếu API key
    lower_task = task.lower()
    combined_text = "\n".join((c.get("text", "") or "") for c in chunks).lower()
    haystack = f"{lower_task}\n{combined_text}"

    exceptions = []
    if "flash sale" in haystack:
        exceptions.append({
            "type": "flash_sale_exception",
            "rule": "Đơn hàng Flash Sale không được hoàn tiền.",
            "source": "policy_refund_v4.txt",
        })
    if any(k in haystack for k in ["digital", "license key", "subscription"]):
        exceptions.append({
            "type": "digital_product_exception",
            "rule": "Sản phẩm kỹ thuật số (license key/subscription) không được hoàn tiền.",
            "source": "policy_refund_v4.txt",
        })
    if any(k in haystack for k in ["đã kích hoạt", "activated", "used"]):
        exceptions.append({
            "type": "activated_product_exception",
            "rule": "Sản phẩm đã kích hoạt/đã sử dụng không được hoàn tiền.",
            "source": "policy_refund_v4.txt",
        })

    policy_name = "refund_policy_v4"
    policy_version_note = "Áp dụng mặc định chính sách v4 theo tài liệu hiện có."
    if "31/01/2026" in haystack or "trước 01/02/2026" in haystack:
        policy_name = "refund_policy_v3"
        policy_version_note = "Có tín hiệu giao dịch trước 01/02/2026, cần tra cứu thêm policy v3."

    applies = len(exceptions) == 0
    explanation = (
        "Không phát hiện ngoại lệ chính sách trong context hiện có."
        if applies else
        "Phát hiện ngoại lệ chính sách, yêu cầu hoàn tiền không được áp dụng."
    )
    return _normalize_policy_result({
        "policy_applies": applies,
        "policy_name": policy_name,
        "exceptions_found": exceptions,
        "source": sources,
        "policy_version_note": policy_version_note,
        "explanation": explanation,
    }, sources)
# ─────────────────────────────────────────────
# Worker Entry Point
# ─────────────────────────────────────────────

def run(state: dict) -> dict:
    """
    Worker entry point — gọi từ graph.py.

    Args:
        state: AgentState dict

    Returns:
        Updated AgentState với policy_result và mcp_tools_used
    """
    task = state.get("task", "")
    chunks = state.get("retrieved_chunks", [])
    needs_tool = state.get("needs_tool", False)

    state.setdefault("workers_called", [])
    state.setdefault("history", [])
    state.setdefault("mcp_tools_used", [])
    state.setdefault("mcp_tool_called", [])
    state.setdefault("mcp_result", [])

    state["workers_called"].append(WORKER_NAME)

    worker_io = {
        "worker": WORKER_NAME,
        "input": {
            "task": task,
            "chunks_count": len(chunks),
            "needs_tool": needs_tool,
        },
        "output": None,
        "error": None,
    }

    try:
        # Step 1: Nếu chưa có chunks, gọi MCP search_kb
        if not chunks and needs_tool:
            mcp_result = _call_mcp_tool("search_kb", {"query": task, "top_k": 3})
            state["mcp_tools_used"].append(mcp_result)
            state["mcp_tool_called"].append(mcp_result.get("tool"))
            state["mcp_result"].append(mcp_result.get("output"))
            state["history"].append(f"[{WORKER_NAME}] called MCP search_kb")

            if mcp_result.get("output") and mcp_result["output"].get("chunks"):
                chunks = mcp_result["output"]["chunks"]
                state["retrieved_chunks"] = chunks

        # Step 2: Phân tích policy
        policy_result = analyze_policy(task, chunks)
        state["policy_result"] = policy_result

        # Step 3: Nếu cần thêm info từ MCP (e.g., ticket status), gọi get_ticket_info
        if needs_tool and any(kw in task.lower() for kw in ["ticket", "p1", "jira"]):
            mcp_result = _call_mcp_tool("get_ticket_info", {"ticket_id": "P1-LATEST"})
            state["mcp_tools_used"].append(mcp_result)
            state["mcp_tool_called"].append(mcp_result.get("tool"))
            state["mcp_result"].append(mcp_result.get("output"))
            state["history"].append(f"[{WORKER_NAME}] called MCP get_ticket_info")

        worker_io["output"] = {
            "policy_applies": policy_result["policy_applies"],
            "exceptions_count": len(policy_result.get("exceptions_found", [])),
            "mcp_calls": len(state["mcp_tools_used"]),
        }
        state["history"].append(
            f"[{WORKER_NAME}] policy_applies={policy_result['policy_applies']}, "
            f"exceptions={len(policy_result.get('exceptions_found', []))}"
        )

    except Exception as e:
        worker_io["error"] = {"code": "POLICY_CHECK_FAILED", "reason": str(e)}
        state["policy_result"] = {"error": str(e)}
        state["history"].append(f"[{WORKER_NAME}] ERROR: {e}")

    state.setdefault("worker_io_logs", []).append(worker_io)
    return state


# ─────────────────────────────────────────────
# Test độc lập
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 50)
    print("Policy Tool Worker — Standalone Test")
    print("=" * 50)

    test_cases = [
        {
            "task": "Khách hàng Flash Sale yêu cầu hoàn tiền vì sản phẩm lỗi — được không?",
            "retrieved_chunks": [
                {"text": "Ngoại lệ: Đơn hàng Flash Sale không được hoàn tiền.", "source": "policy_refund_v4.txt", "score": 0.9}
            ],
        },
        {
            "task": "Khách hàng muốn hoàn tiền license key đã kích hoạt.",
            "retrieved_chunks": [
                {"text": "Sản phẩm kỹ thuật số (license key, subscription) không được hoàn tiền.", "source": "policy_refund_v4.txt", "score": 0.88}
            ],
        },
        {
            "task": "Khách hàng yêu cầu hoàn tiền trong 5 ngày, sản phẩm lỗi, chưa kích hoạt.",
            "retrieved_chunks": [
                {"text": "Yêu cầu trong 7 ngày làm việc, sản phẩm lỗi nhà sản xuất, chưa dùng.", "source": "policy_refund_v4.txt", "score": 0.85}
            ],
        },
    ]

    for tc in test_cases:
        print(f"\n▶ Task: {tc['task'][:70]}...")
        result = run(tc.copy())
        pr = result.get("policy_result", {})
        print(f"  policy_applies: {pr.get('policy_applies')}")
        if pr.get("exceptions_found"):
            for ex in pr["exceptions_found"]:
                print(f"  exception: {ex['type']} — {ex['rule'][:60]}...")
        print(f"  MCP calls: {len(result.get('mcp_tools_used', []))}")

    print("\n✅ policy_tool_worker test done.")