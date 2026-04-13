# Báo Cáo Cá Nhân — Lab Day 08: RAG Pipeline

**Họ và tên:** Phương Hoàng Yến  
**Vai trò trong nhóm:** Tech Lead  
**Ngày nộp:** 13/4/2026 
**Độ dài yêu cầu:** 500–800 từ

---

## 1. Tôi đã làm gì trong lab này? (100-150 từ)

> Mô tả cụ thể phần bạn đóng góp vào pipeline:
Implement các hàm trong file index.py, hoàn thành sprint 1. Tiến hành kiểm thử các hàm trong index.py và in ra định dạng của chunk 
> - Sprint nào bạn chủ yếu làm?
Sprint 1
> - Cụ thể bạn implement hoặc quyết định điều gì?
Implement hàm get_embedding() sử dụng openAI, hoàn thiện hàm build_index() để đọc docs, preprocess, chunk, embed, rồi upsert vào ChromaDB. Chạy phần test ở cuối file index.py vào kiểm tra chunk bằng list_chunks() và inspect_metadata_coverage()
> - Công việc của bạn kết nối với phần của người khác như thế nào?
Làm người 1 nhận nhiệm vụ viết các base function trong index.py, người 2 sẽ implement các hàm còn lại để làm base code indexing cho hệ thống rag của nhóm
_________________

---

## 2. Điều tôi hiểu rõ hơn sau lab này (100-150 từ)

> Chọn 1-2 concept từ bài học mà bạn thực sự hiểu rõ hơn sau khi làm lab.
- Hiểu rõ hơn về reranking. Đây là 1 kỹ thuật không bắt buộc trong RAG nhưng cần thiết khi muốn nâng cao performance cho hệ thống truy vấn. Bước này được implement sau khi đã có baseline RAG hoàn chỉnh, ta sử dụng model reranker để sắp xếp lại thứ hạng trong top-k relevant giúp cải thiện chât lượng tìm kiếm
> Ví dụ: chunking, hybrid retrieval, grounded prompt, evaluation loop.
> Giải thích bằng ngôn ngữ của bạn — không copy từ slide.

_________________

---

## 3. Điều tôi ngạc nhiên hoặc gặp khó khăn (100-150 từ)

> Điều gì xảy ra không đúng kỳ vọng?
Khi push code của mình lên thì xảy ra commit. Thì ra có người push lên trước và khi mình push lên, phiên bản hiện tại xảy ra conflict, cần pull về và giải quyết conflit rồi mới push lên được
> Lỗi nào mất nhiều thời gian debug nhất?
Lỗi push code 
> Giả thuyết ban đầu của bạn là gì và thực tế ra sao?
Giả thuyết là phải push được lên, thực tế là phiên bản hiện tại trong máy không phải phiên bản mới nhất trên github gây conflict 
_________________

---

## 4. Phân tích một câu hỏi trong scorecard (150-200 từ)

> Chọn 1 câu hỏi trong test_questions.json mà nhóm bạn thấy thú vị.
> Phân tích:
> - Baseline trả lời đúng hay sai? Điểm như thế nào?
> - Lỗi nằm ở đâu: indexing / retrieval / generation?
> - Variant có cải thiện không? Tại sao có/không?

**Câu hỏi**: Approval Matrix để cấp quyền hệ thống là tài liệu nào?

**Phân tích**:

Câu hỏi này thử thách khả năng retrieval vì nó dùng alias tên cũ "Approval Matrix" thay vì tên chính thức hiện tại. Baseline có thể trả lời đúng nếu retrieval tìm được được tài liệu access-control-sop.md qua mapping semantic, nhưng cũng có thể sai nếu chỉ dựa trên keyword matching. Lỗi chủ yếu nằm ở retrieval, cần một model hiểu được alias và liên kết tới tên tài liệu hiện tại. Nếu variant làm tốt rerank với kiến thức semantic và xử lý alias, nó sẽ cải thiện rõ rệt so với baseline. Generation là bước cuối cùng, nếu document đúng đã được tìm ra, model khả năng cao sẽ trả lời đúng. Do đó, cải thiện nên tập trung vào retrieval và rerank, thêm mapping alias cho query.

_________________

---

## 5. Nếu có thêm thời gian, tôi sẽ làm gì? (50-100 từ)

> 1-2 cải tiến cụ thể bạn muốn thử.
Thử hybrid model BM25 và model hiện tại, thử các kiến trúc như parent child, có thể chunking nhỏ hơn để tăng khả năng search + giữ chunking hiện tại làm nhánh parent để vừa giữ được toàn bộ ngữ cảnh theo section
> Không phải "làm tốt hơn chung chung" mà phải là:
> "Tôi sẽ thử X vì kết quả eval cho thấy Y."

_________________

---

*Lưu file này với tên: `reports/individual/[ten_ban].md`*
*Ví dụ: `reports/individual/nguyen_van_a.md`*
