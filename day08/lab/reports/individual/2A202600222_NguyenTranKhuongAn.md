# Báo Cáo Cá Nhân — Lab Day 08: RAG Pipeline

**Họ và tên:** Nguyễn Trần Khương An  
**Vai trò trong nhóm:** Retrieval Owner
**Ngày nộp:** 13/04/2026
**Độ dài yêu cầu:** 500–800 từ

---

## 1. Tôi đã làm gì trong lab này? (100-150 từ)

> Mô tả cụ thể phần bạn đóng góp vào pipeline:
> - Chủ yếu làm Sprint 2.
> - Tôi implement retrieval baseline.
> - Công việc của tôi là xây dựng mô hình retrieval baseline.

_________________

---

## 2. Điều tôi hiểu rõ hơn sau lab này (100-150 từ)

> Tôi hiểu sâu hơn về cách retrieval và rerank phối hợp để tạo ra đầu vào chất lượng cho LLM. Rerank là bước quyết định xem điều kiện kết quả có đủ minh chứng để trả lời hay không. Khi tôi thử nghiệm nhiều cấu hình embedding và prompt, rõ ràng rằng cùng một tập document nhưng khác bước rerank lại cho ra chất lượng output rất khác nhau. Điều này giúp tôi thấy được rằng xây dựng pipeline RAG hiệu quả cần cân bằng giữa retrieval, rerank và chính sách abstain chứ không thể tối ưu một mình retrieval.
_________________

---

## 3. Điều tôi ngạc nhiên hoặc gặp khó khăn (100-150 từ)

> Điều khiến tôi bất ngờ nhất là bước đánh giá lại (rerank) thường đóng vai trò quan trọng hơn tôi dự đoán, nhất là với những câu hỏi alias hoặc không rõ ràng. Khó khăn lớn nhất là xác định chính xác điểm tắc nghẽn. Cụ thể như tài liệu đã được index đúng, embedding đưa về vector phù hợp nhưng rerank vẫn chọn tài liệu không chứa câu trả lời chính xác. Debug mất nhiều thời gian nhất khi phải kiểm tra từng phần của pipeline, đặc biệt là prompt context và cách LLM đánh giá chứng cứ. Ban đầu tôi nghĩ thiếu dữ liệu là nguyên nhân chính, nhưng thực tế là chúng tôi cần một bộ lọc evidence rõ ràng hơn.
_________________

---

## 4. Phân tích một câu hỏi trong scorecard (150-200 từ)

**Câu hỏi:** Approval Matrix để cấp quyền hệ thống là tài liệu nào?

**Phân tích:**
> Câu hỏi này thử thách khả năng retrieval vì nó dùng alias tên cũ "Approval Matrix" thay vì tên chính thức hiện tại. Baseline có thể trả lời đúng nếu retrieval tìm được được tài liệu access-control-sop.md qua mapping semantic, nhưng cũng có thể sai nếu chỉ dựa trên keyword matching. Lỗi chủ yếu nằm ở retrieval, cần một model hiểu được alias và liên kết tới tên tài liệu hiện tại. Nếu variant làm tốt rerank với kiến thức semantic và xử lý alias, nó sẽ cải thiện rõ rệt so với baseline. Generation là bước cuối cùng, nếu document đúng đã được tìm ra, model khả năng cao sẽ trả lời đúng. Do đó, cải thiện nên tập trung vào retrieval và rerank, thêm mapping alias cho query.
_________________

---

## 5. Nếu có thêm thời gian, tôi sẽ làm gì? (50-100 từ)

> Mở rộng dataset query alias và thêm bước mapping tên/thuật ngữ trước khi truy vấn retrieval. Ngoài ra, tôi muốn triển khai một cơ chế fallback để model abstain khi evidence không đủ rõ ràng, đồng thời đo lường lại hiệu quả bằng các metric khác nhaus. Những cải tiến này nhắm vào việc giảm lỗi do alias và tăng độ tin cậy của pipeline khi dữ liệu không trực tiếp khớp với câu hỏi.

_________________

---

*Lưu file này với tên: `reports/individual/[ten_ban].md`*
*Ví dụ: `reports/individual/nguyen_van_a.md`*
