# Single Agent vs Multi-Agent Comparison — Lab Day 09

**Nhóm:** Day09-Team  
**Ngày:** 14/04/2026

---

## 1. Metrics Comparison

Nguồn số liệu:
- Day 08: results baseline trong eval report (avg_confidence = 4.6/5)
- Day 09: artifacts/eval_report.json (36 traces)

| Metric | Day 08 (Single Agent) | Day 09 (Multi-Agent) | Delta | Ghi chú |
|--------|----------------------|---------------------|-------|---------|
| Avg confidence | 4.6/5 (~0.92) | 0.506 | -0.414 | Hai pipeline dùng thang confidence khác nhau, đã quy đổi Day08 về thang 0-1 để so |
| Avg latency (ms) | N/A (không log) | 27,939 | N/A | Day09 có trace latency đầy đủ, Day08 chưa instrument |
| Routing coverage | N/A | retrieval 55%, policy 44%, HITL 5% | N/A | Chỉ có ở multi-agent |
| MCP usage rate | N/A | 44% (16/36) | N/A | Cho thấy tool worker được sử dụng thường xuyên |
| Routing visibility | Không có route_reason | Có route_reason theo từng câu | Cải thiện rõ | Hỗ trợ debug trực tiếp từ trace |
| Debug time (estimate) | 20-30 phút | 5-10 phút | Giảm ~15-20 phút | Theo trải nghiệm debug q02 và q09 |

---

## 2. Phân tích theo loại câu hỏi

### 2.1 Câu hỏi đơn giản (single-document)

| Nhận xét | Day 08 | Day 09 |
|---------|--------|--------|
| Accuracy | Ổn định ở các câu fact ngắn | Ổn định nếu route đúng worker |
| Latency | Thấp hơn (không qua supervisor/tool) | Cao hơn vì thêm orchestration |
| Observation | Không có route trace nên khó truy nguyên | Có thể thấy ngay route_reason và worker sequence |

**Kết luận:** Với câu đơn giản, single-agent nhanh hơn. Multi-agent không tăng chất lượng rõ rệt nhưng tăng khả năng quan sát và debug.

### 2.2 Câu hỏi multi-hop (cross-document)

| Nhận xét | Day 08 | Day 09 |
|---------|--------|--------|
| Accuracy | Có thể đúng nhưng thiếu tách vai trò | Tốt hơn ở câu có policy + SLA khi policy worker gọi MCP |
| Routing visible? | ✗ | ✓ |
| Observation | Không phân biệt lỗi retrieval hay logic policy | Trace thể hiện rõ workers_called và mcp_tools_used |

**Kết luận:** Multi-agent có lợi thế rõ ở câu multi-hop vì chia worker theo nhiệm vụ và ghi lại đường đi đầy đủ.

### 2.3 Câu hỏi cần abstain

| Nhận xét | Day 08 | Day 09 |
|---------|--------|--------|
| Abstain behavior | Có abstain nhưng không có HITL | Có abstain + có thể trigger HITL |
| Hallucination cases | Giảm nhờ prompt grounded | Giảm thêm ở nhóm câu rủi ro cao do route human_review |
| Observation | Không biết vì sao abstain | Biết rõ trigger bằng route_reason và hitl_triggered |

**Kết luận:** Day09 an toàn hơn cho câu thiếu dữ liệu vì có thêm cơ chế HITL thay vì chỉ phụ thuộc prompt.

---

## 3. Debuggability Analysis

### Day 08 — Debug workflow
```
Khi answer sai -> phải đọc toàn bộ RAG pipeline code -> tìm lỗi ở indexing/retrieval/generation.
Không có trace route nên khó xác định điểm lỗi đầu tiên.
Thời gian ước tính: 20-30 phút/case.
```

### Day 09 — Debug workflow
```
Khi answer sai -> đọc trace -> xem supervisor_route + route_reason.
Nếu route sai -> sửa routing rules trong supervisor.
Nếu retrieval sai -> test retrieval_worker độc lập.
Nếu synthesis sai -> test synthesis_worker độc lập.
Thời gian ước tính: 5-10 phút/case.
```

**Case debug thực tế:** q02 bị route sang policy_tool_worker thay vì retrieval_worker do rule keyword refund. Nhờ trace có route_reason nên xác định root cause trong supervisor rule trong vài phút.

---

## 4. Extensibility Analysis

| Scenario | Day 08 | Day 09 |
|---------|--------|--------|
| Thêm 1 tool/API mới | Phải sửa prompt hoặc pipeline chính | Thêm MCP tool và điều kiện route |
| Thêm 1 domain mới | Prompt phình to, khó kiểm soát | Thêm worker mới theo domain |
| Thay đổi retrieval strategy | Sửa trực tiếp pipeline chung | Chỉ sửa retrieval_worker |
| A/B test một phần | Khó tách biệt | Dễ test theo từng worker |

**Nhận xét:** Day09 kiến trúc tốt hơn cho mở rộng dài hạn, đổi lại phải trả chi phí orchestration và monitoring nhiều hơn.

---

## 5. Cost & Latency Trade-off

| Scenario | Day 08 calls | Day 09 calls |
|---------|-------------|-------------|
| Simple query | 1 LLM call | 1 LLM call + supervisor/routing overhead |
| Complex query | 1 LLM call | 1 LLM call + 1-2 MCP tool calls + worker orchestration |
| MCP tool call | N/A | 1-2 tool calls/câu policy |

**Nhận xét về cost-benefit:** Day09 đắt hơn về latency và complexity, nhưng đổi lại có khả năng trace, kiểm soát lỗi, và mở rộng tốt hơn cho production-like workflow.

---

## 6. Kết luận

**Multi-agent tốt hơn single-agent ở điểm nào?**

1. Quan sát hệ thống tốt hơn nhờ route_reason, workers_called, mcp_tools_used và hitl_triggered.
2. Dễ debug và mở rộng hơn do kiến trúc tách vai trò theo worker.

**Multi-agent kém hơn hoặc không khác biệt ở điểm nào?**

1. Latency cao hơn và cần thêm effort để tuning routing rules.

**Khi nào không nên dùng multi-agent?**

Khi use case chỉ gồm các câu đơn giản, domain hẹp, ít thay đổi và ưu tiên tốc độ hơn khả năng quan sát.

**Nếu tiếp tục phát triển hệ thống này, nhóm sẽ thêm gì?**

Thêm bộ routing rules ưu tiên theo expected intent (đặc biệt tách refund fact query và policy exception query) và bổ sung confidence threshold để tự động escalate sang HITL khi confidence thấp ở câu rủi ro.
