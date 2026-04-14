# Routing Decisions Log — Lab Day 09

**Nhóm:** Day09-Team  
**Ngày:** 14/04/2026

> Dữ liệu bên dưới lấy từ trace thật trong thư mục artifacts/traces.

---

## Routing Decision #1

**Task đầu vào:**
> Ticket P1 không được phản hồi sau 10 phút. Hệ thống tự động làm gì?

**Worker được chọn:** retrieval_worker  
**Route reason (từ trace):** task contains P1/SLA/ticket/escalation keyword | no MCP  
**MCP tools được gọi:** Không  
**Workers called sequence:** retrieval_worker -> synthesis_worker

**Kết quả thực tế:**
- final_answer (ngắn): Hệ thống tự động escalate lên Senior Engineer.
- confidence: 0.70
- Correct routing? Yes

**Bằng chứng trace:** run_20260414_154651.json (q06)

**Nhận xét:** Đây là ca route đúng mẫu cho câu SLA. Supervisor không gọi policy worker nên giảm chi phí tool call và latency chỉ 7,523ms.

---

## Routing Decision #2

**Task đầu vào:**
> Sản phẩm kỹ thuật số (license key) có được hoàn tiền không?

**Worker được chọn:** policy_tool_worker  
**Route reason (từ trace):** task contains policy/access keyword | choose MCP tools  
**MCP tools được gọi:** search_kb  
**Workers called sequence:** policy_tool_worker -> synthesis_worker

**Kết quả thực tế:**
- final_answer (ngắn): License key không được hoàn tiền theo ngoại lệ trong policy_refund_v4.
- confidence: 0.58
- Correct routing? Yes

**Bằng chứng trace:** run_20260414_155152.json (q07)

**Nhận xét:** Route này đúng vì câu hỏi cần policy exception parsing. Policy worker phát hiện exceptions_count = 1 (Digital Product), giúp answer có cơ sở rõ ràng.

---

## Routing Decision #3

**Task đầu vào:**
> ERR-403-AUTH là lỗi gì và cách xử lý?

**Worker được chọn:** human_review (ban đầu), sau đó retrieval_worker  
**Route reason (từ trace):** unknown error-code style query requires human review | human approved -> retrieval  
**MCP tools được gọi:** Không  
**Workers called sequence:** human_review -> retrieval_worker -> synthesis_worker

**Kết quả thực tế:**
- final_answer (ngắn): Không đủ thông tin trong tài liệu nội bộ để xác định lỗi ERR-403-AUTH.
- confidence: 0.30
- Correct routing? Yes

**Bằng chứng trace:** run_20260414_154718.json (q09)

**Nhận xét:** Đây là quyết định routing quan trọng để tránh hallucination. Trigger HITL trước khi trả lời, sau đó pipeline đi retrieval để lấy bằng chứng và abstain có kiểm soát.

---

## Tổng kết

### Routing Distribution

| Worker | Số câu được route | % tổng |
|--------|------------------|--------|
| retrieval_worker | 20 | 55% |
| policy_tool_worker | 16 | 44% |
| human_review (trigger) | 2 | 5% |

### Routing Accuracy

Trong 15 câu hỏi unique (36 trace runs), supervisor route đúng 14/15 câu theo expected_route trong test_questions.

- Câu route đúng: 14 / 15
- Câu route sai: q02 (expected retrieval nhưng route policy vì keyword refund)
- Câu trigger HITL: 2 (đều là q09)

### Lesson Learned về Routing

1. Keyword routing đủ nhanh và minh bạch để debug, nhưng cần thêm rule ưu tiên để giảm false-positive ở các câu refund đơn giản như q02.
2. HITL rule cho pattern error-code giúp giảm rủi ro trả lời bịa ở nhóm câu không có evidence trong KB.

### Route Reason Quality

route_reason hiện tại đã hữu ích cho debug vì ghi rõ trigger keyword và cờ risk. Cải tiến tiếp theo là chuẩn hóa format machine-readable, ví dụ: route=policy_tool_worker;reason=keyword:refund;risk=false;needs_tool=true.
