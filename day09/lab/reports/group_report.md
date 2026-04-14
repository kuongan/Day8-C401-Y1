# Báo Cáo Nhóm — Lab Day 09: Multi-Agent Orchestration

**Tên nhóm:** Day09-Team  
**Thành viên:**
| Tên | Vai trò | Email |
|-----|---------|-------|
| Lê Hoàng Minh | Orchestrator Owner | 26ai.minhlh@vinu.edu.vn |
| Trần Vọng Triển | Retrieval Owner | 26ai.trientv@vinuni.edu.vn |
| Nguyễn Minh Châu | Policy Owner | 26ai.chaunm@vinuni.edu.vn |
| Nguyễn Trần Khương An | MCP Owner | 26ai.anntk@vinuni.edu.vn |
| Phương Hoàng Yến | Trace + Eval Owner | 26ai.yenph@vinuni.edu.vn |
| Phạm Minh Việt | Documentation + Report Owner | 26ai.vietpm@vinuni.edu.vn |

**Ngày nộp:** 14/04/2026  
**Repo:** Day8-C401-Y1/day09/lab  
**Độ dài:** ~900 từ

---

## 1. Kiến trúc nhóm đã xây dựng

Nhóm xây dựng pipeline theo mô hình Supervisor-Worker với 3 worker chính: retrieval_worker, policy_tool_worker, synthesis_worker, và 1 nhánh HITL qua human_review cho câu rủi ro cao. Luồng chạy: supervisor phân tích task và ghi route_reason, sau đó route sang worker phù hợp, cuối cùng synthesis tổng hợp câu trả lời có nguồn.

Routing logic cốt lõi dùng rule-based keyword matching trong graph.py thay vì LLM classifier. Rule ưu tiên policy/access keyword cho policy_tool_worker; keyword SLA/P1/ticket cho retrieval_worker; pattern error-code như ERR-xxx kích hoạt human_review trước khi chạy retrieval. Cách này giúp route minh bạch và dễ debug từ trace.

MCP tools đã tích hợp gồm search_kb và get_ticket_info. Trong trace run_20260414_155333 (q15), policy_tool_worker gọi cả hai tool để lấy evidence từ access_control_sop + SLA, đồng thời lấy ticket context thực tế, sau đó synthesis tạo answer tổng hợp cho bài toán multi-hop.

---

## 2. Quyết định kỹ thuật quan trọng nhất

**Quyết định:** Dùng keyword-based routing + risk flag thay vì LLM-based route classifier.

**Bối cảnh vấn đề:**
Ở Sprint 1, nhóm cân nhắc việc để supervisor gọi thêm 1 lần LLM để phân loại intent trước khi chọn worker. Cách này linh hoạt nhưng tăng latency và làm trace khó lặp lại giữa các lần chạy. Với timebox của lab và bộ câu hỏi có domain rõ (SLA, refund, access, error-code), nhóm cần routing ổn định và có thể giải thích được.

**Các phương án đã cân nhắc:**

| Phương án | Ưu điểm | Nhược điểm |
|-----------|---------|-----------|
| LLM classifier cho supervisor | Nhận diện intent mềm dẻo | Tăng latency, khó reproducible, tốn thêm call |
| Keyword + rule-based | Nhanh, trace rõ, deterministic | Có false-positive nếu keyword quá rộng |

**Phương án đã chọn và lý do:**

Nhóm chọn keyword + rule-based để ưu tiên tốc độ và khả năng debug. Kết quả thực tế từ 36 traces: routing accuracy đạt 14/15 câu unique, chỉ lệch q02. Ngoài ra route_reason thể hiện rõ lý do route nên dễ truy nguyên.

**Bằng chứng từ trace/code:**

```text
run_20260414_154651.json (q06)
route_reason = "task contains P1/SLA/ticket/escalation keyword | no MCP"
supervisor_route = "retrieval_worker"

run_20260414_155152.json (q07)
route_reason = "task contains policy/access keyword | choose MCP tools"
supervisor_route = "policy_tool_worker"

run_20260414_154718.json (q09)
route_reason = "unknown error-code style query requires human review | human approved -> retrieval"
hitl_triggered = true
```

---

## 3. Kết quả grading questions

Trong lần chạy hiện tại, nhóm chủ yếu có trace của bộ test q01-q15; file grading_run chính thức chưa được khóa điểm trong repo này, nên chưa chốt được raw score 96 theo rubric grading. Tuy vậy, nhóm dùng các câu tương đương để kiểm tra readiness.

**Tổng điểm raw ước tính:** N/A (chưa có grading_run.jsonl final trong bản này)

**Câu pipeline xử lý tốt nhất:**
- ID: q06 — Lý do tốt: route đúng retrieval_worker, trả lời đúng rule escalation sau 10 phút, confidence 0.70, latency 7.5s.

**Câu pipeline fail hoặc partial:**
- ID: q02 — Fail ở đâu: routing lệch sang policy_tool_worker  
  Root cause: rule keyword refund quá rộng, chưa tách câu fact retrieval đơn giản và câu policy exception.

**Câu abstain (tương đương gq07):**
Với q09 (ERR-403-AUTH), supervisor kích hoạt human_review rồi mới retrieval. Kết quả abstain grounded, tránh bịa nghĩa lỗi.

**Câu multi-hop khó (tương đương gq09):**
q15 ghi rõ 2 worker policy_tool_worker + synthesis_worker, có gọi 2 MCP tools (search_kb, get_ticket_info) và trả lời đủ cả access + SLA.

---

## 4. So sánh Day 08 vs Day 09 — Điều nhóm quan sát được

Metric thay đổi rõ nhất là khả năng quan sát và debug. Day08 không có route_reason; Day09 có trace đầy đủ route_reason, workers_called, mcp_tools_used, hitl_triggered. Về số liệu: Day09 có avg_confidence 0.506, avg_latency 27,939ms, mcp_usage_rate 44%, hitl_rate 5%, routing distribution retrieval/policy = 55%/44%.

Điều nhóm bất ngờ là multi-agent không tự động tăng chất lượng ở mọi câu. Ví dụ q02 vẫn sai tuyến do rule chưa tinh, cho thấy routing logic cần được tune giống như retrieval/generation.

Trường hợp multi-agent không giúp ích là các câu ngắn, fact đơn giản. Lúc đó chi phí orchestration làm tăng latency nhưng giá trị bổ sung về chất lượng trả lời không nhiều. Ngược lại, ở câu khó multi-hop hoặc câu rủi ro cao, multi-agent cho lợi thế lớn nhờ tách vai trò và cho phép gắn HITL.

---

## 5. Phân công và đánh giá nhóm

**Phân công thực tế:**

| Thành viên | Phần đã làm | Sprint |
|------------|-------------|--------|
| Lê Hoàng Minh | graph.py: AgentState, supervisor_node, route_decision, route_reason, risk_high, workers_called | 1 |
| Trần Vọng Triển | retrieval.py: query Chroma, retrieved_chunks, retrieved_sources, worker_io_log (retrieval) | 2 |
| Nguyễn Minh Châu | policy_tool.py: policy check, exception (Flash Sale/digital), hitl_triggered rule | 2-3 |
| Nguyễn Trần Khương An | mcp_server.py: search_kb, get_ticket_info, format mcp_tool_called/mcp_result, tích hợp vào policy worker | 3 |
| Phương Hoàng Yến | eval_trace.py + artifacts: chạy 15 test questions, metrics compare, tạo grading_run.jsonl đúng schema | 4 |
| Phạm Minh Việt | system_architecture.md, routing_decisions.md, single_vs_multi_comparison.md, group_report.md, template.md; tổng hợp bằng chứng trace/code và kiểm report khớp đóng góp | 4 |

**Điều nhóm làm tốt:**

Phân tách module tương đối rõ giữa supervisor, workers, và tool layer; trace format thống nhất nên debug nhanh.

**Điều nhóm làm chưa tốt:**

Rule routing ban đầu quá rộng cho nhóm keyword refund, gây lệch route ở q02; chưa có automated regression test cho routing.

**Nếu làm lại, nhóm sẽ thay đổi gì trong cách tổ chức?**

Thiết lập bộ unit test routing ngay cuối Sprint 1 để khóa expected_route sớm, tránh lan lỗi sang Sprint 3-4.

---

## 6. Nếu có thêm 1 ngày, nhóm sẽ làm gì?

Nhóm sẽ thêm intent disambiguation cho các câu refund (fact query vs exception query) và thêm confidence threshold để tự động chuyển HITL khi confidence dưới ngưỡng ở câu rủi ro cao. Lý do: trace hiện tại cho thấy q02 bị route lệch do keyword đơn giản, trong khi q09 chứng minh HITL giúp giảm nguy cơ hallucination.
