# Báo Cáo Nhóm — Lab Day 10: Data Pipeline & Data Observability

**Tên nhóm:** ___________  
**Thành viên:**
| Tên | Vai trò (Day 10) | Email |
|-----|------------------|-------|
| ___ | Ingestion / Raw Owner | ___ |
| ___ | Cleaning & Quality Owner | ___ |
| ___ | Embed & Idempotency Owner | ___ |
| ___ | Monitoring / Docs Owner | ___ |

**Ngày nộp:** ___________  
**Repo:** ___________  
**Độ dài khuyến nghị:** 600–1000 từ

---

> **Nộp tại:** `reports/group_report.md`  
> **Deadline commit:** xem `SCORING.md` (code/trace sớm; report có thể muộn hơn nếu được phép).  
> Phải có **run_id**, **đường dẫn artifact**, và **bằng chứng before/after** (CSV eval hoặc screenshot).

---

## 1. Pipeline tổng quan (150–200 từ)

> Nguồn raw là gì (CSV mẫu / export thật)? Chuỗi lệnh chạy end-to-end? `run_id` lấy ở đâu trong log?

**Tóm tắt luồng:**

_________________

**Lệnh chạy một dòng (copy từ README thực tế của nhóm):**

_________________

---

## 2. Cleaning & expectation (150–200 từ)

> Baseline đã có nhiều rule (allowlist, ngày ISO, HR stale, refund, dedupe…). Nhóm thêm **≥3 rule mới** + **≥2 expectation mới**. Khai báo expectation nào **halt**.

Nhóm đã thiết lập một hệ thống phòng thủ hai lớp chặt chẽ. Ngoài các quy tắc baseline (dedupe, ngày ISO, fix 14 ngày hoàn tiền), nhóm đã mở rộng thêm 3 rule Cleaning và 2 rule Expectation tập trung vào bảo mật và tính hợp lý của dữ liệu. Điểm mấu chốt là việc cấu hình Halt cho các lỗi nghiêm trọng như rò rỉ thông tin nhạy cảm.

Trong quá trình thực hiện, nhóm đã cố tình để lọt lỗi qua tầng Cleaning để kiểm tra tính hiệu quả của tầng Validation. Kết quả cho thấy khi Expectation phát hiện mật khẩu (Admin@123) hoặc ngày hiệu lực phi thực tế (2029), pipeline lập tức dừng lại (Halt), ngăn chặn việc phát tán dữ liệu lỗi vào Vector Database. Sau đó, nhóm đã cập nhật bộ lọc Cleaning để tự động "đẩy" các lỗi này vào khu cách ly (Quarantine) giúp pipeline vận hành thông suốt nhưng vẫn đảm bảo an toàn.
### 2a. Bảng metric_impact (bắt buộc — chống trivial)

| Rule / Expectation mới (tên ngắn) | Trước (số liệu) | Sau / khi inject (số liệu) | Chứng cứ (log / CSV / commit) |
|:-----------------------------------|:----------------:|:---------------------------:|:-------------------------------|
| **Rule Clean:** Lọc từ khóa nhạy cảm | `quarantine: 4` | `quarantine: 7`(tăng 3)| File `quarantine_fail_test.csv` có lý do `security_risk` |
| **Rule Clean:** Giới hạn năm 2027 | `quarantine: 4` | `quarantine: 8`(tăng 1) | Dòng 12 trong `quarantine_fail_test.csv` bị loại |
| **Expectation:** `no_sensitive_info` | `OK` (0 lỗi) | `FAIL` (2 lỗi - **Halt**) | Log: `security_violations=2` tại `run_id=fail_test` |
| **Expectation:** `no_far_future_date` | `OK` (0 lỗi) | `FAIL` (1 lỗi - **Halt**) | Log: `future_date_violations=1` tại `run_id=fail_test` |

**Rule chính (baseline + mở rộng):**

Baseline: Allowlist doc_id, chuẩn hóa ngày ISO, loại trùng nội dung, sửa 14 ngày thành 7 ngày cho refund policy.

Mở rộng 1: Tự động lọc các bản ghi chứa mật khẩu mặc định hoặc token nhạy cảm.

Mở rộng 2: Chặn các bản ghi có effective_date vượt quá năm 2027 (lỗi nhập liệu tương lai).

**Ví dụ 1 lần expectation fail (nếu có) và cách xử lý:**

Khi chạy run-id=fail_test, pipeline bị dừng tại bước Validation do phát hiện dòng số 11 chứa mật khẩu quản trị. Hệ thống báo lỗi: expectation[no_sensitive_info] FAIL (halt).
Cách xử lý: Nhóm không sửa file raw mà cập nhật cleaning_rules.py để chủ động bắt lỗi này và đẩy vào quarantine với lý do security_risk_detected. Sau khi cập nhật, pipeline chạy thành công (Exit 0) và dữ liệu bẩn đã bị loại bỏ an toàn.
_________________

---

## 3. Before / after ảnh hưởng retrieval hoặc agent (200–250 từ)

> Bắt buộc: inject corruption (Sprint 3) — mô tả + dẫn `artifacts/eval/…` hoặc log.

**Kịch bản inject:**

_________________

**Kết quả định lượng (từ CSV / bảng):**

_________________

---

## 4. Freshness & monitoring (100–150 từ)

> SLA bạn chọn, ý nghĩa PASS/WARN/FAIL trên manifest mẫu.

_________________

---

## 5. Liên hệ Day 09 (50–100 từ)

> Dữ liệu sau embed có phục vụ lại multi-agent Day 09 không? Nếu có, mô tả tích hợp; nếu không, giải thích vì sao tách collection.

_________________

---

## 6. Rủi ro còn lại & việc chưa làm

- …
