# Báo Cáo Cá Nhân — Lab Day 08: RAG Pipeline

**Họ và tên:** Trần Vọng Triển   
**Vai trò trong nhóm:** Documentation Owner  
**Ngày nộp:** ___________  
**Độ dài yêu cầu:** 500–800 từ

---

## 1. Tôi đã làm gì trong lab này? (100-150 từ)
 Trong bài lab này, tôi đảm nhận vai trò Documentation Owner, tập trung chủ yếu vào Sprint 4 để tổng hợp toàn bộ kết quả của nhóm. Cụ thể:

- Hệ thống hóa kiến trúc: soạn thảo file architecture.md và tuning-log.

- Theo dõi và ghi chép Tuning Log: tổng hợp số liệu từ các đợt chạy A/B Test giữa Baseline (Dense) và Variant (Rerank). Chạy hàm tính toán Delta để đánh giá xem việc thêm Reranker thực sự mang lại giá trị hay chỉ làm "nặng" máy.

Công việc của tôi là giúp kết nối phần code của Tech Lead và phần đánh giá của Eval Owner thành một bộ hồ sơ dự án hoàn chỉnh.

---

## 2. Điều tôi hiểu rõ hơn sau lab này (100-150 từ)

- Hiểu về trade-off giữa Retrieval và Generation. Việc tăng cường khả năng tìm kiếm (như thêm Reranker) không phải lúc nào cũng giúp câu trả lời tốt hơn. Nếu Reranker không khớp với domain của dữ liệu, nó có thể đưa sai ngữ cảnh lên đầu, gây ra lỗi hallucination. 
- Hiểu thêm về cách dùng Metadata (department, effective_date) để kiểm soát nguồn gốc tài liệu và hỗ trợ việc citation chính xác.

---

## 3. Điều tôi ngạc nhiên hoặc gặp khó khăn (100-150 từ)

- Nhóm mong đợi là Reranker sẽ giúp tăng độ chính xác, nhưng thực tế nó lại nhầm lẫn giữa các đề mục có từ khóa giống nhau (như các Level bảo mật), làm giảm Faithfulness.

- Khó khăn lớn nhất là xử lý lỗi Alias mismatch (q07). Hệ thống không thể nhận diện "Approval Matrix" chính là "Access Control SOP" dù embedding model rất mạnh. Điều này cho thấy vector search vẫn có giới hạn về mặt ngữ nghĩa chuyên biệt.

---

## 4. Phân tích một câu hỏi trong scorecard (150-200 từ)

> Chọn 1 câu hỏi trong test_questions.json mà nhóm bạn thấy thú vị.
> Phân tích:
> - Baseline trả lời đúng hay sai? Điểm như thế nào?
> - Lỗi nằm ở đâu: indexing / retrieval / generation?
> - Variant có cải thiện không? Tại sao có/không?

**Câu hỏi:** q03: "Ai phải phê duyệt để cấp quyền Level 3?"

**Phân tích:**
Baseline: Trả lời rất tốt (Faithfulness 5/5, Completeness 5/5). Hệ thống sử dụng Dense Retrieval đã truy xuất chính xác chunk tài liệu về "Access Control SOP", từ đó LLM trích xuất đầy đủ 3 đối tượng phê duyệt gồm Line Manager, IT Admin và IT Security.

Lỗi nằm ở: Khâu Retrieval (Reranking) của Variant 1. Cụ thể, mô hình Cross-encoder đã chấm điểm ưu tiên cho chunk liên quan đến Level 2 vì có mật độ từ khóa (keyword density) cao, nhưng lại thiếu điều khoản dành riêng cho Level 3. Đây là lỗi phổ biến khi Reranker chỉ tập trung vào độ tương đồng bề mặt mà bỏ qua các logic phân cấp tinh tế trong văn bản chính sách.

Variant có cải thiện không? Không, thậm chí tệ hơn đáng kể. Điểm Faithfulness giảm từ 5 xuống 2. Do Reranker đẩy sai ngữ cảnh lên đầu, LLM đã bị "dẫn dụ" và lấy nhầm điều kiện phê duyệt của Level 2 để áp đặt cho Level 3. Điều này gây ra lỗi hallucination (ảo tưởng) về nội dung, làm sai lệch quy trình vận hành thực tế của doanh nghiệp.

---

## 5. Nếu có thêm thời gian, tôi sẽ làm gì? (50-100 từ)

- Muốn thử Variant 2: Query Expansion. Thay vì cố gắng xếp hạng lại các chunk cũ, tôi muốn dùng LLM để mở rộng các thuật ngữ chuyên môn (như mã lỗi, tên quy trình) trước khi tìm kiếm. Kết quả eval cho thấy nhóm đang yếu ở khả năng xử lý từ đồng nghĩa, nên đây có thể là cách hiệu quả để tăng Relevance mà vẫn giữ được độ an toàn.


---

*Lưu file này với tên: `reports/individual/[ten_ban].md`*
*Ví dụ: `reports/individual/nguyen_van_a.md`*
