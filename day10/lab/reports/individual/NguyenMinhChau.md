# Báo Cáo Cá Nhân - Lab Day 10: Data Pipeline & Observability

**Họ và tên:** Nguyễn Minh Châu  
**Vai trò:** Docs Owner  
**Ngày nộp:** 15/04/2026  
**Độ dài yêu cầu:** **400-650 từ**

---

## 1. Tôi phụ trách phần nào?

Tôi phụ trách phần tài liệu hóa để biến kết quả kỹ thuật của nhóm thành các mô tả có thể kiểm tra lại được. Các file tôi tập trung hoàn thiện là `docs/pipeline_architecture.md`, `docs/quality_report.md`, `docs/data_contract.md` và phối hợp tổng hợp nội dung cho `reports/group_report.md`. Tôi không trực tiếp viết logic clean hay embed, nhưng tôi phải đọc `etl_pipeline.py`, manifest, quarantine CSV và file eval để mô tả đúng boundary giữa ingest, transform, quality gate, embed và monitoring.

Tôi kết nối với các bạn còn lại theo hướng lấy bằng chứng thật từ artifact rồi chuẩn hóa thành tài liệu. Khương An cung cấp bối cảnh ingest/raw, Triển và Yến cung cấp rule clean cùng expectation, Minh Việt cung cấp phần idempotency và embed. Tôi dùng các thông tin đó để viết lại theo ngôn ngữ kiến trúc và observability, tránh mô tả chung chung.

**Bằng chứng (commit / comment trong code):** 2a9a65680a01b1007e6c2e7fdf0752631469b834

---

## 2. Một quyết định kỹ thuật

Quyết định kỹ thuật tôi thấy quan trọng nhất và đã ghi rõ trong `docs/pipeline_architecture.md` là chọn cách embed theo mô hình "snapshot publish mới nhất" thay vì cộng dồn mọi phiên bản dữ liệu vào vector store. Cụ thể, pipeline dùng `chunk_id` làm khóa ổn định, sau đó `upsert` vào Chroma và xóa các `prev_ids` không còn nằm trong cleaned snapshot hiện tại. Tôi chọn nhấn mạnh quyết định này trong tài liệu vì nó giải thích được vì sao rerun không sinh duplicate vector, đồng thời vì sao retrieval sau khi fix có thể sạch hơn ngay lập tức.

Theo tôi, đây là quyết định đúng cho lab Day 10 vì mục tiêu chính là phục vụ retrieval hiện tại của Day 09, không phải lưu kho lịch sử toàn bộ corpus. Trade-off là nhóm chưa có audit sâu theo từng version trong chính Chroma collection, nhưng đổi lại boundary publish rất rõ: chỉ cleaned snapshot mới nhất mới được phục vụ cho agent.

---

## 3. Một lỗi hoặc anomaly đã xử lý

Anomaly tôi theo dõi kỹ nhất là trường hợp pipeline vẫn trả về top-k có dấu vết stale refund policy dù câu trả lời bề mặt nhìn có vẻ đúng. Tín hiệu phát hiện không nằm ở top-1 mà nằm ở metric `hits_forbidden`. Trong `docs/quality_report.md`, run `sprint3-inject-bad` cho thấy expectation `refund_no_stale_14d_window` bị fail với `violations=1`, nhưng do chạy với `--skip-validate` nên dữ liệu xấu vẫn được embed để mô phỏng lỗi có chủ đích.

Điểm tôi xử lý ở góc độ tài liệu là nối được triệu chứng với bằng chứng kỹ thuật. Manifest `manifest_sprint3-inject-bad.json` ghi `no_refund_fix=true`, `skipped_validate=true`, còn eval `after_inject_bad.csv` cho `q_refund_window` có `contains_expected=yes` nhưng `hits_forbidden=yes`. Nghĩa là retrieval vẫn kéo theo context bẩn. Sau khi nhóm chạy lại `python etl_pipeline.py run --run-id sprint3-after-fix`, file `after_fix.csv` chuyển `hits_forbidden` từ `yes` sang `no`. Tôi dùng chính chuỗi bằng chứng này để viết phần before/after và giải thích vì sao observability phải nhìn cả top-k chứ không chỉ nhìn câu trả lời cuối.

---

## 4. Bằng chứng trước / sau

Tôi dùng cặp run `sprint3-inject-bad` và `sprint3-after-fix` làm bằng chứng chính. Hai dòng quan trọng từ eval là:

`q_refund_window,...,policy_refund_v4,...,contains_expected=yes,hits_forbidden=yes,...,3` trong `artifacts/eval/after_inject_bad.csv`

`q_refund_window,...,policy_refund_v4,...,contains_expected=yes,hits_forbidden=no,...,3` trong `artifacts/eval/after_fix.csv`

Tôi cũng đối chiếu với manifest:

- `manifest_sprint3-inject-bad.json`: `no_refund_fix=true`, `skipped_validate=true`
- `manifest_sprint3-after-fix.json`: `no_refund_fix=false`, `skipped_validate=false`

Theo tôi, đây là bằng chứng rõ nhất cho vai trò của Day 10: cùng một câu hỏi retrieval, câu trả lời có thể vẫn "đúng bề mặt", nhưng context phía sau chỉ thật sự sạch sau khi pipeline clean và publish lại đúng snapshot.

---

## 5. Cải tiến tiếp theo

Nếu có thêm 2 giờ, tôi muốn bổ sung một bảng lineage ngắn trong manifest hoặc report để map trực tiếp `run_id -> cleaned_csv -> quarantine_csv -> eval file`. Việc này sẽ giúp tài liệu incident và peer review nhanh hơn, vì người đọc không phải tự lần từng thư mục mới nối được chuỗi bằng chứng.
