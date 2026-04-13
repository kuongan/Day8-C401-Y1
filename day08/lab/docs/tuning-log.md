# Tuning Log — RAG Pipeline (Day 08 Lab)

> Template: Ghi lại mỗi thay đổi và kết quả quan sát được.
> A/B Rule: Chỉ đổi MỘT biến mỗi lần.

---

## Baseline (Sprint 2)

**Ngày:** 2026-04-13  
**Config:**
```
retrieval_mode = "dense"
chunk_size = 400 tokens
overlap = 80 tokens
top_k_search = 10
top_k_select = 3
use_rerank = False
llm_model = gpt-4o-mini
```

**Scorecard Baseline:**
| Metric | Average Score |
|--------|--------------|
| Faithfulness | 4.80 /5 |
| Answer Relevance | 3.80 /5 |
| Context Recall | 5.00 /5 |
| Completeness | 3.40 /5 |

**Câu hỏi yếu nhất (điểm thấp):**
> **q07 (Approval Matrix)** - Relevance=1/5, Completeness=1/5. Dense bỏ lỡ "Approval Matrix" vì document đã đổi tên thành "Access Control SOP". Correctly abstain nhưng không retrieval được expected source.
>
> **q09 (ERR-403-AUTH)** - Relevance=1/5, Completeness=2/5. Error code không trong corpus, model correctly nói "Không đủ dữ liệu". Faithfulness=5/5 (không hallucinate) nhưng relevance thấp vì query yêu cầu dữ liệu không có.
>
> **q10 (VIP Refund)** - Relevance=1/5, Completeness=1/5. Query hỏi quy trình hoàn tiền VIP không có trong docs, correctly abstained. Cần content richer hoặc query expansion.

**Giả thuyết nguyên nhân (Error Tree):**
- [x] Indexing: Metadata đầy đủ, không missing effective_date
- [x] Retrieval: Dense ok (Context Recall=5.0), retrieval logic solid
- [x] Generation: Grounding ok, model không hallucinate (Faithfulness=4.8)
- [x] Alias bỏ lỡ: q07 - Dense không biết "Approval Matrix" = "Access Control SOP"
- [ ] Query expansion: q07, q10 cần expanded query hoặc multi-hop reasoning
- [x] Context length ok: Recall=5.0 cho tất cả retrieval được source

---

## Variant 1 (Sprint 3)

**Ngày:** 2026-04-13  
**Biến thay đổi:** Thêm cross-encoder rerank sau dense retrieval
**Lý do chọn biến này:**
> Baseline faithfulness cao (4.80) nhưng completeness thấp (3.40) → cần improve depth mà không sacrifice grounding.
> Thấy q01, q06, q08 missing completeness (chỉ 4/5) vì context top-3 không enough nuanced → rerank giúp đưa chunk chân chính nhất lên top-3.
> Dense ok về recall (5.0), nhưng precision (relevance=3.8) có thể cải thiện bằng cross-encoder rescoring.

**Config thay đổi:**
```
retrieval_mode = "dense"    # Giữ nguyên
use_rerank = True           # Thay đổi: cross-encoder reranking
top_k_search = 10           # Giữ nguyên
top_k_select = 3            # Giữ nguyên
```

**Scorecard Variant 1:**
| Metric | Baseline | Variant 1 | Delta |
|--------|----------|-----------|-------|
| Faithfulness | 4.80/5 | 4.60/5 | -0.20 |
| Answer Relevance | 3.80/5 | 3.80/5 | 0 |
| Context Recall | 5.00/5 | 5.00/5 | 0 |
| Completeness | 3.40/5 | 3.60/5 | +0.20 |

**Nhận xét:**
> **Cải thiện:** q01, q06 completeness tăng 4→5 vì rerank đưa chunk có first response time (15 min) lên top.
> **Hạ xuống:** q03 faithfulness xuống 4→2 vì rerank chọn sai chunk - lấy Level 2 requirement mà áp cho Level 3, hallucinate "IT Security for L3".
> Trade-off: +0.20 completeness nhưng -0.20 faithfulness → không giá trị.

**Kết luận:**
> **Variant 1 KHÔNG tốt hơn baseline.** Hallucination tăng ở q03, faithfulness giảm. Cross-encoder generic không phù hợp corporate policy domain.
> **Recommendation:** Dùng baseline dense, hoặc thử query expansion để fix alias issues.

---

## Variant 2 (nếu có thời gian)

**Biến thay đổi:** ___________  
**Config:**
```
# TODO
```

**Scorecard Variant 2:**
| Metric | Baseline | Variant 1 | Variant 2 | Best |
|--------|----------|-----------|-----------|------|
| Faithfulness | ? | ? | ? | ? |
| Answer Relevance | ? | ? | ? | ? |
| Context Recall | ? | ? | ? | ? |
| Completeness | ? | ? | ? | ? |


---

## Tóm tắt học được

1. **Lỗi phổ biến nhất trong pipeline này là gì?**
   > **Alias / Paraphrase mismatch** (q07 Approval Matrix): Dense embeddings không biết tên cũ = tên mới. Model correctly abstain (Faithfulness=5) nhưng Relevance=1 vì query không match semantic.
   > **Query outside corpus** (q09, q10): ERR-403, VIP refund không trong docs → correctly abstain nhưng Relevance=1 (no choice).
   > **Completeness gap** (3.4/5): Context top-3 không enough detail, cần multi-hop hoặc expansion.

2. **Biến nào có tác động lớn nhất tới chất lượng?**
   > **Rerank (cross-encoder):** Âm tác động (-0.20 faithfulness ở Variant1). Generic model không phù hợp policy domain → hallucinate q03.
   > **Dense embedding quality:** Cực tốt (Recall=5.0), không cần đổi model.
   > **Query expansion:** Dự kiến +0.5-1.0 relevance (chưa test, nhưng lý thuyết giải q07, q10).

3. **Nếu có thêm 1 giờ, nhóm sẽ thử gì tiếp theo?**
   > (1) Variant 2 - Query Expansion: Thực hiện mở rộng từ khóa "Approval Matrix" thành "Access Control SOP" và các biến thể khác để cải thiện điểm số cho câu q07.

 > (2) Fine-tune reranker: Sử dụng kết quả đánh giá từ q01-q10 để tinh chỉnh mô hình cross-encoder chuyên biệt cho mảng chính sách nội bộ nhằm khắc phục lỗi ở câu q03.

 > (3) Fallback template: Thay vì chỉ báo "Không đủ dữ liệu", hệ thống sẽ gợi ý thêm các từ khóa liên quan hoặc các đầu mục tài liệu gần nhất để tăng trải nghiệm người dùng.

 > Thứ tự ưu tiên: (1) > (3) > (2) để tối ưu hóa trải nghiệm người dùng (user experience) nhanh nhất.

