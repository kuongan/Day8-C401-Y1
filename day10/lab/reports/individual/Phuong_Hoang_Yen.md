# Báo Cáo Cá Nhân — Lab Day 10: Data Pipeline & Observability

**Họ và tên:** Phương Hoàng yến
**Vai trò:** Validation (Quality)
**Ngày nộp:** 15/4/2026
**Độ dài yêu cầu:** **400–650 từ** (ngắn hơn Day 09 vì rubric slide cá nhân ~10% — vẫn phải đủ bằng chứng)

---

> Viết **"tôi"**, đính kèm **run_id**, **tên file**, **đoạn log** hoặc **dòng CSV** thật.  
> Nếu làm phần clean/expectation: nêu **một số liệu thay đổi** (vd `quarantine_records`, `hits_forbidden`, `top1_doc_expected`) khớp bảng `metric_impact` của nhóm.  
> Lưu: `reports/individual/[ten_ban].md`

---

## 1. Tôi phụ trách phần nào? (80–120 từ)

**File / module:**

- quality/expectations.py: Thiết lập các quy tắc kiểm soát chất lượng (Expectation Suite) để đảm bảo dữ liệu sạch trước khi nạp vào Vector Database.

- artifacts/quarantine/: Theo dõi và phân tích các bản ghi bị loại bỏ để phản hồi cho bước Cleaning.

**Kết nối với thành viên khác:**
Tôi đóng vai trò là "chốt chặn cuối cùng" sau bước Cleaning (Người 2). Tôi tiếp nhận danh sách cleaned_rows, thực hiện kiểm tra các ràng buộc về bảo mật và logic thời gian. Nếu phát hiện sai sót mà Người 2 bỏ lỡ, tôi sẽ ra lệnh HALT để bảo vệ tính toàn vẹn của hệ thống RAG, sau đó phối hợp để Người 2 cập nhật lại bộ lọc.
_________________

**Bằng chứng (commit / comment trong code):**
Trong file expectations.py, tôi đã thêm hàm run_expectations với các rule mới: no_sensitive_info (chặn mật khẩu) và no_unrealistic_future_dates (chặn ngày hiệu lực phi thực tế sau năm 2027).

Commit hash: 
87d3a898d3d50e1cfae7c89b0ab0d46753c9ef13
_________________

---

## 2. Một quyết định kỹ thuật (100–150 từ)

> VD: chọn halt vs warn, chiến lược idempotency, cách đo freshness, format quarantine.
Quyết định kỹ thuật quan trọng nhất của tôi là áp dụng chiến lược halt (dừng khẩn cấp) cho quy tắc kiểm tra thông tin nhạy cảm (no_sensitive_info). Thay vì chỉ sử dụng mức độ warn (cảnh báo), tôi chọn halt vì trong bối cảnh hệ thống RAG, việc để lọt mật khẩu (như dòng mật khẩu Admin@123 trong file dirty) vào Vector Database là một lỗ hổng bảo mật nghiêm trọng không thể đảo ngược dễ dàng nếu dữ liệu đã được embedding.

Quyết định này ép buộc toàn bộ Pipeline phải dừng lại ngay lập tức, buộc kỹ sư dữ liệu phải xử lý thủ công hoặc cập nhật bộ lọc Cleaning trước khi cho phép dữ liệu đi tiếp. Điều này đảm bảo tuân thủ nguyên tắc "Phòng thủ chiều sâu" (Defense in Depth), nơi Validation đóng vai trò kiểm soát độc lập với tầng Cleaning.
_________________

---

## 3. Một lỗi hoặc anomaly đã xử lý (100–150 từ)

> Mô tả triệu chứng → metric/check nào phát hiện → fix.
Triệu chứng: Khi chạy thử nghiệm với run_id=fail_test, hệ thống đã phát hiện ra các bản ghi "bẩn" lọt qua tầng lọc mặc định. Cụ thể, dòng số 11 chứa mật khẩu quản trị và dòng số 12 có ngày hiệu lực là năm 2029 (sai lệch hoàn toàn với thực tế năm 2026).

Metric phát hiện: Expectation no_sensitive_info báo FAIL với security_violations=2 và no_unrealistic_future_dates báo FAIL với future_date_violations=1. Tổng số quarantine_records lúc này là 4 bản ghi.

Xử lý: Tôi đã ghi nhận các lỗi này vào manifest_fail_test.json và yêu cầu Người 2 cập nhật cleaning_rules.py để bổ sung rule lọc từ khóa nhạy cảm và kiểm tra giới hạn năm. Sau khi fix, tôi chạy lại với run_id=pass_final, kết quả expectation[...] báo OK và hệ thống trả về exit 0.
_________________

---

## 4. Bằng chứng trước / sau (80–120 từ)

> Dán ngắn 2 dòng từ `before_after_eval.csv` hoặc tương đương; ghi rõ `run_id`.
Trước khi fix (run_id=fail_test):
Log hệ thống báo lỗi nghiêm trọng:
expectation[no_sensitive_info] FAIL (halt) :: security_violations=2
PIPELINE_HALT: expectation suite failed (halt).
Dữ liệu nhạy cảm: 11,it_helpdesk_faq,"...Mật khẩu mặc định là Admin@123..." bị chặn đứng.

Sau khi fix (run_id=pass_final):
Pipeline chạy thành công, dữ liệu bẩn được Người 2 chủ động đẩy vào khu cách ly:
quarantine_records=6 (tăng 2 bản ghi so với baseline do bắt thêm lỗi mật khẩu).
expectation[no_sensitive_info] OK (halt) :: security_violations=0
Dữ liệu trong artifacts/cleaned/cleaned_pass_final.csv hoàn toàn sạch và an toàn.
_________________

---

## 5. Cải tiến tiếp theo (40–80 từ)

> Nếu có thêm 2 giờ — một việc cụ thể (không chung chung).
Nếu có thêm 2 giờ, tôi sẽ triển khai Regex-based Validation thay vì chỉ kiểm tra từ khóa cố định. Cụ thể, tôi sẽ viết rule sử dụng biểu thức chính quy để tự động nhận diện các định dạng nhạy cảm phức tạp hơn như số thẻ tín dụng, mã định danh cá nhân (PII), hoặc các chuỗi Base64 nghi ngờ là mã khóa bí mật, giúp tầng Validation trở nên thông minh và bao quát hơn trước các lỗi nhập liệu ngẫu nhiên.
_________________
