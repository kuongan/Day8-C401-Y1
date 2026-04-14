# Báo Cáo Cá Nhân — Lab Day 09: Multi-Agent Orchestration

**Họ và tên:** Phạm Minh Việt  
**Vai trò trong nhóm:** Documentation + Report Owner  
**Ngày nộp:** 14/04/2026  
**Độ dài:** khoảng 680 từ

---


## 1. Tôi phụ trách phần nào?

Trong lab Day 09, phần tôi chịu trách nhiệm chính là Documentation + Report, tức biến kết quả kỹ thuật thành hồ sơ nộp có thể kiểm chứng được theo rubric. Cụ thể, tôi phụ trách điền và đồng bộ nội dung ở các file: day09/lab/docs/system_architecture.md, day09/lab/docs/routing_decisions.md, day09/lab/docs/single_vs_multi_comparison.md, day09/lab/reports/group_report.md, và template báo cáo cá nhân trong day09/lab/reports/individual/template.md.

Tôi không implement worker trực tiếp, nhưng tôi là điểm nối giữa phần kỹ thuật và phần chấm điểm. Khi các owner gửi kết quả, tôi đối chiếu ngược từ nội dung báo cáo về trace để đảm bảo mọi nhận định đều có căn cứ. Ví dụ, khi ghi “policy worker có MCP call”, tôi dùng đúng trace run_20260414_155152 (q07) và run_20260414_155333 (q15), thay vì chỉ mô tả định tính. Vai trò này liên quan đến toàn nhóm vì nếu report không khớp code/trace thì vẫn bị trừ điểm dù hệ thống chạy được.

**Module/file tôi chịu trách nhiệm:**
- File chính: docs/*.md và reports/group_report.md
- Công việc chính: tổng hợp bằng chứng từ trace/code, điền docs đúng rubric, kiểm nội dung khớp đóng góp

---

## 2. Tôi đã ra một quyết định kỹ thuật gì?

**Quyết định:** Tôi chọn cách viết tài liệu theo mô hình evidence-first (mỗi kết luận đều kèm trace hoặc metric) thay vì viết theo dạng narrative thuần.

Lý do là Day 09 chấm mạnh vào routing visibility, trace quality, và phần so sánh có số liệu. Nếu chỉ viết “nhóm làm tốt” hoặc “route ổn” mà thiếu run id, confidence, latency thì người chấm không thể xác minh độc lập. Tôi cân nhắc hai hướng: (1) kể theo timeline sprint cho dễ đọc; (2) trình bày theo claim + evidence để kiểm chứng nhanh. Tôi chọn hướng (2) vì mục tiêu của báo cáo là chứng minh quyết định kỹ thuật, không chỉ tóm tắt quá trình làm việc.

Trade-off là tốn thêm thời gian đọc trace và đối chiếu chéo giữa các file. Bù lại, báo cáo nhất quán và giảm rủi ro mâu thuẫn giữa phần mô tả và kết quả chạy thật. Tác động rõ nhất là các file docs đã chuyển từ placeholder sang số liệu cụ thể như routing distribution 20/36 và 16/36, mcp_usage_rate 44%, hitl_rate 5%.

**Bằng chứng từ trace/code:**

```text
run_20260414_154651 (q06): retrieval route, confidence 0.70, latency 7523ms
run_20260414_155152 (q07): policy route + MCP search_kb
run_20260414_154718 (q09): hitl_triggered = true
```

---

## 3. Tôi đã sửa một lỗi gì?

**Lỗi:** Bộ tài liệu nộp ban đầu chưa đạt chuẩn Sprint 4 vì còn dạng template, thiếu số liệu thật và thiếu liên kết với trace thực tế.

**Symptom:** Các mục trong routing_decisions.md và single_vs_multi_comparison.md có nhiều chỗ để trống; group_report.md chưa phản ánh rõ bằng chứng định lượng. Nếu nộp ở trạng thái đó, nhóm dễ mất điểm ở tiêu chí “ít nhất 3 quyết định routing thực tế” và “ít nhất 2 metrics so sánh thực tế”.

**Root cause:** Team ưu tiên code trước nên khâu tài liệu bị dồn về cuối, chưa có bước chốt evidence đầu vào ngay từ đầu Sprint 4. Ngoài ra, do có nhiều lần chạy trace, việc chọn nhầm run hoặc trộn số liệu giữa các lần chạy rất dễ xảy ra nếu không thống nhất nguồn.

**Cách sửa:**
1. Chốt một nguồn metric duy nhất từ day09/lab/artifacts/eval_report.json.
2. Chọn trace đại diện theo 3 nhóm retrieval / policy+MCP / HITL để tránh mô tả lệch.
3. Điền lại hai file docs theo đúng rubric, đưa route_reason, workers_called, confidence, latency vào từng phần cần chứng minh.
4. Cập nhật group_report.md để đồng bộ phân công, bằng chứng, và kết luận kỹ thuật.

**Bằng chứng trước/sau:**
- Trước: file chủ yếu là placeholder.
- Sau: nội dung có trace id cụ thể, có số liệu định lượng, và kết luận bám sát output thật.

---

## 4. Tôi tự đánh giá đóng góp của mình

Điểm tôi làm tốt nhất là chuẩn hóa tài liệu theo cùng một logic kiểm chứng, giúp phần nộp cuối không bị rời rạc giữa code và report. Tôi cũng chủ động rà chéo các claim quan trọng (route đúng, có MCP, có HITL) để tránh nói quá so với trace. Điểm tôi còn yếu là bắt đầu chuẩn hóa hơi muộn; nếu triển khai checklist evidence sớm hơn thì nhóm sẽ bớt áp lực ở giai đoạn chốt bài.

Nhóm phụ thuộc vào tôi ở bước đóng gói kết quả kỹ thuật thành hồ sơ chấm điểm. Nếu bước này chưa xong, phần nộp cuối sẽ thiếu tính nhất quán. Ngược lại, tôi phụ thuộc vào owner của orchestrator, retrieval, policy, MCP, eval để nhận dữ liệu trace chính xác và cập nhật thay đổi đúng thời điểm.

---

## 5. Nếu có thêm 2 giờ, tôi sẽ làm gì?

Tôi sẽ thêm một bảng evidence checklist theo dạng: tiêu chí chấm -> file chứng minh -> trace id -> dòng dữ liệu then chốt. Tôi chọn đúng một cải tiến này vì trace q02 cho thấy chỉ một lỗi route nhỏ cũng có thể làm sai kết luận chung, và checklist sẽ giúp phát hiện mismatch sớm trước khi khóa báo cáo.
