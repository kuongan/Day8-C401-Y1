# Báo Cáo Cá Nhân — Lab Day 09: Multi-Agent Orchestration

**Họ và tên:** Le Hoang Minh  
**MSSV:** 2A202600471  
**Vai trò trong nhóm:** Sprint 1  
**Ngày nộp:** 14/04/2026  
**Độ dài:** ~650 từ

---

## 1. Tôi phụ trách phần nào?

Trong Day 09, tôi phụ trách chính phần Sprint 1, điều phối ở `graph.py`. Cụ thể, tôi triển khai `AgentState` làm shared state xuyên suốt pipeline, sau đó viết `supervisor_node()` để phân tích task đầu vào và quyết định route cho worker phù hợp. Tôi cũng viết `route_decision()` để tách riêng logic chọn nhánh, giúp dễ test và dễ thay đổi khi mở rộng rule. Ngoài ra, tôi kết nối flow tổng thể theo đúng kiến trúc supervisor-worker: supervisor -> worker phù hợp -> synthesis.

Phần của tôi là điểm vào của toàn hệ thống, nên ảnh hưởng trực tiếp đến Sprint 2 và Sprint 3. Nếu route sai, dù retrieval/policy worker làm đúng thì câu trả lời cuối vẫn lệch. Vì vậy, tôi tập trung vào traceability ngay từ Sprint 1: mỗi quyết định route đều có `route_reason`, có cờ `risk_high`, và có log trong `history` để truy vết nguyên nhân.

**Module/file tôi chịu trách nhiệm:**
- File chính: `graph.py`
- Functions: `make_initial_state`, `supervisor_node`, `route_decision`, `build_graph`, `run_graph`

**Bằng chứng:**
- Chạy `python graph.py` tạo trace JSON tại `artifacts/traces/`.
- Trace có đủ trường route và history như yêu cầu DoD Sprint 1.

---

## 2. Tôi đã ra một quyết định kỹ thuật gì?

**Quyết định:** Tôi chọn keyword-based routing cho supervisor thay vì dùng LLM classifier ở Sprint 1.

Tôi cân nhắc hai lựa chọn. Lựa chọn thứ nhất là gọi LLM để phân loại intent rồi route. Cách này linh hoạt, nhưng tốn thêm độ trễ, khó kiểm soát output, và khó debug trong giai đoạn đầu khi nhóm còn đang tách monolith sang graph. Lựa chọn thứ hai là rule-based theo từ khóa domain (refund/policy/access/P1/ticket/error code). Tôi chọn lựa chọn thứ hai vì Sprint 1 ưu tiên tính ổn định và khả năng kiểm chứng.

Với quyết định này, chúng tôi có thể giải thích rõ “tại sao route như vậy” bằng một chuỗi lý do cố định (`route_reason`) thay vì một câu classify khó kiểm định. Điều này hỗ trợ trực tiếp cho phần debug tree ở README: khi sai route thì nhìn ngay được signal nào đã kích hoạt. Ví dụ trong trace cho câu SLA P1, route được ghi là `retrieval_worker` cùng lý do `task contains P1/SLA/ticket/escalation keyword | no MCP`. Với câu refund, route là `policy_tool_worker` cùng lý do `task contains policy/access keyword | choose MCP tools`.

**Trade-off tôi chấp nhận:** keyword routing có thể sai ở câu nhiều ý (multi-intent), đặc biệt khi query chứa cả access và P1. Tôi chấp nhận trade-off này ở Sprint 1 để đảm bảo graph chạy ổn định trước, rồi mới tối ưu ưu tiên route ở sprint sau.

**Bằng chứng từ trace/code:**

```text
q13: supervisor_route=policy_tool_worker
route_reason="task contains policy/access keyword | choose MCP tools"

q14: supervisor_route=retrieval_worker
route_reason="default fallback: general retrieval | no MCP"

q15: supervisor_route=policy_tool_worker
route_reason="task contains policy/access keyword | choose MCP tools | risk_high flagged"
```

---

## 3. Tôi đã sửa một lỗi gì?

**Lỗi:** Thiếu khả năng xử lý riêng cho truy vấn có mã lỗi không rõ (dạng ERR-xxx), khiến pipeline dễ đi vào luồng retrieval mặc định và trả lời thiếu an toàn.

**Symptom:** Ở các câu hỏi kiểu sự cố hệ thống có mã lỗi, hệ thống cần human review trước khi trả lời tự động. Nếu không có nhánh này, output có thể tự tin sai hoặc thiếu cảnh báo vận hành.

**Root cause:** Routing rule ban đầu chưa tách explicit branch cho unknown error code. Mọi query lạ bị gom vào fallback retrieval.

**Cách sửa:** Tôi thêm điều kiện ưu tiên trong `supervisor_node`:
- Nếu task chứa `err-` hoặc `error code` -> route `human_review`
- Đồng thời bật `risk_high=True`
- Sau placeholder human approval thì mới quay lại retrieval để tiếp tục pipeline.

Cách sửa này giữ được hai mục tiêu cùng lúc: an toàn vận hành (có HITL) và không làm gãy luồng xử lý tự động của lab (vì lab mode auto-approve).

**Bằng chứng trước/sau:**
- Trước khi bổ sung nhánh này: query dạng lỗi dễ rơi về fallback retrieval.
- Sau khi sửa, trace có lý do rõ ràng:
`route_reason="unknown error-code style query requires human review | human approved -> retrieval"`

Việc có log rõ đường đi giúp nhóm dễ audit vì biết chính xác lúc nào hệ thống đã trigger human_review.

---

## 4. Tôi tự đánh giá đóng góp của mình

Điểm tôi làm tốt nhất là biến Sprint 1 từ mức “chạy được” thành mức “debug được”. Tôi không chỉ route, mà còn chuẩn hóa state và log để các sprint sau có dữ liệu phân tích. Điều này giúp các bạn làm worker không phải đoán “vì sao vào nhánh này”.

Điểm tôi chưa tốt là phần ưu tiên route cho câu hỏi multi-intent (vừa có access vừa có P1) chưa thật tối ưu theo guideline “P1 ưu tiên”. Đây là điểm tôi đã note để tinh chỉnh rule thứ tự ưu tiên.

Nhóm phụ thuộc vào tôi ở chỗ orchestrator là xương sống: nếu state/route/history không ổn định thì Sprint 2 và Sprint 3 bị chặn vì worker không nhận đúng ngữ cảnh. Ngược lại, tôi phụ thuộc vào thành viên phụ trách worker để kiểm chứng route bằng output thực tế, và phụ thuộc phần synthesis để xác nhận route hiện tại có tạo ra câu trả lời đúng không.

---

## 5. Nếu có thêm 2 giờ, tôi sẽ làm gì?

Tôi sẽ chỉnh lại ưu tiên routing cho multi-intent theo hướng “P1/escalation/ticket thắng policy/access” để bám sát guideline Sprint 1. Lý do: trace q15 cho thấy query có cả P1 lẫn access đang route sang `policy_tool_worker`, trong khi yêu cầu bài lab nhấn mạnh P1 là tín hiệu ưu tiên. Sau khi sửa, tôi sẽ chạy lại toàn bộ test questions và so sánh tỉ lệ route đúng theo rule.
