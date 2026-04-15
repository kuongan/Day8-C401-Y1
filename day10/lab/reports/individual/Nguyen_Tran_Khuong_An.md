# Báo Cáo Cá Nhân — Lab Day 10: Data Pipeline & Observability

**Họ và tên:** Nguyễn Trần Khương An  (2A202600222)
**Vai trò:** Ingestion 
**Ngày nộp:** 15/4/2026  
**Độ dài yêu cầu:** **400–650 từ** 

---

> Viết **"tôi"**, đính kèm **run_id**, **tên file**, **đoạn log** hoặc **dòng CSV** thật.  
> Nếu làm phần clean/expectation: nêu **một số liệu thay đổi** (vd `quarantine_records`, `hits_forbidden`, `top1_doc_expected`) khớp bảng `metric_impact` của nhóm.  
> Lưu: `reports/individual/[ten_ban].md`

---

## 1. Tôi phụ trách phần nào? (80–120 từ)

**File / module:**

- `day10/lab/etl_pipeline.py`
- `day10/lab/contracts/data_contract.yaml`
- Các artifacts chạy thử: `day10/lab/artifacts/cleaned/cleaned_sprint1.csv`, `day10/lab/artifacts/quarantine/quarantine_sprint1.csv`, `day10/lab/artifacts/manifests/manifest_sprint1.json`

**Kết nối với thành viên khác:**

Tôi phối hợp với bạn phụ trách quality/eval để thống nhất các số liệu quan sát (cleaned/quarantine) và trạng thái pipeline cần được ghi vào manifest. Tôi cũng trao đổi với bạn phụ trách embedding để đảm bảo khi pipeline bị halt thì bước embed không chạy, tránh ghi dữ liệu sai vào vector store.

**Bằng chứng (commit / comment trong code):**

Commit `a7c6524` (update day 10 sprint 1) và các thay đổi trong `etl_pipeline.py`/`data_contract.yaml`.

---

## 2. Một quyết định kỹ thuật (100–150 từ)

> VD: chọn halt vs warn, chiến lược idempotency, cách đo freshness, format quarantine.

Tôi quyết định tách rõ trạng thái `pipeline_status` và `embed_status` trong manifest thay vì chỉ dựa vào exit code. Lý do: ở sprint 1, expectation có thể fail và pipeline phải halt để đảm bảo dữ liệu sạch, nhưng đội embedding vẫn cần biết lý do không có vector mới. Vì vậy tôi thêm `pipeline_status: HALT|OK` và `embed_status: ok|failed|skipped` để quan sát được cả hai pha. Đồng thời tôi chỉnh logic: khi `halt` và không `--skip-validate`, embed bị bỏ qua; khi `--skip-validate` (demo) thì vẫn embed nhưng ghi rõ trạng thái. Quyết định này giúp dễ truy vết lỗi, nhất là khi chạy nhiều `run_id` khác nhau.

---

## 3. Một lỗi hoặc anomaly đã xử lý (100–150 từ)

> Mô tả triệu chứng → metric/check nào phát hiện → fix.

Triệu chứng là pipeline bị fail expectation nhưng vẫn tiếp tục embed và ghi dữ liệu vào Chroma, dẫn đến trạng thái “mờ” khi kiểm tra sau. Dấu hiệu thấy qua log expectation có `halt=True`, nhưng không có dòng cảnh báo rõ ràng về việc embed bị skip. Tôi phát hiện qua việc `quarantine_records=4` nhưng vẫn có vector mới, không khớp với kỳ vọng “halt thì dừng”. Fix là cập nhật `etl_pipeline.py` để chỉ gọi embed khi không halt hoặc có `--skip-validate`, đồng thời luôn ghi manifest với `pipeline_status` và `embed_status`. Sau fix, khi `halt` thì pipeline trả mã 2 và không ghi embed, giúp observability rõ ràng hơn.

---

## 4. Bằng chứng trước / sau (80–120 từ)

> Dán ngắn 2 dòng từ `before_after_eval.csv` hoặc tương đương; ghi rõ `run_id`.

Tôi dùng `run_id: sprint1`. Dưới đây là 2 dòng CSV thật từ output cleaned/quarantine (tương đương bằng chứng trước/sau cho ingestion):

`cleaned_sprint1.csv`:
```
policy_refund_v4_2_c96089a43e33aa9d,policy_refund_v4,Yêu cầu hoàn tiền được chấp nhận trong vòng 7 ngày làm việc kể từ xác nhận đơn (ghi chú: bản sync cũ policy-v3 — lỗi migration). [cleaned: stale_refund_window],2026-02-01,2026-04-10T08:00:00
```

`quarantine_sprint1.csv`:
```
7,hr_leave_policy,Nhân viên dưới 3 năm kinh nghiệm được 10 ngày phép năm (bản HR 2025).,2025-01-01,2026-04-10T08:00:00,stale_hr_policy_effective_date,2025-01-01
```

Trong manifest `run_id: sprint1`, số liệu thay đổi là `cleaned_records=6`, `quarantine_records=4`.

---

## 5. Cải tiến tiếp theo (40–80 từ)

> Nếu có thêm 2 giờ — một việc cụ thể (không chung chung).

Nếu có thêm 2 giờ, tôi sẽ bổ sung log “explainability” cho từng record bị quarantine (kèm rule và threshold), xuất ra file `artifacts/quarantine/quarantine_explain_{run_id}.json`. Việc này giúp đội quality kiểm tra nhanh pattern lỗi mà không cần mở CSV thủ công, đồng thời dễ viết dashboard cho các rule vi phạm phổ biến.
