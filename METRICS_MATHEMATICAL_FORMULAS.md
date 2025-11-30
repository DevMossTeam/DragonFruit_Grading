# Mathematical Formulas - Classification Metrics

## 1. CONFUSION MATRIX

For 3-class problem (A, B, C), we have a 3×3 matrix:

```
CM[i,j] where:
- i = true label (0=A, 1=B, 2=C)
- j = predicted label (0=A, 1=B, 2=C)
```

### Matrix Structure:

$$\text{CM} = \begin{pmatrix} 
n_{AA} & n_{AB} & n_{AC} \\
n_{BA} & n_{BB} & n_{BC} \\
n_{CA} & n_{CB} & n_{CC}
\end{pmatrix}$$

Where $n_{ij}$ = number of samples with true label $i$ predicted as label $j$

---

## 2. ACCURACY

The percentage of correct predictions across all classes.

### Formula:

$$\text{Accuracy} = \frac{\text{Total Correct Predictions}}{\text{Total Samples}} = \frac{\sum_{i=0}^{n-1} n_{ii}}{\sum_{i,j} n_{ij}}$$

For 3 classes (A, B, C):

$$\text{Accuracy} = \frac{n_{AA} + n_{BB} + n_{CC}}{N}$$

Where:
- $n_{AA}$ = correctly predicted A (True Positive for A)
- $n_{BB}$ = correctly predicted B (True Positive for B)
- $n_{CC}$ = correctly predicted C (True Positive for C)
- $N$ = total number of samples

### Range: 0 to 1 (0% to 100%)

### Example:
$$\text{Accuracy} = \frac{8 + 9 + 5}{23} = \frac{22}{23} = 0.9565 \approx 95.65\%$$

---

## 3. PRECISION (Per-class)

The accuracy of positive predictions for a specific class.

### Formula:

$$\text{Precision}_c = \frac{TP_c}{TP_c + FP_c}$$

Where for class $c$:
- $TP_c$ = True Positives (correctly predicted as class $c$)
- $FP_c$ = False Positives (predicted as class $c$, but wasn't)

### For our system:

$$\text{Precision}_A = \frac{n_{AA}}{n_{AA} + n_{BA} + n_{CA}}$$

This counts:
- Numerator: samples correctly predicted as A
- Denominator: ALL samples predicted as A (regardless if correct)

### Example:
$$\text{Precision}_A = \frac{8}{8 + 1 + 0} = \frac{8}{9} = 0.8889 \approx 88.89\%$$

### Interpretation:
"When the model predicts Grade A, it's correct 88.89% of the time"

### Range: 0 to 1

---

## 4. RECALL (Per-class)

The ability to find all positive samples of a specific class.

### Formula:

$$\text{Recall}_c = \frac{TP_c}{TP_c + FN_c}$$

Where for class $c$:
- $TP_c$ = True Positives (correctly found)
- $FN_c$ = False Negatives (missed, predicted as something else)

### For our system:

$$\text{Recall}_A = \frac{n_{AA}}{n_{AA} + n_{AB} + n_{AC}}$$

This counts:
- Numerator: samples correctly predicted as A
- Denominator: ALL actually A samples (regardless if found correctly)

### Example:
$$\text{Recall}_A = \frac{8}{8 + 1 + 0} = \frac{8}{9} = 0.8889 \approx 88.89\%$$

### Interpretation:
"Out of all actual Grade A fruits, the model finds 88.89%"

### Range: 0 to 1

---

## 5. F1-SCORE (Per-class)

The harmonic mean of Precision and Recall. Provides a single metric that balances both.

### Formula:

$$F1_c = 2 \times \frac{\text{Precision}_c \times \text{Recall}_c}{\text{Precision}_c + \text{Recall}_c}$$

### Alternative form (direct from confusion matrix):

$$F1_c = \frac{2 \times TP_c}{2 \times TP_c + FP_c + FN_c}$$

### Example:

Let $\text{Precision}_A = 0.8889$ and $\text{Recall}_A = 0.8889$

$$F1_A = 2 \times \frac{0.8889 \times 0.8889}{0.8889 + 0.8889}$$

$$F1_A = 2 \times \frac{0.7901}{1.7778}$$

$$F1_A = \frac{1.5802}{1.7778} = 0.8889 \approx 88.89\%$$

### Range: 0 to 1

### Why Harmonic Mean?
- Arithmetic mean: $(0.5 + 0.9) / 2 = 0.7$ (misleading)
- Harmonic mean: $2/(1/0.5 + 1/0.9) \approx 0.64$ (penalizes imbalance)
- Ensures both metrics contribute equally

---

## 6. MACRO AVERAGING

Average of metrics across all classes with equal weight.

### Formula:

$$\text{Macro}_{\text{metric}} = \frac{1}{K} \sum_{c=1}^{K} \text{metric}_c$$

Where $K$ = number of classes (3 in our case: A, B, C)

### For Precision:

$$\text{Macro Precision} = \frac{\text{Precision}_A + \text{Precision}_B + \text{Precision}_C}{3}$$

### For F1-Score:

$$\text{Macro F1} = \frac{F1_A + F1_B + F1_C}{3}$$

### Example:

$$\text{Macro F1} = \frac{0.8889 + 0.8947 + 0.9231}{3} = \frac{2.7067}{3} = 0.9022 \approx 90.22\%$$

### When to use:
- When all classes are equally important
- When you want a single overall performance metric
- Useful when classes are balanced

---

## 7. WEIGHTED AVERAGING

Average of metrics weighted by class frequency.

### Formula:

$$\text{Weighted}_{\text{metric}} = \sum_{c=1}^{K} \text{metric}_c \times \frac{n_c}{N}$$

Where:
- $\text{metric}_c$ = metric for class $c$
- $n_c$ = number of samples in class $c$
- $N$ = total number of samples

### For F1-Score:

$$\text{Weighted F1} = \sum_{c=1}^{3} F1_c \times \frac{n_c}{N}$$

### Example:

Assume:
- 100 samples of A with $F1_A = 0.8889$
- 80 samples of B with $F1_B = 0.8947$
- 20 samples of C with $F1_C = 0.9231$
- Total: 200 samples

$$\text{Weighted F1} = (0.8889 \times \frac{100}{200}) + (0.8947 \times \frac{80}{200}) + (0.9231 \times \frac{20}{200})$$

$$= (0.8889 \times 0.5) + (0.8947 \times 0.4) + (0.9231 \times 0.1)$$

$$= 0.4445 + 0.3579 + 0.0923$$

$$= 0.8947 \approx 89.47\%$$

### When to use:
- When classes are imbalanced (unequal number of samples)
- Better reflects real-world performance with imbalanced data
- More representative than macro average for imbalanced datasets

---

## 8. COMPARISON TABLE

| Metric | Formula | Range | Use Case |
|--------|---------|-------|----------|
| **Accuracy** | $\frac{\sum n_{ii}}{N}$ | [0,1] | Overall performance |
| **Precision** | $\frac{TP}{TP+FP}$ | [0,1] | Avoid false positives |
| **Recall** | $\frac{TP}{TP+FN}$ | [0,1] | Avoid false negatives |
| **F1-Score** | $\frac{2TP}{2TP+FP+FN}$ | [0,1] | Balance precision/recall |
| **Macro Avg** | $\frac{1}{K}\sum metric_c$ | [0,1] | Equal importance to classes |
| **Weighted Avg** | $\sum metric_c \times \frac{n_c}{N}$ | [0,1] | Account for imbalance |

---

## 9. SPECIFIC TO DRAGON FRUIT SYSTEM

### Ground Truth Conversion:

$$\text{true\_grade} = \begin{cases}
A & \text{if } \text{weight\_actual\_g} \geq 600 \\
B & \text{if } 300 \leq \text{weight\_actual\_g} < 600 \\
C & \text{if } \text{weight\_actual\_g} < 300 \\
\text{null} & \text{if } \text{weight\_actual\_g} \text{ is missing}
\end{cases}$$

### Comparison:

$$\text{Metrics} = \text{compare}(\text{y\_true, y\_pred})$$

Where:
- $\text{y\_true}$ = grades from weight (ground truth)
- $\text{y\_pred}$ = grades from fuzzy logic (predictions)

This tells us: **How well does fuzzy logic match weight-based grading?**

---

## 10. EXAMPLE FULL CALCULATION

Given confusion matrix:
$$CM = \begin{pmatrix} 
8 & 1 & 0 \\
1 & 9 & 0 \\
0 & 1 & 5
\end{pmatrix}$$

### Per-class metrics:

**Grade A:**
$$\text{Precision}_A = \frac{8}{8+1+0} = 0.8889$$
$$\text{Recall}_A = \frac{8}{8+1+0} = 0.8889$$
$$F1_A = \frac{2 \times 0.8889 \times 0.8889}{0.8889+0.8889} = 0.8889$$

**Grade B:**
$$\text{Precision}_B = \frac{9}{9+1+1} = 0.8182$$
$$\text{Recall}_B = \frac{9}{1+9+0} = 0.9000$$
$$F1_B = \frac{2 \times 0.8182 \times 0.9000}{0.8182+0.9000} = 0.8571$$

**Grade C:**
$$\text{Precision}_C = \frac{5}{5+0+1} = 0.8333$$
$$\text{Recall}_C = \frac{5}{0+0+5} = 1.0000$$
$$F1_C = \frac{2 \times 0.8333 \times 1.0000}{0.8333+1.0000} = 0.9091$$

### Overall metrics:

$$\text{Accuracy} = \frac{8+9+5}{23} = 0.9565$$

$$\text{Macro F1} = \frac{0.8889 + 0.8571 + 0.9091}{3} = 0.8850$$

$$\text{Macro Precision} = \frac{0.8889 + 0.8182 + 0.8333}{3} = 0.8468$$

$$\text{Macro Recall} = \frac{0.8889 + 0.9000 + 1.0000}{3} = 0.9296$$
