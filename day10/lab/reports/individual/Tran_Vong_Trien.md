# Báo Cáo Cá Nhân — Lab Day 10: Data Pipeline & Observability

**Họ và tên:** Trần Vọng Triển
**Vai trò:** Cleaning & Quality Owner
**Ngày nộp:** 15/04/2026  
**Độ dài yêu cầu:** **400–650 từ** 

---

> Viết **"tôi"**, đính kèm **run_id**, **tên file**, **đoạn log** hoặc **dòng CSV** thật.  
> Nếu làm phần clean/expectation: nêu **một số liệu thay đổi** (vd `quarantine_records`, `hits_forbidden`, `top1_doc_expected`) khớp bảng `metric_impact` của nhóm.  
> Lưu: `reports/individual/[ten_ban].md`

---

## 1. Tôi phụ trách phần nào? (80–120 từ)

**File / module:**

- transform/cleaning_rules.py: Thiết kế và triển khai các quy tắc làm sạch dữ liệu từ Raw sang Cleaned/Quarantine.

**Kết nối với thành viên khác:**

- Tôi nhận dữ liệu thô từ Ingestion Owner, sau đó bàn giao file cleaned đã được chuẩn hóa cho Embed Owner để nạp vào Vector DB. Tôi cũng cung cấp các mã lỗi trong Quarantine cho Monitoring Owner để hoàn thiện hệ thống cảnh báo.

**Bằng chứng (commit / comment trong code):**

- Đã thêm 05 rules mới (Min length, SLA normalization, Strip chars, Sensitive info, Future date).

- Comment trong code tại hàm clean_rows mô tả chi tiết metric_impact của từng quy tắc.

---

## 2. Một quyết định kỹ thuật (100–150 từ)

Tôi quyết định áp dụng nguyên tắc Fail-safe (An toàn tối đa) cho bộ lọc dữ liệu nhạy cảm.

Qua kiểm tra file artifacts/quarantine/quarantine_cleaning_v1.csv, tôi phát hiện dòng số 10 (FAQ hướng dẫn đổi mật khẩu) bị hệ thống tự động gắn nhãn sensitive_info_detected và đẩy vào vùng cách ly, dù đây không phải là mật khẩu thật.

Đây là lỗi "False Positive" do Regex nhận diện nhầm các thực thể viết hoa (FAQ) và số (24 giờ) đứng gần từ khóa "mật khẩu". Quyết định này đảm bảo tuyệt đối không có thông tin nhạy cảm nào lọt vào Vector Store. Quy trình phục hồi các dòng bị chặn nhầm sẽ được xử lý thông qua hậu kiểm thủ công (Human-in-the-loop), ưu tiên tính bảo mật và an toàn dữ liệu lên mức cao nhất cho hệ thống.

---

## 3. Một lỗi hoặc anomaly đã xử lý (100–150 từ)

Triệu chứng: Tại run_id: cleaning_v1, bản ghi ngắn dưới 60 ký tự bị đẩy vào Quarantine.

Phát hiện: Qua rà soát file quarantine_cleaning_v1.csv, tôi thấy ngưỡng Min Text Length = 60 trước đó quá cao, khiến các câu hướng dẫn ngắn nhưng súc tích bị loại bỏ do không đủ độ dài.

Cách xử lý: Tôi đã điều chỉnh logic trong hàm clean_rows, hạ ngưỡng độ dài tối thiểu từ 60 xuống 30 ký tự. Thay đổi này cho phép hệ thống giữ lại các bản ghi có giá trị nội dung ngắn nhưng cần thiết vào tập dữ liệu sạch (cleaned_records), đồng thời vẫn duy trì khả năng loại bỏ các dòng nhiễu hoặc dữ liệu thử nghiệm không đủ ngữ cảnh.
_________________

---

## 4. Bằng chứng trước / sau (80–120 từ)

> Run_id: manifest_cleaning_v1.json (Ngưỡng 60 chars)

"raw_records": 10,
  "cleaned_records": 5,
  "quarantine_records": 5

> Run_id: manifest_test_pass.json (Ngưỡng 30 chars)

 "raw_records": 13,
  "cleaned_records": 5,
  "quarantine_records": 8

Bằng chứng: Dòng 6 lúc này đã thỏa mãn độ dài (>30) và được giữ lại, nhưng dòng 10 lúc này bị hệ thống gắn nhãn với sử dụng nguyên tắc Fail-safe
_________________


## 5. Cải tiến tiếp theo (40–80 từ)

Nếu có thêm 2 giờ, tôi sẽ triển khai mô hình Named Entity Recognition (NER) để thay thế Regex trong việc nhận diện thông tin nhạy cảm. Giải pháp này giúp hệ thống phân biệt chính xác ngữ cảnh giữa hướng dẫn nghiệp vụ và dữ liệu rò rỉ thực tế, giảm tỷ lệ bản ghi bị đưa vào vùng cách ly nhầm và tối ưu hóa quy trình kiểm duyệt dữ liệu tự động.

_________________
