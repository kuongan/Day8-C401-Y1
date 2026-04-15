# Quality report — Lab Day 10 (nhom)

**run_id:** sprint3-inject-bad -> sprint3-after-fix  
**Ngay:** 2026-04-15

---

## 1. Tom tat so lieu

| Chi so | Truoc (inject-bad) | Sau (after-fix) | Ghi chu |
|--------|---------------------|-----------------|---------|
| raw_records | 13 | 13 | Tu `manifest_sprint3-inject-bad.json` va `manifest_sprint3-after-fix.json` |
| cleaned_records | 5 | 5 | Khong doi so luong cleaned |
| quarantine_records | 8 | 8 | Khong doi so luong quarantine |
| Expectation halt? | Co fail (`refund_no_stale_14d_window`, violations=1) nhung duoc bo qua do `--skip-validate` | Khong halt, tat ca expectation halt deu pass | The hien su khac biet giua inject va fix |

---

## 2. Before / after retrieval (bat buoc)

File evidence:

- `artifacts/eval/after_inject_bad.csv`
- `artifacts/eval/after_fix.csv`

**Cau hoi then chot:** refund window (`q_refund_window`)

**Truoc (inject-bad):**

- `top1_doc_id=policy_refund_v4`
- `contains_expected=yes`
- `hits_forbidden=yes`
- `top_k_used=3`

**Sau (after-fix):**

- `top1_doc_id=policy_refund_v4`
- `contains_expected=yes`
- `hits_forbidden=no`
- `top_k_used=3`

Ket luan: Sau khi fix va publish lai, context stale trong top-k da bien mat (`hits_forbidden: yes -> no`).

**Merit (khuyen nghi):** versioning HR — `q_leave_version`

**Truoc:** `contains_expected=yes`, `hits_forbidden=no`, `top1_doc_expected=yes`  
**Sau:** `contains_expected=yes`, `hits_forbidden=no`, `top1_doc_expected=yes`

Ket luan: Case HR on dinh o ca 2 scenario, khong bi hoi quy.

---

## 3. Freshness & monitor

Tu log pipeline:

- `freshness_check=FAIL` trong ca 2 run.
- Ly do: `freshness_sla_exceeded`, `latest_exported_at=2026-04-10T08:00:00`, `sla_hours=24.0`.
- Age quan sat:
  - inject-bad: `age_hours=120.897`
  - after-fix: `age_hours=120.908`

Giai thich: FAIL freshness do raw export cu hon SLA, khong phai loi retrieval pipeline. Sprint 3 van hop le vi muc tieu la chung minh before/after tren retrieval khi inject/fix.

---

## 4. Corruption inject (Sprint 3)

Cach inject da thuc hien:

- Chay: `python etl_pipeline.py run --run-id sprint3-inject-bad --no-refund-fix --skip-validate`
- Tac dong ky vong:
  - Tat fix refund 14->7 (`--no-refund-fix`) de tao stale chunk.
  - Van cho embed du expectation fail (`--skip-validate`) de mo phong publish loi co chu dich.

Cach phat hien:

- Log fail expectation: `refund_no_stale_14d_window FAIL (violations=1)`.
- Eval retrieval cho `q_refund_window` co `hits_forbidden=yes`.

Cach khac phuc:

- Chay lai clean flow: `python etl_pipeline.py run --run-id sprint3-after-fix`
- Re-eval: `python eval_retrieval.py --out artifacts/eval/after_fix.csv`
- Ket qua: `q_refund_window` tro ve `hits_forbidden=no`.

---

## 5. Han che & viec chua lam

- Chua dat freshness SLA vi sample raw co `exported_at` cu.
- Chua tong hop noi dung nay vao `reports/group_report.md`.
- Chua bo sung dashboard/canh bao tu dong cho freshness (moi o muc log/manifest).
