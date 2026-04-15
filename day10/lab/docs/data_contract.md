# Data contract — Lab Day 10

> Bắt đầu từ `contracts/data_contract.yaml` — mở rộng và đồng bộ file này.

---

## 1. Nguồn dữ liệu (source map)

| Nguồn | Phương thức ingest | Failure mode chính | Metric / alert |
|-------|-------------------|-------------------|----------------|
| `data/raw/policy_export_dirty.csv` (export từ hệ CS + IT Helpdesk) | Batch CSV theo lần export, đọc bằng `csv.DictReader` trong `etl_pipeline.py` | Duplicate `chunk_text`, `doc_id` ngoài allowlist, thiếu/sai định dạng `effective_date`, stale HR version | `raw_records`, `cleaned_records`, `quarantine_records`; cảnh báo khi `quarantine_records/raw_records > 0.3` |
| `data/docs/policy_refund_v4.txt` (canonical policy refund) | Dùng làm chuẩn nghiệp vụ cho cleaning/expectation khi publish chunk refund | Stale window 14 ngày lọt qua cleaned hoặc bypass fix/refund | Expectation `refund_no_stale_14d_window` (halt), đếm `violations`; theo dõi `hits_forbidden` trên eval |
| `data/docs/hr_leave_policy.txt` (canonical HR leave) | Dùng làm chuẩn version policy HR khi clean dữ liệu lịch sử | Bản cũ (effective_date < 2026-01-01) hoặc nội dung còn marker 10 ngày phép năm | Quarantine reason `stale_hr_policy_effective_date`; expectation `hr_leave_no_stale_10d_annual` (halt) |

---

## 2. Schema cleaned

| Cột | Kiểu | Bắt buộc | Ghi chú |
|-----|------|----------|---------|
| chunk_id | string | Có | ID ổn định theo công thức hash `doc_id|chunk_text|seq` để hỗ trợ upsert idempotent vào Chroma |
| doc_id | string | Có | Thuộc allowlist: `policy_refund_v4`, `sla_p1_2026`, `it_helpdesk_faq`, `hr_leave_policy` |
| chunk_text | string | Có | Nội dung chunk sau clean; tối thiểu 8 ký tự theo expectation `chunk_min_length_8` |
| effective_date | date (YYYY-MM-DD) | Có | Chuẩn hoá từ raw (`dd/mm/yyyy` -> ISO); fail parse sẽ quarantine |
| exported_at | datetime | Có | Dấu thời gian export từ source, dùng để tính freshness theo SLA |

---

## 3. Quy tắc quarantine vs drop

Record vi phạm không bị xóa im lặng. Tất cả được ghi vào `artifacts/quarantine/quarantine_<run_id>.csv` kèm cột `reason` để truy vết.

- Quarantine (giữ lại để điều tra):
	- `unknown_doc_id`
	- `missing_effective_date`
	- `invalid_effective_date_format`
	- `stale_hr_policy_effective_date`
	- `missing_chunk_text`
	- `duplicate_chunk_text`
- Drop khỏi cleaned publish:
	- Mọi record đã bị quarantine sẽ không vào `artifacts/cleaned/cleaned_<run_id>.csv` và không được embed.

Quy trình approve merge lại:

- Ingestion Owner + Cleaning/Quality Owner review từng `reason` trong quarantine.
- Nếu là lỗi dữ liệu nguồn: sửa tại source và re-export raw.
- Nếu là false positive rule: cập nhật rule/contract có kiểm soát, rerun pipeline với `run_id` mới, đối chiếu chênh lệch metric trước/sau.

---

## 4. Phiên bản & canonical

Source of truth và versioning áp dụng cho lab này:

- Refund policy canonical: `data/docs/policy_refund_v4.txt` (`doc_id=policy_refund_v4`), cửa sổ hợp lệ là 7 ngày làm việc.
- HR leave canonical: `data/docs/hr_leave_policy.txt` với cutoff version `effective_date >= 2026-01-01`.
- Allowlist doc_id bắt buộc đồng bộ giữa:
	- `transform/cleaning_rules.py` (`ALLOWED_DOC_IDS`)
	- `contracts/data_contract.yaml` (`allowed_doc_ids`)

Nguyên tắc publish boundary:

- Chỉ dữ liệu đã clean + pass expectation halt mới được embed mặc định.
- Embed chạy idempotent theo `chunk_id` (upsert) và prune id không còn trong cleaned để tránh stale vector.
