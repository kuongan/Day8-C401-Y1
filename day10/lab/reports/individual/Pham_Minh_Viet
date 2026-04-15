# Báo Cáo Cá Nhân — Lab Day 10: Data Pipeline & Observability

**Họ và tên:** Phạm Minh Việt  
**Vai trò:** Monitoring  
**Ngày nộp:** 15/4/2026
**Độ dài yêu cầu:** 400–650 từ

---

## 1. Tôi phụ trách phần nào? (80–120 từ)

**File / module:**

- `monitoring/freshness_check.py`
- `docs/runbook.md`

Tôi phụ trách phần monitoring cho pipeline, cụ thể là kiểm tra freshness từ manifest để biết dữ liệu có còn “mới” theo ngưỡng hay không. Tôi cũng tham gia định nghĩa ba mức trạng thái `PASS / WARN / FAIL` để hệ thống có phản hồi rõ ràng khi nguồn dữ liệu chậm hoặc bị trễ. Ngoài code, tôi viết runbook xử lý lỗi trong `docs/runbook.md` để các thành viên khác có thể tra cứu nhanh khi freshness check báo bất thường.

**Kết nối với thành viên khác:**

Tôi nhận manifest từ phần ingestion/cleaning của nhóm và trả kết quả để nhóm evaluation/ops biết run nào cần kiểm tra lại.

**Bằng chứng (commit / comment trong code):**

`monitoring/freshness_check.py` và `docs/runbook.md` được cập nhật trong cùng nhánh làm việc của tôi.

---

## 2. Một quyết định kỹ thuật (100–150 từ)

Tôi chọn thiết kế freshness check dựa trên manifest thay vì đọc trực tiếp dữ liệu thô. Lý do là manifest có sẵn metadata như timestamp, số bản ghi, và run_id, nên kiểm tra nhanh hơn và ổn định hơn khi pipeline lớn dần. Tôi định nghĩa `PASS / WARN / FAIL` theo ngưỡng lệch thời gian: nếu độ trễ nhỏ hơn ngưỡng thì `PASS`, vượt ngưỡng cảnh báo thì `WARN`, và vượt ngưỡng nghiêm trọng thì `FAIL`. Cách này giúp tách rõ mức độ ảnh hưởng thay vì chỉ trả về “đúng/sai”. Tôi cũng ghi rõ cách diễn giải trong runbook để cùng một tín hiệu freshness có thể được xử lý nhất quán bởi cả người vận hành lẫn người phát triển.

---

## 3. Một lỗi hoặc anomaly đã xử lý (100–150 từ)

Tôi đã xử lý một anomaly khi manifest vẫn được tạo nhưng timestamp của run bị trễ hơn bình thường, khiến freshness check có nguy cơ đánh dấu sai nếu chỉ nhìn vào thời điểm file xuất hiện. Khi kiểm tra log, tôi thấy tín hiệu phát hiện đến từ bước đọc manifest chứ không phải từ dữ liệu đầu ra. Tôi sửa logic để ưu tiên timestamp trong manifest và so sánh với ngưỡng freshness đã định, đồng thời ghi rõ cách phản ứng trong runbook. Sau khi sửa, pipeline không còn báo nhầm `PASS` cho một run bị chậm.  
**Ví dụ tín hiệu liên quan:** `run_id=<REPLACE_ME>`, file manifest `manifest.json`, log freshness: `status=WARN` khi độ trễ vượt ngưỡng cảnh báo.

---

## 4. Bằng chứng trước / sau (80–120 từ)

Trước khi sửa, một run có manifest hợp lệ nhưng freshness vượt ngưỡng vẫn chưa được gắn cảnh báo rõ ràng. Sau khi cập nhật kiểm tra, cùng run đó chuyển sang trạng thái đúng theo rule.

- `run_id=<REPLACE_ME>` — trước: `freshness_status=PASS`, sau: `freshness_status=WARN`
- `run_id=<REPLACE_ME>` — trước: `lag_minutes=<REPLACE_ME>`, sau: `lag_minutes=<REPLACE_ME>`

Hai dòng trên phản ánh thay đổi trong cách đọc manifest và phân loại `PASS / WARN / FAIL`, giúp nhóm nhận biết sớm dữ liệu chậm thay vì chỉ phát hiện ở bước downstream.

---

## 5. Cải tiến tiếp theo (40–80 từ)

Nếu có thêm 2 giờ, tôi sẽ thêm một bảng summary trong runbook hoặc script để in ra reason code cụ thể cho từng trạng thái, ví dụ `late_manifest`, `missing_timestamp`, hoặc `stale_run`. Việc này sẽ giúp debug nhanh hơn khi freshness check thất bại và giảm thời gian tra cứu thủ công khi pipeline có nhiều run liên tiếp.

---
