# Runbook — Lab Day 10

Mục tiêu của runbook này là xử lý nhanh các ca dữ liệu cũ, manifest hỏng, hoặc pipeline publish ra kết quả chưa an toàn.

## Symptom

Người dùng / agent bắt đầu thấy câu trả lời cũ, ví dụ refund window vẫn là 14 ngày thay vì 7 ngày, hoặc pipeline vừa chạy xong nhưng dữ liệu publish không còn đáng tin.

## Detection

Freshness được check từ manifest bằng lệnh:

```bash
python etl_pipeline.py freshness --manifest artifacts/manifests/manifest_<run-id>.json
```

Ý nghĩa trạng thái:

- `PASS`: manifest có timestamp hợp lệ và `latest_exported_at` còn trong SLA.
- `WARN`: manifest có nhưng thiếu / sai timestamp, nên chưa xác nhận được freshness một cách chắc chắn.
- `FAIL`: manifest mất, lỗi đọc / parse, hoặc `latest_exported_at` quá SLA.

Lưu ý vận hành:

- Nếu thấy `age_hours < 0` (timestamp nằm trong tương lai) nhưng command vẫn trả `PASS`, coi đây là dấu hiệu metadata không đáng tin, cần xử lý như một ca cảnh báo vận hành.
- Với ca này, không dùng kết quả `PASS` để kết luận dữ liệu fresh; phải kiểm tra lại nguồn export và chạy lại pipeline để tạo manifest hợp lệ.

SLA mặc định là 24 giờ, nhưng có thể đổi bằng biến môi trường `FRESHNESS_SLA_HOURS` nếu nhóm muốn thống nhất một ngưỡng khác.

## Diagnosis

| Bước | Việc làm | Kết quả mong đợi |
|------|----------|------------------|
| 1 | Mở manifest gần nhất trong `artifacts/manifests/` và kiểm tra `latest_exported_at`, `run_timestamp`, `pipeline_status`, `embed_status` | Có timestamp hợp lệ và trạng thái pipeline rõ ràng |
| 2 | So sánh `latest_exported_at` với thời điểm hiện tại và SLA | Nếu trong SLA thì `PASS`, nếu quá cũ thì `FAIL`, nếu nằm ở tương lai (age âm) thì đánh dấu bất thường vận hành |
| 3 | Nếu `WARN`, kiểm tra manifest có bị thiếu field hoặc timestamp sai format không | Xác nhận đây là lỗi metadata, không phải lỗi nội dung dữ liệu |
| 4 | Mở `artifacts/quarantine/` để xem có record nào bị loại vì rule / contract | Hiểu nguyên nhân dữ liệu sạch ít hoặc bị chặn |
| 5 | Chạy lại `python eval_retrieval.py --out artifacts/eval/<file>.csv` nếu dữ liệu vừa được sửa | Xác nhận before / after trên retrieval |

## Mitigation

Khi `FAIL` vì freshness:

1. Xác nhận source export thật sự là mới, không phải chỉ rerun trên dữ liệu cũ.
2. Chạy lại pipeline ingestion / clean / embed với `run_id` mới để tạo manifest mới.
3. Nếu `embed_status=failed`, xử lý lỗi embed trước rồi rerun vì manifest chỉ phản ánh publish boundary, không thay thế được index thật.
4. Nếu dữ liệu đã stale nhưng chưa thể refresh ngay, gắn cảnh báo tạm thời kiểu “data stale” hoặc tạm ngừng dùng kết quả publish đó.

Khi `PASS` nhưng `age_hours < 0` (timestamp tương lai):

1. Mở manifest và xác nhận `latest_exported_at` có vượt quá thời điểm hiện tại không (sai timezone, clock drift, hoặc dữ liệu test tương lai).
2. Không dùng run đó cho báo cáo chất lượng; gắn nhãn incident metadata/freshness.
3. Chạy lại pipeline bằng dữ liệu export hợp lệ ở hiện tại để tạo manifest mới, sau đó check lại freshness.
4. Ghi nguyên nhân vào report/runbook để tránh lặp lại (timezone, dữ liệu mock, hoặc thao tác sửa tay manifest).

Khi `WARN` vì thiếu timestamp:

1. Kiểm tra code tạo manifest có ghi `latest_exported_at` hay không.
2. Nếu chỉ thiếu metadata nhưng dữ liệu clean / embed vẫn hợp lệ, bổ sung field đó rồi regenerate manifest.
3. Nếu manifest bị lỗi shape / JSON, coi như artifact hỏng và tạo lại từ đầu.

## Prevention

- Ghi `latest_exported_at` nhất quán trong manifest để freshness luôn đo được.
- Giữ `FRESHNESS_SLA_HOURS` ở cùng một giá trị trong README, runbook, và script chạy CI / demo.
- Mỗi lần fix dữ liệu phải tạo `run_id` mới để không đè mất evidence before / after.
- Khi nhóm đã có alert hoặc dashboard, nối rule freshness vào owner phụ trách ingest / publish để tránh phát hiện muộn.
