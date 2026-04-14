# Báo Cáo Cá Nhân — Lab Day 09: Multi-Agent Orchestration

**Họ và tên:** Trần Vọng Triển  
**Vai trò trong nhóm:** Worker Owner (Policy Tool Worker)  
**Ngày nộp:** 14/04/2026  
**Độ dài yêu cầu:** 

---

## 1. Tôi phụ trách phần nào? (100–150 từ)

Tôi trực tiếp chịu trách nhiệm thiết kế và triển khai **Policy Tool Worker**, nhằm kiểm tra các ngoại lệ (exceptions) trước khi phản hồi khách hàng.

**Module/file tôi chịu trách nhiệm:**
- File chính: `workers/policy_tool.py`
- Functions tôi implement: `analyze_policy`, `_normalize_policy_result`, `run`.

**Cách công việc của tôi kết nối với phần của thành viên khác:**
Công việc của tôi nhận input từ `retrieval_worker` (các đoạn context) và chỉ thị từ `supervisor_node` (biến `needs_tool`). Output của tôi cung cấp `policy_result` cho `synthesis_worker` để tạo câu trả lời cuối cùng và thực hiện các cuộc gọi MCP qua `mcp_server` của An.

```python
  "worker_io_logs": [
    {
      "worker": "policy_tool_worker",
      "input": {
        "task": "Contractor cần Admin Access (Level 3) để khắc phục sự cố P1 đang active. Quy trình cấp quyền tạm thời như thế nào?",
        "chunks_count": 0,
        "needs_tool": true
      },
      "output": {
        "policy_applies": true,
        "exceptions_count": 0,
        "mcp_calls": 2
      },
      "error": null
```

**Bằng chứng:**
- File `workers/policy_tool.py` 

 *Commit hash*: c1be063074b45d4bc1c6c8c4d08e6e5aad85faa4

---

## 2. Tôi đã ra một quyết định kỹ thuật gì? (150–200 từ)

**Quyết định:** Thiết kế cơ chế **Hybrid Analysis (LLM + Rule-based Fallback)** và **Data Normalization** cho kết quả trả về.

**Lý do:** LLM đôi khi trả về JSON thiếu trường hoặc sai định dạng khi gặp áp lực về latency, điều này sẽ làm hỏng (crash) toàn bộ Graph. Tôi quyết định không tin tưởng tuyệt đối vào output của LLM mà xây dựng hàm `_normalize_policy_result` để ép kiểu dữ liệu và điền giá trị mặc định. Ngoài ra, tôi thêm logic `if not openai_key` để hệ thống vẫn chạy được dựa trên keyword (Flash Sale, Digital...) nếu API gặp sự cố.

**Trade-off đã chấp nhận:**
Chấp nhận tăng thêm một chút độ phức tạp của code (duy trì cả prompt và bộ rule-based) để đổi lấy sự ổn định của hệ thống (High Availability).

**Bằng chứng từ code:**
```python
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
```

---

## 3. Tôi đã sửa một lỗi gì? (150–200 từ)

**Lỗi:** Mất Context khi `supervisor` yêu cầu dùng tool nhưng `retrieval_worker` chưa cung cấp đủ dữ liệu.

**Symptom:** Trong một số trace test sớm, nếu `retrieved_chunks` trống, `analyze_policy` trả về `True` (có thể hoàn tiền) một cách sai lầm vì không tìm thấy vi phạm nào trong đống context... rỗng.

**Root cause:**
Logic ban đầu phụ thuộc hoàn toàn vào dữ liệu có sẵn trong state. Khi hệ thống cần gọi MCP tool để tra cứu thêm, worker lại thực hiện phân tích ngay lập tức trên dữ liệu trống trước khi tool kịp trả về kết quả.

**Cách sửa:**
Hàm `run` để kiểm tra điều kiện: Nếu `not chunks` nhưng `needs_tool` là True, Worker sẽ chủ động gọi `_call_mcp_tool("search_kb", ...)` để nạp dữ liệu vào state trước khi tiến hành phân tích policy.

**Bằng chứng trước/sau:**
- **Trước:** Trace trả về `policy_applies: True` dù đơn hàng là Flash Sale (do context trống).
- **Sau (Bằng chứng cần điền):** Trong trace run_20260414_154658, log worker_io_logs cho thấy policy_tool_worker nhận chunks_count: 0 nhưng đã thực hiện mcp_calls: 1. Kết quả là policy_result đã chuyển từ True (mặc định khi thiếu context) sang policy_applies: false nhờ tìm thấy ngoại lệ "Digital Product" từ tool search_kb..

```python

  "workers_called": [
    "policy_tool_worker",
    "synthesis_worker"
  ],
  "worker_io_logs": [
    {
      "worker": "policy_tool_worker",
      "input": {
        "task": "Sản phẩm kỹ thuật số (license key) có được hoàn tiền không?",
        "chunks_count": 0,
        "needs_tool": true
      },
      "output": {
        "policy_applies": false,
        "exceptions_count": 1,
        "mcp_calls": 1  },
      "error": null
    },
        
```

---

## 4. Tôi tự đánh giá đóng góp của mình (100–150 từ)

**Tôi làm tốt nhất ở điểm nào?**
Tính cẩn trọng trong việc xử lý dữ liệu. Hệ thống của nhóm sẽ không bị crash do lỗi định dạng JSON từ Worker của tôi nhờ hàm Normalization.

**Tôi làm chưa tốt hoặc còn yếu ở điểm nào?**
Phần Fallback rule-based còn khá đơn giản, chỉ dựa trên keyword matching thô sơ nên có thể bị đánh lừa bởi ngữ cảnh phủ định (ví dụ: "đây không phải là flash sale").

**Nhóm phụ thuộc vào tôi ở đâu?**
Nếu Worker của tôi không xác định đúng `policy_applies`, toàn bộ câu trả lời của Agent sẽ vi phạm quy định công ty, gây rủi ro pháp lý/tài chính.

**Phần tôi phụ thuộc vào thành viên khác:**
Tôi cần An (MCP Owner) đảm bảo server MCP trả về đúng schema `chunks` để hàm `run` của tôi có thể kế thừa dữ liệu đó.

---

## 5. Nếu có thêm 2 giờ, tôi sẽ làm gì? (50–100 từ)

Tôi sẽ nâng cấp logic kiểm tra ngày tháng ở phần Fallback. 

**Lý do:** Hiện tại, trace của các câu hỏi liên quan đến lịch sử (như giao dịch trước 01/02/2026) đang bị code xử lý cứng bằng string matching. Tôi muốn dùng thư viện `dateutil` để parse ngày tháng từ task, từ đó xác định chính xác phiên bản Policy V3 hay V4, giúp tăng độ chính xác cho các câu hỏi về mốc thời gian (như câu `q02` đã bị lệch route).



