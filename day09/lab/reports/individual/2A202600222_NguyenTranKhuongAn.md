# Báo Cáo Cá Nhân — Lab Day 09: Multi-Agent Orchestration

**Họ và tên:** Nguyễn Trần Khương An
**Vai trò trong nhóm:** MCP Owner
**Ngày nộp:** 14/04/2026  
**Độ dài yêu cầu:** 500–800 từ

---

> **Lưu ý quan trọng:**
> - Viết ở ngôi **"tôi"**, gắn với chi tiết thật của phần bạn làm
> - Phải có **bằng chứng cụ thể**: tên file, đoạn code, kết quả trace, hoặc commit
> - Nội dung phân tích phải khác hoàn toàn với các thành viên trong nhóm
> - Deadline: Được commit **sau 18:00** (xem SCORING.md)
> - Lưu file với tên: `reports/individual/[ten_ban].md` (VD: `nguyen_van_a.md`)

---

## 1. Tôi phụ trách phần nào? (100–150 từ)

> Mô tả cụ thể module, worker, contract, hoặc phần trace bạn trực tiếp làm.
> Không chỉ nói "tôi làm Sprint X" — nói rõ file nào, function nào, quyết định nào.

Trong lab này tôi phụ trách vai trò MCP Owner, đồng thời là người nối các phần Sprint 1-3 để pipeline chạy liền mạch. Trọng tâm của tôi là xây dựng tầng công cụ trung gian để policy worker không phải gọi API hay truy cập KB theo kiểu hard-code. Tôi chịu trách nhiệm chính ở `mcp_server.py` và phần tích hợp trong `workers/policy_tool.py`, đồng thời chỉnh `graph.py` để state và trace mang được thông tin MCP.

**Module/file tôi chịu trách nhiệm:**
- File chính: `day09/lab/mcp_server.py`
- Functions tôi implement: `list_tools()`, `dispatch_tool()`, `call_tool()`, `tool_search_kb()`, `tool_get_ticket_info()`

**Cách công việc của tôi kết nối với phần của thành viên khác:**

Tôi nối supervisor và worker bằng cơ chế `needs_tool` và `mcp_tools_used`, để khi supervisor route vào policy worker thì worker có thể gọi MCP ngay thay vì phụ thuộc chặt vào retrieval. Tôi cũng thêm `mcp_tool_called` và `mcp_result` vào state để Trace & Docs owner có đủ dữ liệu phân tích flow.

**Bằng chứng (commit hash, file có comment tên bạn, v.v.):**

Commit chính của tôi: `1af7f64` (author/nhãn: kuongan), thay đổi các file `day09/lab/mcp_server.py`, `day09/lab/workers/policy_tool.py`, `day09/lab/graph.py`.

---

## 2. Tôi đã ra một quyết định kỹ thuật gì? (150–200 từ)

> Chọn **1 quyết định** bạn trực tiếp đề xuất hoặc implement trong phần mình phụ trách.
> Giải thích:
> - Quyết định là gì?
> - Các lựa chọn thay thế là gì?
> - Tại sao bạn chọn cách này?
> - Bằng chứng từ code/trace cho thấy quyết định này có effect gì?

**Quyết định:** Tôi chọn dùng mock MCP interface thống nhất (`call_tool` envelope) thay vì để từng worker tự gọi function trực tiếp.

**Ví dụ:**
> "Tôi chọn dùng keyword-based routing trong supervisor_node thay vì gọi LLM để classify.
>  Lý do: keyword routing nhanh hơn (~5ms vs ~800ms) và đủ chính xác cho 5 categories.
>  Bằng chứng: trace gq01 route_reason='task contains P1 SLA keyword', latency=45ms."

**Lý do:**

Tôi cân nhắc hai cách. Cách 1 là để `policy_tool.py` gọi thẳng `retrieve_dense` hoặc các hàm nghiệp vụ. Cách này làm nhanh nhưng về dài hạn sẽ khó bảo trì vì worker sẽ phụ thuộc trực tiếp vào implementation bên dưới. Cách 2 là đặt một lớp MCP chuẩn hóa input/output rồi worker chỉ biết gọi tool qua tên tool. Tôi chọn cách 2 vì bám đúng yêu cầu Sprint 3 và giúp mở rộng công cụ mới mà không sửa graph logic.

Tôi implement `call_tool()` theo format JSON có `tool`, `input`, `output`, `timestamp`. Trong `policy_tool.py`, mỗi lần gọi MCP sẽ append đồng thời vào `mcp_tools_used`, `mcp_tool_called`, `mcp_result`. Nhờ vậy trace vừa có bản đầy đủ của call, vừa có field gọn để thống kê.

**Trade-off đã chấp nhận:**

Trade-off là tăng thêm một lớp trung gian nên code dài hơn và cần map schema cẩn thận. Ngoài ra ở chế độ lab, khi KB chưa sẵn sàng tôi cho phép fallback mock để pipeline không gãy, đổi lại quality câu trả lời có thể thấp hơn dữ liệu thật.

**Bằng chứng từ trace/code:**

```
# mcp_server.py
def call_tool(tool_name: str, tool_input: dict) -> dict:
	return {
		"tool": tool_name,
		"input": tool_input,
		"output": dispatch_tool(tool_name, tool_input),
		"timestamp": datetime.now().replace(microsecond=0).isoformat(),
	}

# trace mẫu run_20260414_150816.json
"mcp_tool_called": ["search_kb"],
"mcp_result": [{"chunks": [...], "sources": ["policy_refund_v4.txt"], "total_found": 3}]
```

---

## 3. Tôi đã sửa một lỗi gì? (150–200 từ)

> Mô tả 1 bug thực tế bạn gặp và sửa được trong lab hôm nay.
> Phải có: mô tả lỗi, symptom, root cause, cách sửa, và bằng chứng trước/sau.

**Lỗi:** `policy_result.policy_applies` có lúc bị thiếu hoặc thành `None`.

**Symptom (pipeline làm gì sai?):**

Trong test độc lập của policy worker với câu hỏi dạng ticket/escalation, log cho thấy `policy_applies= None` dù worker vẫn chạy xong và đã gọi MCP tools. Điều này làm downstream logic và báo cáo trace không ổn định vì contract yêu cầu `policy_applies` phải là bool.

**Root cause (lỗi nằm ở đâu — indexing, routing, contract, worker logic?):**

Lỗi nằm ở worker logic: phần parse JSON từ LLM trong `analyze_policy()` nhận nguyên output model mà không normalize schema. Khi model trả thiếu field `policy_applies`, code không ép kiểu hoặc điền default nên giá trị bị rỗng.

**Cách sửa:**

Tôi thêm hàm `_normalize_policy_result(raw, sources)` để chuẩn hóa output trước khi ghi state. Hàm này đảm bảo luôn có đủ: `policy_applies` (bool), `policy_name`, `exceptions_found` (list), `source` (list), `policy_version_note`, `explanation`. Nếu thiếu `policy_applies`, tôi suy luận mặc định theo số lượng exception (`len(exceptions)==0`). Sau khi vá, test lại cho kết quả `policy_applies= True bool` thay vì `None`.

**Bằng chứng trước/sau:**
> Dán trace/log/output trước khi sửa và sau khi sửa.

Trước sửa (test policy worker):
`policy_applies= None`

Sau sửa (test policy worker):
`policy_applies= True bool`

Đồng thời trace vẫn giữ đúng dữ liệu MCP:
`mcp_tool_called= ['search_kb', 'get_ticket_info']`
`mcp_result_count= 2`

---

## 4. Tôi tự đánh giá đóng góp của mình (100–150 từ)

> Trả lời trung thực — không phải để khen ngợi bản thân.

**Tôi làm tốt nhất ở điểm nào?**

Tôi làm tốt nhất ở phần thiết kế điểm nối giữa các module. Cụ thể là tách rõ lớp MCP để policy worker gọi tool chuẩn hóa, đồng thời đưa dữ liệu trace về dạng dễ đọc và dễ thống kê. Nhờ đó lúc debug có thể biết worker gọi tool nào, input gì, output gì và thời điểm nào.

**Tôi làm chưa tốt hoặc còn yếu ở điểm nào?**

Ban đầu tôi để output policy phụ thuộc nhiều vào format JSON của LLM nên có trường hợp thiếu field. Tôi cũng mất thêm thời gian vì phải xử lý fallback cho giai đoạn KB chưa sẵn sàng.

**Nhóm phụ thuộc vào tôi ở đâu?** _(Phần nào của hệ thống bị block nếu tôi chưa xong?)_

Nếu tôi chưa hoàn thành MCP server và phần tích hợp ở policy worker thì Sprint 3 bị block hoàn toàn, trace không có `mcp_tool_called`/`mcp_result`, và nhóm không chứng minh được external capability qua MCP.

**Phần tôi phụ thuộc vào thành viên khác:** _(Tôi cần gì từ ai để tiếp tục được?)_

Tôi phụ thuộc vào người phụ trách retrieval/index để dữ liệu KB đã index đầy đủ, và phụ thuộc supervisor owner để route đúng `needs_tool=True` cho các câu policy/access/ticket cần gọi MCP.

---

## 5. Nếu có thêm 2 giờ, tôi sẽ làm gì? (50–100 từ)

> Nêu **đúng 1 cải tiến** với lý do có bằng chứng từ trace hoặc scorecard.
> Không phải "làm tốt hơn chung chung" — phải là:
> *"Tôi sẽ thử X vì trace của câu gq___ cho thấy Y."*

Tôi sẽ nâng `mcp_server.py` từ in-process mock sang HTTP-based MCP service (FastAPI) để tách hẳn runtime giữa worker và tool layer. Lý do là trace hiện cho thấy latency của các câu policy vẫn cao (khoảng 15s), và nếu tách service tôi có thể cache kết quả `search_kb(query, top_k)` để giảm thời gian ở những câu hỏi lặp ngữ nghĩa gần nhau.

---

*Lưu file này với tên: `reports/individual/[ten_ban].md`*  
*Ví dụ: `reports/individual/nguyen_van_a.md`*
