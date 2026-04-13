# Báo Cáo Cá Nhân — Lab Day 08: RAG Pipeline

**Họ và tên:** Nguyễn Minh Châu  
**Vai trò trong nhóm:** Eval Owner
**Ngày nộp:** 13/04/2026s
**Độ dài yêu cầu:** 500–800 từ

---

## 1. Tôi đã làm gì trong lab này? (100-150 từ)

> Mô tả cụ thể phần bạn đóng góp vào pipeline:
> - Chủ yếu làm Sprint 4.
> - Tôi implement các hàm đánh giá.
> - Công việc của tôi là đánh giá mô hình của nhóm với baseline.

_________________

---

## 2. Điều tôi hiểu rõ hơn sau lab này (100-150 từ)

> Sau lab này, tôi hiểu rõ hơn về vai trò của rerank trong pipeline retrieval-augmented generation. Việc chỉ lấy document dựa trên cosine similarity không đủ, vì cần có bước đánh giá lại để chọn ra nguồn phù hợp nhất trước khi chuyển sang generation. Tôi cũng có thêm kinh nghiệm với cách dùng LLM-as-Judge để đánh giá chất lượng trả lời bằng các thước đo grounding và factuality, thay vì chỉ so sánh text đơn thuần. Phương pháp này giúp phát hiện được trường hợp model trả lời chắc chắn nhưng thiếu bằng chứng, đặc biệt khi dữ liệu nguồn không chứa câu trả lời rõ ràng.
_________________

---

## 3. Điều tôi ngạc nhiên hoặc gặp khó khăn (100-150 từ)

> Điều khiến tôi ngạc nhiên là lỗi ở bước generation. Câu hỏi có thông tin không rõ ràng hoặc không có đáp án trong tài liệu dễ khiến model hallucinate. Debug dài nhất là khi đối chiếu kết quả retrieval với scorecard, vì phải kiểm tra từng bước như index doc, query vector, rerank và prompt template. Giả thuyết ban đầu của tôi là vấn đề chủ yếu do retrieval kém, nhưng thực tế là cần cả retrieval tốt và judge phù hợp để tránh trả lời sai khi dữ liệu không đủ.
_________________

---

## 4. Phân tích một câu hỏi trong scorecard (150-200 từ)

**Câu hỏi:** ERR-403-AUTH là lỗi gì và cách xử lý?

**Phân tích:**
> Câu hỏi này rất thú vị vì thuộc loại "insufficient context": tài liệu hiện tại không có thông tin chính xác về mã lỗi ERR-403-AUTH. Baseline thường trả lời sai hoặc đưa ra câu trả lời chung chung về lỗi xác thực, vì model cố gắng sinh kết quả từ ngữ cảnh không phù hợp. Lỗi chính nằm ở cả retrieval và generation. Retrieval không thể cung cấp bằng chứng đúng, và generation lại không abstain được khi thiếu dữ kiện. LLM-as-Judge có thể phát hiện absence of evidence và trả về thông báo không tìm thấy thông tin, nhưng không hoàn hảo nếu prompt vẫn khuyến khích model cố gắng suy luận.
_________________

---

## 5. Nếu có thêm thời gian, tôi sẽ làm gì? (50-100 từ)

> Tôi sẽ thử thêm cơ chế detect "không có đủ thông tin" trước khi generation, bằng cách dùng LLM-as-Judge để so sánh truy vấn với nguồn. Ngoài ra tôi muốn thử prompt engineering rõ ràng hơn cho việc abstain và kiểm tra lại hiệu quả rerank với các metrics như recall và evidence precision. Những cải tiến này dựa trên kết quả eval cho thấy lỗi lớn nhất là model trả lời khi không có bằng chứng đầy đủ.

_________________

---

*Lưu file này với tên: `reports/individual/[ten_ban].md`*
*Ví dụ: `reports/individual/nguyen_van_a.md`*
