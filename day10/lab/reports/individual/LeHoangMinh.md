# Báo Cáo Cá Nhân — Lab Day 10: Data Pipeline & Observability

**Họ và tên:** Le Hoàng Minh  
**Vai trò:** Sprint 3 (Inject corruption + before/after eval) và chạy Grading Question
**Ngày nộp:** 2026-04-15

---

## 1. Tôi phụ trách phần nào?

Trong Day 10, tôi phụ trách 2 việc chính: (1) thực thi Sprint 3 theo hướng inject có chủ đích để tạo tình huống dữ liệu xấu, sau đó phục hồi pipeline sạch và so sánh retrieval; (2) chạy bộ câu hỏi grading để tạo file kết quả JSONL phục vụ quick check. Các file tôi làm việc trực tiếp gồm `etl_pipeline.py`, `eval_retrieval.py`, `grading_run.py` và các artifact trong `artifacts/eval`, `artifacts/logs`, `artifacts/manifests`.

Tôi phối hợp với bạn phụ trách cleaning/quality để xác nhận logic expectation halt, sau đó tôi là người chạy full luồng Sprint 3 từ đầu đến cuối và tổng hợp bằng chứng vào báo cáo chất lượng.

---

## 2. Một quyết định kỹ thuật

Quyết định kỹ thuật quan trọng nhất của tôi là tách rõ 2 luồng run trong Sprint 3:

- Luồng inject-bad: `--no-refund-fix --skip-validate` để chủ động đưa dữ liệu stale vào index và quan sát hệ quả retrieval.
- Luồng after-fix: chạy lại pipeline bình thường không inject để khôi phục index boundary.

Lý do tôi chọn cách này là để chứng minh quan hệ nhân-quả một cách rõ ràng: thay đổi một cơ chế clean quan trọng (refund 14->7) sẽ ảnh hưởng trực tiếp đến chất lượng top-k context. Kết quả lấy được không chỉ ở log expectation mà còn xuất hiện trong file eval qua cột `hits_forbidden`, đúng tinh thần observability của đề bài. Cũng từ đó, tôi để ý quy ước run_id có nghĩa (`sprint3-inject-bad`, `sprint3-after-fix`) để team truy vết nhanh từ manifest sang eval.

---

## 3. Một lỗi/anomaly đã xử lý

Anomaly tôi gặp là file eval inject lần đầu không thể hiện xấu đi như kỳ vọng. Triệu chứng: file eval inject và file eval sau fix có kết quả quá giống nhau, không phục vụ được thông điệp before/after. Tôi xử lý bằng cách rerun đúng thứ tự và đúng option theo kịch bản Sprint 3:

1. Chạy inject run trước với `--no-refund-fix --skip-validate`.
2. Chạy eval ngay sau inject để đóng băng state xấu vào CSV.
3. Chạy clean run sau đó.
4. Chạy eval lần 2 cho state đã fix.

Sau khi làm lại đúng quy trình, log inject có `refund_no_stale_14d_window FAIL (violations=1)` trong `run_sprint3-inject-bad.log`, và kết quả eval đã tách bạch rõ ràng.

---

## 4. Bằng chứng trước/sau

Bằng chứng từ 2 file:

- `artifacts/eval/after_inject_bad.csv`
- `artifacts/eval/after_fix.csv`

Với câu `q_refund_window`:

- Trước fix (run_id=`sprint3-inject-bad`): `contains_expected=yes`, `hits_forbidden=yes`.
- Sau fix (run_id=`sprint3-after-fix`): `contains_expected=yes`, `hits_forbidden=no`.

Đây là bằng chứng định lượng cho thấy retrieval tốt hơn sau khi fix pipeline.

Phần grading tôi phụ trách đã chạy ra `artifacts/eval/grading_run.jsonl` với 3 câu `gq_d10_01..03` đều đạt: `contains_expected=true`, `hits_forbidden=false`, và với `gq_d10_03` thì `top1_doc_matches=true`.

---

## 5. Cải tiến tiếp theo

Nếu có thêm 2 giờ, tôi sẽ bổ sung một script so sánh tự động giữa 2 file eval (inject vs fix) để sinh ra bảng delta theo từng question_id, tự động highlight cột thay đổi như `hits_forbidden` và `top1_doc_id`. Như vậy team có thể tạo báo cáo Sprint 3 nhanh hơn, giảm sai sót khi copy số liệu thủ công.
