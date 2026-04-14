# Báo Cáo Cá Nhân — Lab Day 09: Multi-Agent Orchestration

**Họ và tên:** Nguyễn Minh Châu
**Vai trò trong nhóm:** Retrieval Owner
**Ngày nộp:** 14/04/2026
**Độ dài:** khoảng 680 từ

---

## 1. Tôi phụ trách phần nào?

Trong lab Day 09, phần tôi chịu trách nhiệm chính là viết Retrieval — cụ thể là implement `workers/retrieval.py`, tức module thực hiện dense retrieval từ ChromaDB và tích hợp vào `AgentState` của graph.

Cụ thể, tôi phụ trách toàn bộ pipeline trong file này: thiết kế embedding strategy (ưu tiên OpenAI `text-embedding-3-small` 1536 dims, fallback SentenceTransformers 384 dims, sau đó đến random cho test), kết nối ChromaDB collection `day09_docs`, logic lọc chunk theo `score_threshold`, deduplication sources, và chuẩn hóa output vào `AgentState` với đầy đủ `worker_io_log` và `worker_io_logs` cho audit trail.

**Module/file tôi chịu trách nhiệm:**
- File chính: `workers/retrieval.py`
- Công việc chính: implement dense retrieval, embedding strategy, ChromaDB integration, state output chuẩn hóa

**Bằng chứng (commit hash, file có comment tên bạn, v.v.):**

Commit chính của tôi: `5bbbda03968ce18184540a1d047ce4adb02f6e16` (author/nhãn: chauminhnguyen)

---

## 2. Tôi đã ra một quyết định kỹ thuật gì?

**Quyết định:** Tôi chọn giữ `retrieval_score_threshold` mặc định là `0.0` (không lọc noise) thay vì đặt thẳng `~0.3` như comment trong code gợi ý.

Lý do là ở giai đoạn đầu chưa có đủ dữ liệu để biết phân phối score của collection `day09_docs`. Nếu đặt threshold quá cao ngay từ đầu, những câu hỏi nằm ở vùng biên (score 0.25–0.35) sẽ bị lọc hết, khiến retrieval trả về list rỗng và đẩy toàn bộ query sang policy worker hoặc HITL — làm lệch routing distribution.

Tôi cân nhắc hai hướng: đặt threshold cứng 0.3 cho sạch. Hai là để 0.0 và để eval quyết định sau khi có dữ liệu thật. Tôi chọn hướng 2 vì mục tiêu Sprint 2 là đảm bảo retrieval không silent-fail trước khi có baseline metric.

Trade-off là downstream worker có thể nhận chunk chất lượng thấp nếu ChromaDB trả về kết quả nhiễu. Bù lại, routing distribution phản ánh đúng hành vi thật của hệ thống, và `top_score` được log vào `worker_io_log` để eval dễ phát hiện chunk kém chất lượng.

**Bằng chứng từ trace/code:**
```text
run_20260414_154651 (q06): retrieval route, confidence 0.70, latency 7523ms, top_score logged
run_20260414_155152 (q07): policy route — retrieval trả đủ chunks, policy worker xử lý tiếp
```

---

## 3. Tôi đã sửa một lỗi gì?

**Lỗi:** Embedding dimension mismatch — retrieval worker ban đầu load SentenceTransformers (384 dims) trong khi collection `day09_docs` đã được index bằng OpenAI `text-embedding-3-small` (1536 dims).

**Symptom:** ChromaDB không báo lỗi ngay mà trả về kết quả với score rất thấp (gần 0) cho mọi query, khiến tưởng retrieval chạy đúng nhưng chunk trả về hoàn toàn vô nghĩa. Routing vẫn đi vào retrieval branch nhưng `retrieved_chunks` thực tế là noise.

**Root cause:** Priority trong `_get_embedding_fn()` lúc đầu để SentenceTransformers lên trước OpenAI. Khi OpenAI key có sẵn nhưng đoạn code đó bị comment out (để test nhanh), fallback về ST luôn được dùng mà không có cảnh báo rõ ràng về dimension mismatch.

**Cách sửa:**
1. Đưa OpenAI lên làm priority đầu tiên trong `_get_embedding_fn()`, comment rõ lý do (`# PHẢI đặt trước để match collection 1536 dims`).
2. Thêm warning print ra stderr khi fallback về SentenceTransformers để không bao giờ bị silent.
3. Kiểm tra lại collection bằng `collection.count()` — raise `RuntimeError` rõ ràng nếu rỗng thay vì để ChromaDB trả về kết quả lạ.
4. Verify lại với q06 sau khi sửa — `top_score` tăng lên 0.70, xác nhận embedding đã khớp.

**Bằng chứng trước/sau:**
- Trước: mọi chunk trả về score ~0.02–0.08, sources đều là `unknown`.
- Sau (`run_20260414_154651`, q06): `top_score = 0.70`, sources khớp đúng tài liệu liên quan.

---

## 4. Tôi tự đánh giá đóng góp của mình

Điểm tôi làm tốt nhất là thiết kế `run()` theo worker contract rõ ràng — mọi trường hợp lỗi đều được catch, ghi vào `worker_io["error"]`, và state vẫn có `retrieved_chunks = []` để downstream không crash. Tôi cũng chủ động log `worker_io_logs` dạng audit trail để eval và documentation có thể trace lại từng run mà không cần debug lại từ đầu.

Điểm tôi còn yếu là phát hiện lỗi dimension mismatch hơi muộn — nên có unit test kiểm tra embedding dimension ngay từ đầu Sprint 2 thay vì phát hiện qua eval score bất thường.

Nhóm phụ thuộc vào tôi ở chỗ retrieval là điểm vào của mọi query đi vào retrieval branch. Ngược lại, tôi phụ thuộc vào orchestrator để nhận đúng `task` và `retrieval_top_k`, và vào team index để collection `day09_docs` có dữ liệu thật trước khi chạy.

---

## 5. Nếu có thêm 2 giờ, tôi sẽ làm gì?

Tôi sẽ thêm một bước calibrate `score_threshold` tự động dựa trên phân phối score của 5–10 query đầu tiên trong eval set. Cụ thể: chạy retrieval trên một mini eval batch, vẽ histogram score, rồi đặt threshold ở percentile 20 để cắt noise mà không mất chunk biên. Tôi chọn đúng cải tiến này vì `top_score` trong trace q06 là 0.70 nhưng một số query khác có score thấp hơn đáng kể — threshold tĩnh 0.0 hoặc 0.3 đều chưa optimal cho toàn bộ distribution thực tế.
