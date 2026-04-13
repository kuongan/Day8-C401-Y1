# Báo Cáo Cá Nhân — Lab Day 08: RAG Pipeline

**Họ và tên:** Lê Hoàng Minh
**Vai trò trong nhóm:** Tech Lead 
**Ngày nộp:** 13/4/2026
**Độ dài yêu cầu:** 500–800 từ

---

## 1. Tôi đã làm gì trong lab này? (100-150 từ)

> Mô tả cụ thể phần bạn đóng góp vào pipeline:
> - Sprint nào bạn chủ yếu làm?
> - Cụ thể bạn implement hoặc quyết định điều gì?
> - Công việc của bạn kết nối với phần của người khác như thế nào?

Trong lab Day 08, tôi đảm nhiệm vai trò Tech Lead nên tập trung chính vào Sprint 1 và phần kết nối end-to-end giữa các sprint. Ở Sprint 1, tôi hoàn thiện pipeline index trong index.py gồm preprocess metadata, chunking theo heading/paragraph, embedding bằng OpenAI text-embedding-3-small và lưu vào ChromaDB. Kết quả chạy thực tế index được đủ 5 tài liệu, tạo 29 chunks, không thiếu effective_date. Sau đó tôi phối hợp với Retrieval Owner để cố định baseline dense (top-k search = 10, top-k select = 3), giúp nhóm có một mốc so sánh rõ ràng cho Sprint 3. Tôi cũng hỗ trợ Documentation Owner cập nhật architecture.md bằng số liệu runtime thật, đảm bảo report không chỉ mô tả ý tưởng mà phản ánh đúng hành vi hệ thống khi chạy.

---

## 2. Điều tôi hiểu rõ hơn sau lab này (100-150 từ)

> Chọn 1-2 concept từ bài học mà bạn thực sự hiểu rõ hơn sau khi làm lab.
> Ví dụ: chunking, hybrid retrieval, grounded prompt, evaluation loop.
> Giải thích bằng ngôn ngữ của bạn — không copy từ slide.

Điều tôi hiểu rõ hơn là chunking không chỉ là cắt văn bản, mà là thiết kế đơn vị tri thức để retrieval tìm đúng bằng chứng. Khi chunk theo ranh giới tự nhiên (section heading) rồi mới tách tiếp theo paragraph nếu quá dài, model giữ được ngữ cảnh điều khoản tốt hơn so với cắt cứng theo độ dài. Tôi cũng hiểu sâu hơn về trade-off giữa recall và precision trong retrieval. Baseline dense của nhóm cho context recall rất cao (5.0), nghĩa là hệ thống thường tìm được đúng nguồn lớn. Tuy nhiên relevance và completeness vẫn có thể thấp vì thứ tự top chunk chưa tối ưu cho câu hỏi cụ thể. Từ đó, tôi nhìn rõ vai trò của bước tuning: không phải thay toàn bộ pipeline, mà chọn đúng nút thắt để cải thiện.

---

## 3. Điều tôi ngạc nhiên hoặc gặp khó khăn (100-150 từ)

> Điều gì xảy ra không đúng kỳ vọng?
> Lỗi nào mất nhiều thời gian debug nhất?
> Giả thuyết ban đầu của bạn là gì và thực tế ra sao?

Điều khiến tôi ngạc nhiên là baseline đã khá mạnh dù triển khai tương đối tối thiểu: faithfulness 4.8/5 và context recall 5.0/5. Trước khi chạy eval, tôi kỳ vọng rerank bằng cross-encoder sẽ cải thiện rõ relevance và completeness mà không ảnh hưởng faithfulness. Thực tế thì không hoàn toàn như vậy. Ở variant rerank, completeness tăng nhẹ (+0.2) nhưng faithfulness lại giảm (-0.2), cho thấy pipeline có thể tradeoff khi thêm thành phần mới. Khó khăn lớn nhất là phân biệt lỗi do retrieval hay generation. Ban đầu tôi nghi retrieval thiếu dữ liệu, nhưng sau khi đối chiếu từng câu và metadata, một phần lỗi đến từ rerank chọn sai chunk ưu tiên, khiến generation bám theo ngữ cảnh chưa chuẩn. Bài học là phải debug theo error tree thay vì đoán theo cảm giác.

---

## 4. Phân tích một câu hỏi trong scorecard (150-200 từ)

> Chọn 1 câu hỏi trong test_questions.json mà nhóm bạn thấy thú vị.
> Phân tích:
> - Baseline trả lời đúng hay sai? Điểm như thế nào?
> - Lỗi nằm ở đâu: indexing / retrieval / generation?
> - Variant có cải thiện không? Tại sao có/không?

**Câu hỏi:** “Ai phải phê duyệt để cấp quyền Level 3?” (q03)

**Phân tích:**

Với baseline dense, hệ thống trả lời tương đối ổn vì retrieve được các đoạn trong Access Control SOP liên quan đến phân cấp quyền. Điểm của câu này ở baseline đạt mức chấp nhận được do nội dung vẫn grounded vào policy và không bịa thông tin ngoài ngữ cảnh. Tuy nhiên khi chuyển sang variant có rerank cross-encoder, q03 là ví dụ rõ nhất cho mặt trái của tuning. Mặc dù top-k search và top-k select giữ nguyên để A/B công bằng, bước rerank đã đẩy lên một chunk không đúng trọng tâm Level 3, dẫn tới suy luận sai và làm faithfulness giảm mạnh ở câu này.

Từ góc nhìn pipeline, lỗi chính nằm ở retrieval ranking, không phải indexing. Index đã đủ metadata và coverage tốt, nên dữ liệu nguồn không phải vấn đề. Generation cũng chỉ đang “trung thành” với context được đưa vào; khi context top-3 bị lệch, câu trả lời bị lệch theo. Variant vì vậy không tốt hơn baseline cho q03, dù có cải thiện nhỏ ở một số câu khác về completeness. Kết luận của tôi là reranker generic chưa phù hợp domain policy nội bộ, và không nên áp dụng nếu chưa có kiểm định theo từng nhóm câu hỏi quan trọng.

---

## 5. Nếu có thêm thời gian, tôi sẽ làm gì? (50-100 từ)

> 1-2 cải tiến cụ thể bạn muốn thử.
> Không phải "làm tốt hơn chung chung" mà phải là:
> "Tôi sẽ thử X vì kết quả eval cho thấy Y."

Nếu có thêm thời gian, tôi sẽ thử query expansion có kiểm soát thay vì tiếp tục tăng độ phức tạp rerank. Lý do là scorecard cho thấy vấn đề nổi bật nằm ở alias/paraphrase mismatch (ví dụ “Approval Matrix” vs “Access Control SOP”), trong khi dense đã có recall cao. Tôi cũng muốn thêm fallback answer template khi hệ thống abstain, để ngoài câu “Không đủ dữ liệu” còn gợi ý nguồn liên quan hoặc từ khóa thay thế, giúp trải nghiệm người dùng tốt hơn.

---

*Lưu file này với tên: `reports/individual/[ten_ban].md`*
*Ví dụ: `reports/individual/nguyen_van_a.md`*
