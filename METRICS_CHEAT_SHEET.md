# 📋 METRICS CHEAT SHEET - Dragon Fruit Grading System

## Quick Formulas

```
┌─────────────────────────────────────────────────────────────┐
│  CONFUSION MATRIX: 3×3 grid of Actual vs Predicted grades  │
│                                                             │
│           Predicted                                         │
│        A      B      C                                      │
│    A [TP_A  FP_B  FP_C]  ← Actual samples that are A       │
│    B [FN_A  TP_B  FP_C]  ← Actual samples that are B       │
│    C [FN_A  FN_B  TP_C]  ← Actual samples that are C       │
└─────────────────────────────────────────────────────────────┘

TP = True Positive (diagonal - correct predictions)
FP = False Positive (predicted wrong)
FN = False Negative (missed)
```

---

## 4 Main Metrics

### 1️⃣ ACCURACY
```
Formula:  Correct / Total
Example:  22 / 23 = 95.65%
Range:    0% to 100%
Judge by: > 85% is good
```

### 2️⃣ PRECISION
```
Formula:  TP / (TP + FP)
Example:  8 / (8+1) = 88.89%
Range:    0% to 100%
Judge by: > 85% means "rarely wrong when I predict A"
```

### 3️⃣ RECALL
```
Formula:  TP / (TP + FN)
Example:  8 / (8+1) = 88.89%
Range:    0% to 100%
Judge by: > 85% means "found most of the A's"
```

### 4️⃣ F1-SCORE
```
Formula:  2 × (Precision × Recall) / (Precision + Recall)
Example:  2 × (0.89 × 0.89) / (0.89 + 0.89) = 0.89
Range:    0% to 100%
Judge by: > 85% means "good at both precision AND recall"
```

---

## Quick Decision Tree

```
                    Look at Metrics
                           │
              ┌────────────┼────────────┐
              │            │            │
        Is Accuracy    Is Precision  Is Recall
         > 85%?         > 85%?        > 85%?
           YES            YES            YES
            │              │              │
            ▼              ▼              ▼
        ✅ Good!      ✅ Not          ✅ Not
                     mislabeling     missing
        
        System works    Be careful     Find all
        overall!        with Grade A   Grade A!
```

---

## Per-Class Analysis

### For each grade (A, B, C), you get:

| Grade | Precision | Recall | F1 | Problem? |
|-------|-----------|--------|----|----|
| A | High ✅ | Low ❌ | Mid ⚠️ | Missing Grade A |
| A | Low ❌ | High ✅ | Mid ⚠️ | Mislabeling as Grade A |
| A | High ✅ | High ✅ | High ✅ | No problem! |
| B | Low ❌ | Low ❌ | Low ❌ | Grade B is confused |
| C | High ✅ | High ✅ | High ✅ | No problem! |

---

## What the Numbers Mean

### Grade A is YOUR PREMIUM FRUIT

```
Precision_A = "How often am I RIGHT when I say Premium?"
If 95% → Good! Customers won't get angry
If 60% → Bad! Selling mediocre fruit as premium

Recall_A = "Do I FIND all premium fruit?"
If 95% → Good! Don't lose money on premium
If 60% → Bad! Underselling premium fruit
```

### Grade B is REGULAR FRUIT

```
Precision_B = "How often am I right about regular?"
If 90% → Good! Pricing is accurate
If 70% → Some get wrong grade

Recall_B = "Do I catch all regular fruit?"
If 90% → Good! Consistent grading
If 70% → Some slip into other grades
```

### Grade C is LOW-QUALITY FRUIT

```
Precision_C = "Am I right about low-quality?"
If 95% → Good! Not wasting premium prices on trash
If 60% → Bad! Underselling some fruit

Recall_C = "Do I find all low-quality?"
If 95% → Good! Customers won't complain
If 60% → Bad! Some bad fruit slips through
```

---

## Typical Good Performance

```
🎯 TARGET VALUES:

Accuracy:          > 0.90  (90%+)
Macro F1:          > 0.85  (85%+)
Weighted F1:       > 0.85  (85%+)

Per-class:
  Precision_A:     > 0.90
  Recall_A:        > 0.90
  F1_A:            > 0.90
  (same for B, C)
```

---

## Quick Fixes When Something is Low

### If Accuracy is low (<80%):
```
Problem: Overall system doesn't work
Fix: Check entire pipeline
  - Are thresholds correct?
  - Is fuzzy logic working?
  - Are weights accurate?
```

### If Precision_A is low (<75%):
```
Problem: Marking bad fruit as premium
Fix: Raise threshold for Grade A prediction
  - Make fuzzy logic stricter
  - Require higher score for "Grade A"
```

### If Recall_A is low (<75%):
```
Problem: Missing premium fruit
Fix: Lower threshold for Grade A prediction
  - Make fuzzy logic more lenient
  - Accept medium scores as "Grade A"
```

### If F1 score is low but Accuracy is high:
```
Problem: One or two grades are unbalanced
Fix: Focus on that grade
  - Rebalance fuzzy membership functions
  - Retune rules for problematic grade
```

---

## Example Report Reading

```
YOUR RESULTS:
{
  "accuracy": 0.9565,           ✅ GREAT! 95.65% correct
  "macro_f1": 0.8850,           ✅ GOOD! 88.5% balanced
  "weighted_f1": 0.8947,        ✅ GOOD! Accounts for imbalance
  
  "precision_A": 0.8889,        ✅ Right 88.89% when predicting A
  "recall_A": 0.8889,           ✅ Find 88.89% of real A's
  "f1_A": 0.8889,               ✅ Grade A is balanced
  
  "precision_B": 0.8182,        ⚠️  Right 81.82% when predicting B
  "recall_B": 0.9000,           ✅ Find 90% of real B's
  "f1_B": 0.8571,               ⚠️  Grade B needs improvement
  
  "precision_C": 0.8333,        ✅ Right 83.33% when predicting C
  "recall_C": 1.0000,           ✅✅ Find 100% of real C's!
  "f1_C": 0.9091,               ✅ Grade C works great!
  
  "confusion_matrix": [
    [8, 1, 0],   ← Grade A: 8 correct, 1 missed, 0 false
    [1, 9, 0],   ← Grade B: 9 correct, some confusion
    [0, 1, 5]    ← Grade C: 5 correct, 1 confusion from B
  ]
}

ANALYSIS:
✅ Overall system works (95.65% accuracy)
✅ Grade A is good (premium fruit identified well)
⚠️  Grade B has slight precision issue (sometimes marks B when not)
✅ Grade C is excellent (catches all low-quality)

ACTION: System is ready to deploy!
Minor: Consider tuning Grade B rules if needed
```

---

## Copy-Paste Formulas

```python
# If you need to implement from scratch:

# Accuracy
accuracy = (TP_A + TP_B + TP_C) / Total

# Precision per class
precision_A = TP_A / (TP_A + FP_A)

# Recall per class
recall_A = TP_A / (TP_A + FN_A)

# F1 per class
f1_A = 2 * (precision_A * recall_A) / (precision_A + recall_A)

# Macro average
macro_f1 = (f1_A + f1_B + f1_C) / 3

# Weighted average (if counts are n_A, n_B, n_C)
weighted_f1 = (f1_A * n_A + f1_B * n_B + f1_C * n_C) / Total
```

---

## Remember

| If you see... | It means... | Emoji |
|---|---|---|
| High Accuracy, High F1 | System works! | ✅ |
| High Accuracy, Low F1 | One grade is bad | ⚠️ |
| Low Accuracy | System broken | ❌ |
| High Precision, Low Recall | Too strict | 🚫 |
| Low Precision, High Recall | Too lenient | 🎯 |
| High Precision, High Recall | Perfect! | 🎉 |

---

## Files to Reference

- **METRICS_QUICK_REFERENCE.md** ← You are here
- **METRICS_FORMULAS_GUIDE.md** ← Detailed explanations
- **METRICS_VISUAL_GUIDE.md** ← Diagrams
- **METRICS_MATHEMATICAL_FORMULAS.md** ← Formal math
