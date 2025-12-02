# Classification Metrics Formulas Guide
# For Dragon Fruit Grading System

## 1️⃣ CONFUSION MATRIX

The foundation of all classification metrics. A 3×3 matrix for grades A, B, C.

```
                    PREDICTED
                 A      B      C
TRUE         A  [TP_A  FP_B  FP_C]
LABELS       B  [FN_A  TP_B  FP_C]
             C  [FN_A  FN_B  TP_C]
```

**Where:**
- **TP (True Positive)** = Correctly predicted (diagonal)
- **FP (False Positive)** = Predicted as grade X, but was different
- **FN (False Negative)** = Should be grade X, but predicted as different
- **TN (True Negative)** = Not applicable for multi-class (3+ classes)

**Example with real numbers:**
```
          Predicted
       A    B    C
True A [8    1    0]    ← 8 correct A's, 1 predicted as B, 0 as C
     B [1    9    0]    ← 1 predicted as A, 9 correct B's, 0 as C
     C [0    1    5]    ← 0 predicted as A, 1 as B, 5 correct C's
```

---

## 2️⃣ ACCURACY (Overall Correctness)

### Formula:
```
           Correct Predictions
Accuracy = ───────────────────────────
           Total Samples

          TP_A + TP_B + TP_C
        = ──────────────────────────
          Total All Samples
```

### Example:
```
Correct: 8 (A) + 9 (B) + 5 (C) = 22
Total:   23 samples
Accuracy = 22/23 = 0.9565 (95.65%)
```

**Interpretation:** Out of 23 samples, 95.65% were classified correctly.

---

## 3️⃣ PRECISION (False Positive Rate)

### Formula:
```
             True Positives for Class X
Precision_X = ────────────────────────────────────
              All Predicted as Class X

             TP_X
           = ──────────────────
             TP_X + FP_X
```

### Example (for Grade A):
```
Grade A Precision = TP_A / (TP_A + all FP_A)
                  = 8 / (8 + 1)  [1 is from B→A]
                  = 8 / 9
                  = 0.8889 (88.89%)
```

**Interpretation:** When the model predicts Grade A, it's correct 88.89% of the time.

**Use Case:** Important when false positives are costly
- e.g., Don't want to mark low-quality fruit as premium (Grade A)

---

## 4️⃣ RECALL (False Negative Rate)

### Formula:
```
            True Positives for Class X
Recall_X = ──────────────────────────────────
           All Actually Class X

            TP_X
          = ──────────────────
            TP_X + FN_X
```

### Example (for Grade A):
```
Grade A Recall = TP_A / (TP_A + all FN_A)
               = 8 / (8 + 0)  [0 A's were missed]
               = 8 / 8
               = 1.0000 (100%)
```

**Interpretation:** Out of all actual Grade A fruits, the model finds 100%.

**Use Case:** Important when false negatives are costly
- e.g., Don't want to miss premium Grade A fruits in batch

---

## 5️⃣ F1-SCORE (Precision-Recall Balance)

### Formula:
```
         2 × (Precision × Recall)
F1_X = ─────────────────────────────
           Precision + Recall

         2 × (TP_X)
       = ──────────────────────────────
         2×TP_X + FP_X + FN_X
```

### Example (for Grade A):
```
Precision_A = 8/9 = 0.8889
Recall_A = 8/8 = 1.0000

F1_A = 2 × (0.8889 × 1.0000)
     = ────────────────────────
       0.8889 + 1.0000
     = 1.7778 / 1.8889
     = 0.9412 (94.12%)
```

**Interpretation:** Balanced score between precision and recall.

**Use Case:** When you need balance between:
- Not marking low-quality as premium (Precision)
- Not missing premium fruits (Recall)

---

## 6️⃣ MACRO-AVERAGING (Equal weight to all classes)

### Formula:
```
         Metric_A + Metric_B + Metric_C
Macro = ───────────────────────────────
                 3
```

### Example:
```
Precision_A = 0.8889
Precision_B = 0.9000
Precision_C = 1.0000

Macro Precision = (0.8889 + 0.9000 + 1.0000) / 3
                = 2.7889 / 3
                = 0.9296 (92.96%)
```

**Interpretation:** Average performance across all grades.

**Use Case:** When all classes are equally important

---

## 7️⃣ WEIGHTED-AVERAGING (Weight by class frequency)

### Formula:
```
           (Metric_A × Count_A) + (Metric_B × Count_B) + ...
Weighted = ────────────────────────────────────────────────
           Total Samples
```

### Example:
```
If you have:
- 100 samples Grade A
- 80 samples Grade B
- 20 samples Grade C
Total = 200

Weighted F1 = (F1_A × 100) + (F1_B × 80) + (F1_C × 20)
            = ─────────────────────────────────────────
                        200
```

**Interpretation:** Performance considering class imbalance.

**Use Case:** When some grades appear more frequently in real data

---

## 📊 YOUR CODE'S IMPLEMENTATION

In `metrics_service.py`, line 118-135:

```python
# Overall metrics using sklearn
accuracy = accuracy_score(y_true, y_pred)
macro_precision = precision_score(y_true, y_pred, average='macro')
macro_recall = recall_score(y_true, y_pred, average='macro')
macro_f1 = f1_score(y_true, y_pred, average='macro')
weighted_f1 = f1_score(y_true, y_pred, average='weighted')

# Per-class metrics (A, B, C)
for grade in ["A", "B", "C"]:
    precision = precision_score(y_true, y_pred, labels=[grade], average=None)[0]
    recall = recall_score(y_true, y_pred, labels=[grade], average=None)[0]
    f1 = f1_score(y_true, y_pred, labels=[grade], average=None)[0]
```

---

## 🎯 YOUR SYSTEM'S COMPARISON

**What your code compares:**

```
y_true (Ground Truth) ← Grade from weight_actual_g
vs
y_pred (Prediction) ← Grade from fuzzy logic

Using thresholds:
A: >= 600g
B: 300-600g
C: < 300g
```

---

## 📈 INTERPRETATION TABLE

| Metric | Range | Meaning |
|--------|-------|---------|
| **Accuracy** | 0-1 | Overall correctness (all classes) |
| **Precision** | 0-1 | When we predict X, how often is it correct? |
| **Recall** | 0-1 | Of all actual X, how many did we find? |
| **F1** | 0-1 | Balance between precision & recall |
| **Macro Avg** | 0-1 | Average of all classes equally |
| **Weighted Avg** | 0-1 | Average weighted by class frequency |

---

## ✅ EXAMPLE REPORT

```
Confusion Matrix:
     A    B    C
A  [[80   15    5]   ← Grade A predictions
B   [10   70   20]   ← Grade B predictions
C   [ 5   10   85]]  ← Grade C predictions

Metrics:
  Accuracy: 0.7833 (78.33% correct overall)
  
  Grade A:
    Precision: 0.8235 (82% of A predictions correct)
    Recall: 0.8000 (80% of actual A found)
    F1: 0.8116
  
  Grade B:
    Precision: 0.7368 (73.68% of B predictions correct)
    Recall: 0.7000 (70% of actual B found)
    F1: 0.7179
  
  Grade C:
    Precision: 0.8949 (89.49% of C predictions correct)
    Recall: 0.8500 (85% of actual C found)
    F1: 0.8717
  
  Overall:
    Macro F1: 0.8337 (average of all 3 grades)
    Weighted F1: 0.7988 (weighted by frequency)
```

---

## 🔍 KEY INSIGHTS FOR YOUR SYSTEM

1. **High Accuracy (>0.90)** = System is working well overall
2. **High Precision for Grade A** = Premium fruits not mislabeled as regular
3. **High Recall for Grade A** = All premium fruits correctly identified
4. **Balanced F1** = Good balance in not missing or mislabeling

This helps you understand:
- ✅ Is the fuzzy logic system accurate?
- ✅ Does it correctly identify premium Grade A?
- ✅ Are low-quality fruits properly classified?
