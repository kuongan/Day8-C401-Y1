# Báo Cáo Cá Nhân — Lab Day 08: RAG Pipeline

**Họ và tên:** Phạm Minh Việt  
**Vai trò trong nhóm:** Retrieval Owner (Sprint 3)  
**Ngày nộp:** 13/04/2026  
**Độ dài yêu cầu:** 500–800 từ

---

## 1. Tôi đã làm gì trong lab này? (100-150 từ)

> Mô tả cụ thể phần bạn đóng góp vào pipeline:
> - Sprint nào bạn chủ yếu làm?
> - Cụ thể bạn implement hoặc quyết định điều gì?
> - Công việc của bạn kết nối với phần của người khác như thế nào?

Trong lab này, phần mình phụ trách chính là Sprint 3, tức tuning retrieval để cải thiện chất lượng trả lời mà vẫn giữ tính grounded. Cụ thể, mình chọn hướng rerank bằng cross-encoder thay vì đổi toàn bộ retrieval stack. Mình implement hàm rerank trong rag_answer.py theo kiểu funnel: đầu tiên dense search lấy top_k_search = 10 candidates, sau đó cross-encoder chấm lại từng cặp query-chunk, rồi chọn top_k_select = 3 chunks tốt nhất đưa vào prompt generate. Model mình dùng là cross-encoder/ms-marco-MiniLM-L-6-v2, được load lazy để tránh tốn tài nguyên khi không bật rerank. Ngoài phần code, mình chạy so sánh baseline với variant và ghi kết quả vào tuning-log. Công việc của mình nối trực tiếp với phần eval vì mọi thay đổi retrieval đều phải được xác nhận bằng scorecard chứ không chỉ dựa vào cảm giác.

---

## 2. Điều tôi hiểu rõ hơn sau lab này (100-150 từ)

> Chọn 1-2 concept từ bài học mà bạn thực sự hiểu rõ hơn sau khi làm lab.
> Ví dụ: chunking, hybrid retrieval, grounded prompt, evaluation loop.
> Giải thích bằng ngôn ngữ của bạn — không copy từ slide.

Sau lab này, mình hiểu rõ hơn sự khác nhau giữa recall và ranking quality trong RAG. Trước đây mình hay nghĩ retrieve được đúng tài liệu là đủ, nhưng khi làm thật mới thấy điều quan trọng là thứ tự chunk nào được đưa vào context cuối cùng. Với baseline dense, Context Recall đạt 5.00/5 nghĩa là hệ thống thường tìm được nguồn đúng, nhưng Completeness chỉ 3.40/5 vì top-3 chưa phải lúc nào cũng là 3 đoạn hữu ích nhất để trả lời trọn ý. Từ đó mình hiểu vì sao rerank tồn tại: nó không thay retrieval gốc, mà tối ưu chất lượng đầu vào cho bước generation. Mình cũng hiểu thêm rằng grounded prompt không tự cứu được mọi trường hợp. Nếu context top-3 bị lệch, model vẫn có thể trả lời lệch nhưng trông rất thuyết phục. Nói ngắn gọn: retrieval quyết định model được “nhìn thấy gì”, còn generation chỉ quyết định model “nói thế nào”.

---

## 3. Điều tôi ngạc nhiên hoặc gặp khó khăn (100-150 từ)

> Điều gì xảy ra không đúng kỳ vọng?
> Lỗi nào mất nhiều thời gian debug nhất?
> Giả thuyết ban đầu của bạn là gì và thực tế ra sao?

Điều làm mình bất ngờ là rerank không tự động làm hệ thống tốt hơn, dù về lý thuyết đây là bước “nâng cấp”. Giả thuyết ban đầu của mình là thêm cross-encoder sẽ tăng Relevance và Completeness mà gần như không ảnh hưởng Faithfulness. Kết quả thực tế: Completeness tăng nhẹ từ 3.40 lên 3.60, nhưng Faithfulness lại giảm từ 4.80 xuống 4.60. Lỗi debug tốn thời gian nhất là câu q03 về approval cho quyền Level 3. Ban đầu mình nghi do index thiếu hoặc metadata sai, nhưng kiểm tra lại thì indexing ổn và nguồn vẫn retrieve được. Vấn đề nằm ở bước rerank: một chunk không đúng trọng tâm bị đẩy lên cao, làm generation bám theo ngữ cảnh lệch. Bài học lớn nhất của mình là không có “silver bullet” trong tuning. Mỗi biến thay đổi đều có trade-off và bắt buộc phải kiểm tra bằng A/B có kiểm soát, chỉ đổi một biến mỗi lần.

---

## 4. Phân tích một câu hỏi trong scorecard (150-200 từ)

> Chọn 1 câu hỏi trong test_questions.json mà nhóm bạn thấy thú vị.
> Phân tích:
> - Baseline trả lời đúng hay sai? Điểm như thế nào?
> - Lỗi nằm ở đâu: indexing / retrieval / generation?
> - Variant có cải thiện không? Tại sao có/không?

**Câu hỏi:** Ai phải phê duyệt để cấp quyền Level 3? (q03)

**Phân tích:**

Ở baseline dense, câu q03 cho kết quả khá ổn: hệ thống trả lời đúng hướng và có dẫn nguồn. Điểm Relevance và Completeness cao vì câu trả lời bám đúng intent của câu hỏi. Tuy nhiên, khi bật variant rerank, đây lại là câu bị giảm chất lượng rõ nhất về Faithfulness (trong scorecard xuống 2/5 cho câu này). Điều đáng chú ý là Context Recall vẫn 5/5, nghĩa là dữ liệu liên quan thật ra đã được lấy về từ retrieval ban đầu. Vì vậy, lỗi không nằm ở indexing và cũng không phải do “không có tài liệu”, mà nằm ở ranking sau retrieval.

Khi cross-encoder sắp xếp lại candidates, một đoạn nói về cấp quyền khác mức đã được ưu tiên cao hơn đoạn then chốt cho Level 3. Generation sau đó vẫn trả lời rất tự tin vì nó trung thành với context top-3 được cung cấp, nhưng nội dung bị lệch logic nghiệp vụ. Trường hợp này cho mình thấy một điểm quan trọng: tăng độ “thông minh” ở rerank chưa chắc phù hợp domain nếu model reranker không hiểu tốt thuật ngữ chính sách nội bộ. Variant có lợi ở một số câu khác như q01 và q06 (Completeness tăng từ 4 lên 5), nhưng riêng q03 thì hồi quy chất lượng. Kết luận của mình là với bộ dữ liệu hiện tại, rerank generic cần được dùng thận trọng và không thể thay baseline dense một cách mặc định.

---

## 5. Nếu có thêm thời gian, tôi sẽ làm gì? (50-100 từ)

> 1-2 cải tiến cụ thể bạn muốn thử.
> Không phải "làm tốt hơn chung chung" mà phải là:
> "Tôi sẽ thử X vì kết quả eval cho thấy Y."

Nếu có thêm thời gian, mình sẽ thử query expansion cho nhóm câu có alias mismatch, đặc biệt q07 (Approval Matrix so với Access Control SOP), vì score hiện tại cho thấy đây là lỗi truy vấn chứ không phải lỗi thiếu tài liệu. Mình cũng muốn thêm bước kiểm tra consistency sau rerank: nếu top chunks mâu thuẫn về level/điều kiện thì fallback về thứ hạng dense ban đầu. Hai cải tiến này hợp lý hơn tiếp tục tăng độ phức tạp model, vì chúng bám sát đúng lỗi đã thấy trong eval.

---

*Lưu file này với tên: `reports/individual/[ten_ban].md`*
*Ví dụ: `reports/individual/nguyen_van_a.md`*
