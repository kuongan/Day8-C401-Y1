# Báo Cáo Nhóm - Lab Day 10: Data Pipeline & Data Observability

**Tên nhóm:** X2  
**Thành viên:**
| Tên | Vai trò (Day 10) | Email |
|-----|------------------|-------|
| Nguyễn Trần Khương An | Ingestion / Raw Owner | 26ai.anntk@vinuni.edu.vn |
| Trần Vọng Triển | Cleaning | 26ai.trientv@vinuni.edu.vn |
| Phương Hoàng Yến | Quality Owner | 26ai.yenph@vinuni.edu.vn |
| Phạm Minh Việt | Embed & Idempotency Owner | 26ai.vietpm@vinuni.edu.vn |
| Lê Hoàng Minh | Docs Owner | 26ai.minhlh@vinu.edu.vn |
| Nguyễn Minh Châu | Docs Owner | 26ai.chaunm@vinuni.edu.vn |

**Ngày nộp:** 15/04/2026  
**Repo:** https://github.com/kuongan/Day8-C401-Y1.git  
**Độ dài khuyến nghị:** 600-1000 từ

---

## 1. Pipeline tổng quan

Nhóm dùng nguồn raw là file mẫu `data/raw/policy_export_dirty.csv`, mô phỏng export từ hệ CS + IT Helpdesk của cùng bài toán đã dùng ở Day 09. File này cố ý chứa nhiều lỗi cùng lúc như duplicate `chunk_text`, `doc_id` ngoài allowlist, thiếu `effective_date`, bản HR cũ, dữ liệu nhạy cảm và ngày hiệu lực phi thực tế. Luồng end-to-end của nhóm được triển khai trong `etl_pipeline.py` theo chuỗi `ingest -> clean -> validate -> embed -> manifest -> freshness`. Trong đó, `run_id` được tạo từ UTC timestamp hoặc truyền tay qua `--run-id`, rồi được ghi xuyên suốt vào log, cleaned CSV, quarantine CSV và manifest để có thể truy vết từ dữ liệu nguồn đến vector store.

Run chuẩn mà nhóm dùng làm baseline là `2026-04-15T06-53Z`, tương ứng manifest `artifacts/manifests/manifest_2026-04-15T06-53Z.json`. Run này cho thấy `raw_records=10`, `cleaned_records=6`, `quarantine_records=4`, `pipeline_status="OK"` và `embed_status="ok"`. Sau clean, chỉ cleaned snapshot mới được embed vào collection `day10_kb`; phần bị loại được giữ trong `artifacts/quarantine/` thay vì xóa âm thầm. Điều này khác với Day 09 ở chỗ Day 09 tập trung vào lớp orchestration và retrieval trên corpus đã có sẵn, còn Day 10 bổ sung lớp kiểm soát dữ liệu trước khi agent truy vấn.

Lệnh chạy một dòng nhóm dùng theo README là:

`python etl_pipeline.py run`

Để kiểm tra freshness theo manifest vừa tạo, nhóm dùng:

`python etl_pipeline.py freshness --manifest artifacts/manifests/manifest_<run-id>.json`

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

---

## 3. Before / after ảnh hưởng retrieval hoặc agent

Kịch bản inject của nhóm tập trung vào lỗi stale refund policy vì đây là case dễ thấy nhất ở tầng retrieval và cũng là đúng kiểu lỗi sẽ làm Supervisor/Worker ở Day 09 dùng sai evidence. Nhóm chạy:

`python etl_pipeline.py run --run-id sprint3-inject-bad --no-refund-fix --skip-validate`

Sau đó eval bằng:

`python eval_retrieval.py --out artifacts/eval/after_inject_bad.csv`

Mục tiêu của inject là tạo một tình huống mà câu trả lời nhìn vẫn có vẻ đúng, nhưng top-k context vẫn còn chunk stale. Đây là lý do nhóm dùng metric `hits_forbidden`, không chỉ nhìn `top1_doc_id`. Với góc nhìn Day 09, nếu retrieval worker kéo nhầm stale chunk thì synthesis worker vẫn có thể tạo ra câu trả lời nghe hợp lý nhưng dựa trên context sai version. Sau khi chạy lại flow chuẩn:

`python etl_pipeline.py run --run-id sprint3-after-fix`

và eval ra `artifacts/eval/after_fix.csv`, nhóm thấy chất lượng retrieval được cải thiện đúng theo kỳ vọng.

Kết quả định lượng rõ nhất là câu `q_refund_window`:

- Trong `artifacts/eval/after_inject_bad.csv`: `top1_doc_id=policy_refund_v4`, `contains_expected=yes`, nhưng `hits_forbidden=yes`, `top_k_used=3`.
- Trong `artifacts/eval/after_fix.csv`: `top1_doc_id=policy_refund_v4`, `contains_expected=yes`, `hits_forbidden=no`, `top_k_used=3`.

Điểm quan trọng là `contains_expected` đều bằng `yes` ở cả hai run, nên nếu chỉ nhìn answer bề mặt thì nhóm có thể tưởng pipeline vẫn ổn. Chính `hits_forbidden: yes -> no` mới chứng minh được observability đang phát hiện đúng lỗi context bẩn trong top-k. Với câu `q_leave_version`, cả hai file eval đều cho `contains_expected=yes`, `hits_forbidden=no`, `top1_doc_expected=yes`, cho thấy fix refund không làm hồi quy case HR hiện hành. Đây cũng là bằng chứng cho thấy Day 10 không chỉ sửa lỗi cục bộ mà còn giúp tầng agent phía sau ổn định hơn khi truy vấn policy hiện hành.

---

## 4. Freshness & monitoring

Freshness được đo ở mức publish theo `contracts/data_contract.yaml`, với `measured_at: publish` và `sla_hours: 24`. Script `monitoring/freshness_check.py` đọc trường `latest_exported_at` từ manifest, tính `age_hours`, rồi trả về `PASS` hoặc `FAIL`. Trong các run Sprint 3 mà nhóm dùng làm bằng chứng, cả `sprint3-inject-bad` và `sprint3-after-fix` đều cho `freshness_check=FAIL` vì `latest_exported_at=2026-04-10T08:00:00`, cũ hơn nhiều so với SLA 24 giờ. Theo `docs/quality_report.md`, tuổi dữ liệu quan sát được là khoảng `120.897` và `120.908` giờ.

Nhóm xem đây là tín hiệu vận hành hợp lệ chứ không phải lỗi của logic retrieval. Nghĩa là publish boundary vẫn hoạt động, nhưng snapshot upstream đang stale. PASS/WARN/FAIL trong bối cảnh này được hiểu như sau: `PASS` khi dữ liệu còn trong SLA, `FAIL` khi vượt SLA, còn `WARN` dành cho tình huống manifest thiếu timestamp hoặc timestamp không parse được. Từ góc nhìn Day 09, freshness là lớp bảo vệ trước khi đổ lỗi cho supervisor, routing hay prompt của synthesis worker.

---

## 5. Liên hệ Day 09

Day 10 phục vụ trực tiếp cho Day 09 ở tầng dữ liệu. Hai lab dùng cùng bộ tài liệu nghiệp vụ nền như `policy_refund_v4.txt`, `sla_p1_2026.txt`, `hr_leave_policy.txt` và `it_helpdesk_faq.txt`. Trong Day 09, nhóm build index từ thư mục `data/docs/` sang collection `day09_docs`, rồi để retrieval worker và policy tool worker truy vấn trên đó. Day 10 bổ sung bước ingest từ raw export bẩn, clean và validate trước khi publish sang collection `day10_kb`.

Vì vậy, nếu nhìn xuyên suốt hai ngày lab thì Day 09 trả lời câu hỏi "agent điều phối ra sao", còn Day 10 trả lời câu hỏi "agent đang đọc dữ liệu sạch đến mức nào". Collection `day10_kb` nên được xem như snapshot sạch hơn để feed retrieval/agent Day 09 khi cần tránh stale chunk hoặc sai version policy. Đây cũng là lý do nhóm mô tả Day 10 như lớp data quality đứng trước orchestration layer.

---

## 6. Rủi ro còn lại & việc chưa làm

- `docs/runbook.md` mới ở mức khung tối thiểu, chưa điền đầy đủ quy trình xử lý incident theo từng bước thực tế.
- Freshness hiện chỉ đo ở boundary publish; nhóm chưa đo thêm boundary ingest như phần bonus trong rubric.
- `day09_docs` và `day10_kb` vẫn là hai collection tách nhau, nên nếu agent Day 09 chưa được nối sang `day10_kb` thì vẫn có nguy cơ truy vấn index cũ.
- Cơ chế versioning HR đang dùng cutoff cố định `2026-01-01`; nếu dữ liệu thật thay đổi thường xuyên hơn, nhóm cần đưa cutoff ra contract/env để giảm hard-code.
