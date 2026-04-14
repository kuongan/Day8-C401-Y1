# Báo Cáo Cá Nhân — Lab Day 09: Multi-Agent Orchestration

**Họ và tên:** Phương Hoàng Yến
**Vai trò trong nhóm:** Trace Owner  
**Ngày nộp:** 14/4/2026 
**Độ dài yêu cầu:** 500–800 từ

---

> **Lưu ý quan trọng:**
> - Viết ở ngôi **"tôi"**, gắn với chi tiết thật của phần bạn làm
> - Phải có **bằng chứng cụ thể**: tên file, đoạn code, kết quả trace, hoặc commit
> - Nội dung phân tích phải khác hoàn toàn với các thành viên trong nhóm
> - Deadline: Được commit **sau 18:00** (xem SCORING.md)
> - Lưu file với tên: `reports/individual/[ten_ban].md` (VD: `nguyen_van_a.md`)

---

## 1. Tôi phụ trách phần nào? (100–150 từ)

> Mô tả cụ thể module, worker, contract, hoặc phần trace bạn trực tiếp làm.
> Không chỉ nói "tôi làm Sprint X" — nói rõ file nào, function nào, quyết định nào.

**Module/file tôi chịu trách nhiệm:**
- File chính: `eval_trace.py`
- Functions tôi implement: `analyze_trace() , compare_single_vs_multi()`

**Cách công việc của tôi kết nối với phần của thành viên khác:**
- Sau khi các thành viên đã hoàn thành phần code agent, tôi tiến hành eval nó trên tập test_questions.json gồm 10 câu hỏi giống với lab 8. Sau đó so sánh các metrics giữa 2 architecture lab 8 và lab 9
_________________

**Bằng chứng (commit hash, file có comment tên bạn, v.v.):**
commit hash:
6aa7a327737af4a3e9552f332084d9d8b28092dc
cf22410c658f7a655d9d4a6d0c42d43f25e7d4e3
285fec429f5b9bbaff9477afcb9f679d6491799e
---

## 2. Tôi đã ra một quyết định kỹ thuật gì? (150–200 từ)

> Chọn **1 quyết định** bạn trực tiếp đề xuất hoặc implement trong phần mình phụ trách.
> Giải thích:
> - Quyết định là gì?
> - Các lựa chọn thay thế là gì?
> - Tại sao bạn chọn cách này?
> - Bằng chứng từ code/trace cho thấy quyết định này có effect gì?

**Quyết định:** Tôi chịu trách nhiệm evaluation của nhóm, không có quyết định kỹ thuật nào

**Ví dụ:**
> "Tôi chọn dùng keyword-based routing trong supervisor_node thay vì gọi LLM để classify.
>  Lý do: keyword routing nhanh hơn (~5ms vs ~800ms) và đủ chính xác cho 5 categories.
>  Bằng chứng: trace gq01 route_reason='task contains P1 SLA keyword', latency=45ms."

**Lý do:**

_________________

**Trade-off đã chấp nhận:**

_________________

**Bằng chứng từ trace/code:**

```
[PASTE ĐOẠN CODE HOẶC TRACE RELEVANT VÀO ĐÂY]
```

---

## 3. Tôi đã sửa một lỗi gì? (150–200 từ)

> Mô tả 1 bug thực tế bạn gặp và sửa được trong lab hôm nay.
> Phải có: mô tả lỗi, symptom, root cause, cách sửa, và bằng chứng trước/sau.
**Lỗi**: UnicodeDecodeError khi load dữ liệu và Trace Files trên môi trường Windows.

**Symptom** (pipeline làm gì sai?):
Pipeline bị crash hoàn toàn ngay khi bắt đầu quá trình indexing hoặc analyze_traces. Hệ thống không thể nạp các tài liệu chứa ký tự tiếng Việt (có dấu) hoặc các ký tự đặc biệt từ file JSON, dẫn đến bộ nhớ đệm ChromaDB bị rỗng.

**Root cause** (lỗi nằm ở đâu — indexing, routing, contract, worker logic?):
Lỗi nằm ở phần Indexing và File I/O. Trên Windows, hàm open() mặc định sử dụng bảng mã cp1252, không tương thích với định dạng UTF-8 của các file dữ liệu mô hình và file trace.

**Cách sửa**:
Tiến hành rà soát toàn bộ các hàm open() trong script ingest.py và evaluation.py, bổ sung tham số encoding='utf-8'. Đồng thời, thêm kiểm tra if not os.path.exists và if not data để tránh nạp dữ liệu rỗng vào Vector DB.

**Bằng chứng trước/sau**:

Trước: UnicodeDecodeError: 'charmap' codec can't decode byte 0x9d... -> Collection 'day09_docs' rỗng.

Sau: route=retrieval_worker, conf=0.85, 420ms. Hệ thống load thành công 100% tài liệu và bắt đầu trả lời được câu hỏi.

> Dán trace/log/output trước khi sửa và sau khi sửa.

_________________

---

## 4. Tôi tự đánh giá đóng góp của mình (100–150 từ)

> Trả lời trung thực — không phải để khen ngợi bản thân.

**Tôi làm tốt nhất ở điểm nào?**
Thiết lập hệ thống Trace Analysis tự động. Thay vì kiểm tra thủ công từng câu trả lời, tôi đã viết hàm analyze_traces để thống kê toàn diện metrics (Latency, Confidence, Routing) cho toàn bộ 15 câu hỏi kiểm thử, giúp nhóm có cái nhìn khách quan về hiệu quả của Agent.
_________________

**Tôi làm chưa tốt hoặc còn yếu ở điểm nào?**
Việc xử lý lỗi môi trường (encoding, quyền Admin cho symlinks) tốn quá nhiều thời gian ban đầu, làm chậm tiến độ so sánh sâu các kết quả thất bại (failed cases) giữa các model.
_________________

**Nhóm phụ thuộc vào tôi ở đâu?** _(Phần nào của hệ thống bị block nếu tôi chưa xong?)_
Nhóm cần báo cáo Evaluation của tôi để biết model Agent (Lab 9) thực sự cải thiện chất lượng câu trả lời so với RAG (Lab 8) bao nhiêu phần trăm, từ đó quyết định có cần điều chỉnh prompt cho supervisor hay không.
_________________

**Phần tôi phụ thuộc vào thành viên khác:** _(Tôi cần gì từ ai để tiếp tục được?)_
Tôi cần thành viên phụ trách Indexing đảm bảo dữ liệu trong ChromaDB đã được "clean" và nạp đầy đủ, nếu không mọi kết quả trace tôi thu được đều vô nghĩa (do database rỗng)
_________________

---

## 5. Nếu có thêm 2 giờ, tôi sẽ làm gì? (50–100 từ)

> Nêu **đúng 1 cải tiến** với lý do có bằng chứng từ trace hoặc scorecard.
> Không phải "làm tốt hơn chung chung" — phải là:
> *"Tôi sẽ thử X vì trace của câu gq___ cho thấy Y."*
Tôi sẽ tập trung cải thiện độ phủ của Knowledge Base và khả năng truy xuất (Retrieval). Dựa trên kết quả trace của các câu gq07, gq08 và gq09, hệ thống hiện đang trả về độ tự tin rất thấp (confidence: 0.3) và báo lỗi "không đủ thông tin" dù dữ liệu nằm trong tài liệu. Tôi sẽ tiến hành tinh chỉnh lại quy trình chunking (chia nhỏ văn bản) để tránh mất ngữ cảnh của các chính sách phức tạp và cập nhật thêm metadata cho tài liệu, giúp retrieval_worker không bị "miss" thông tin khi xử lý các câu hỏi đa ý

---

*Lưu file này với tên: `reports/individual/[ten_ban].md`*  
*Ví dụ: `reports/individual/nguyen_van_a.md`*
