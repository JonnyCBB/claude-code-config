# Evaluation Patterns

Metrics and evaluation strategies for ML models.

> **Related**: For logging these metrics, distributed evaluation, and Ray Train integration, see [evaluation-patterns.md](../evaluation-patterns.md).

## Classification Metrics

### Binary Classification
```python
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    average_precision_score,
)

def evaluate_binary_classification(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_prob: np.ndarray,
) -> dict[str, float]:
    return {
        "accuracy": accuracy_score(y_true, y_pred),
        "precision": precision_score(y_true, y_pred),
        "recall": recall_score(y_true, y_pred),
        "f1": f1_score(y_true, y_pred),
        "auc_roc": roc_auc_score(y_true, y_prob),
        "auc_pr": average_precision_score(y_true, y_prob),
    }
```

### Multi-class Classification
```python
def evaluate_multiclass(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_prob: np.ndarray,
) -> dict[str, float]:
    return {
        "accuracy": accuracy_score(y_true, y_pred),
        "macro_f1": f1_score(y_true, y_pred, average="macro"),
        "weighted_f1": f1_score(y_true, y_pred, average="weighted"),
        "auc_roc_ovr": roc_auc_score(y_true, y_prob, multi_class="ovr"),
    }
```

## Ranking Metrics

Ranking metrics evaluate how well a model orders items. These are crucial for search, recommendations, and retrieval systems.

### DCG (Discounted Cumulative Gain)
```python
def dcg_at_k(relevances: list[float], k: int) -> float:
    """Calculate DCG@k - sum of relevances weighted by position."""
    relevances = np.array(relevances)[:k]
    if len(relevances) == 0:
        return 0.0

    # Position discount: log2(position + 1)
    discounts = np.log2(np.arange(len(relevances)) + 2)
    return np.sum((2**relevances - 1) / discounts)
```

### IDCG (Ideal DCG)
```python
def idcg_at_k(relevances: list[float], k: int) -> float:
    """Calculate IDCG@k - best possible DCG with optimal ordering."""
    # Sort by relevance descending for ideal ordering
    ideal_order = np.sort(relevances)[::-1][:k]
    return dcg_at_k(ideal_order.tolist(), k)
```

### NDCG (Normalized Discounted Cumulative Gain)
```python
def ndcg_at_k(relevances: list[float], k: int) -> float:
    """Calculate NDCG@k = DCG@k / IDCG@k."""
    relevances = np.array(relevances)[:k]

    dcg = dcg_at_k(relevances.tolist(), k)
    idcg = idcg_at_k(relevances.tolist(), k)

    if idcg == 0:
        return 0.0
    return dcg / idcg
```

### MRR (Mean Reciprocal Rank)
```python
def mrr(ranked_lists: list[list[int]], relevant_items: list[set[int]]) -> float:
    """Calculate Mean Reciprocal Rank - average of 1/position of first relevant item."""
    reciprocal_ranks = []

    for ranking, relevant in zip(ranked_lists, relevant_items):
        for i, item in enumerate(ranking):
            if item in relevant:
                reciprocal_ranks.append(1.0 / (i + 1))
                break
        else:
            reciprocal_ranks.append(0.0)

    return np.mean(reciprocal_ranks)
```

### Precision@K
```python
def precision_at_k(
    predictions: list[list[int]],
    ground_truth: list[set[int]],
    k: int,
) -> float:
    """Calculate Precision@k - fraction of top-k items that are relevant."""
    precisions = []
    for pred, true in zip(predictions, ground_truth):
        top_k = pred[:k]
        relevant_in_top_k = sum(1 for item in top_k if item in true)
        precisions.append(relevant_in_top_k / k)
    return np.mean(precisions)
```

### Recall@K
```python
def recall_at_k(
    predictions: list[list[int]],
    ground_truth: list[set[int]],
    k: int,
) -> float:
    """Calculate Recall@k - fraction of relevant items that appear in top-k."""
    recalls = []
    for pred, true in zip(predictions, ground_truth):
        if len(true) == 0:
            recalls.append(0.0)
            continue
        top_k = pred[:k]
        relevant_in_top_k = sum(1 for item in top_k if item in true)
        recalls.append(relevant_in_top_k / len(true))
    return np.mean(recalls)
```

### MAP@K (Mean Average Precision)
```python
def average_precision_at_k(
    prediction: list[int],
    ground_truth: set[int],
    k: int,
) -> float:
    """Calculate Average Precision@k for a single query."""
    if len(ground_truth) == 0:
        return 0.0

    prediction = prediction[:k]
    precisions = []
    num_relevant = 0

    for i, item in enumerate(prediction):
        if item in ground_truth:
            num_relevant += 1
            precisions.append(num_relevant / (i + 1))

    if len(precisions) == 0:
        return 0.0

    # Normalize by min(k, |ground_truth|)
    return sum(precisions) / min(k, len(ground_truth))


def map_at_k(
    predictions: list[list[int]],
    ground_truth: list[set[int]],
    k: int,
) -> float:
    """Calculate Mean Average Precision@k across all queries."""
    aps = [
        average_precision_at_k(pred, true, k)
        for pred, true in zip(predictions, ground_truth)
    ]
    return np.mean(aps)
```

### Hit Rate
```python
def hit_rate_at_k(
    predictions: list[list[int]],
    ground_truth: list[set[int]],
    k: int,
) -> float:
    """Calculate Hit Rate@k - fraction of queries with at least one relevant in top-k."""
    hits = 0
    for pred, true in zip(predictions, ground_truth):
        if any(item in true for item in pred[:k]):
            hits += 1
    return hits / len(predictions)
```

### Full Ranking Evaluation
```python
def evaluate_ranking(
    predictions: list[list[int]],
    ground_truth: list[set[int]],
    relevances: list[list[float]],
    k_values: list[int] = [5, 10, 20],
) -> dict[str, float]:
    """Comprehensive ranking evaluation with all metrics."""
    metrics = {}

    for k in k_values:
        metrics[f"hit_rate@{k}"] = hit_rate_at_k(predictions, ground_truth, k)
        metrics[f"precision@{k}"] = precision_at_k(predictions, ground_truth, k)
        metrics[f"recall@{k}"] = recall_at_k(predictions, ground_truth, k)
        metrics[f"map@{k}"] = map_at_k(predictions, ground_truth, k)
        metrics[f"mrr@{k}"] = mrr(
            [p[:k] for p in predictions],
            ground_truth
        )
        metrics[f"ndcg@{k}"] = np.mean([
            ndcg_at_k(rel, k) for rel in relevances
        ])

    return metrics
```

### Ranking Metrics Summary Table

| Metric | Range | Interpretation | Use Case |
|--------|-------|----------------|----------|
| **MRR** | [0, 1] | Higher = first relevant item ranks higher | Single relevant item, navigational queries |
| **NDCG@K** | [0, 1] | Higher = relevant items rank higher | Graded relevance, search results |
| **Precision@K** | [0, 1] | Higher = more relevant in top-k | When k items shown |
| **Recall@K** | [0, 1] | Higher = more relevant found | Coverage of relevant items |
| **MAP@K** | [0, 1] | Higher = precision at each relevant item | When order of relevance matters |
| **Hit Rate@K** | [0, 1] | Higher = more queries with a hit | Binary relevance, quick success |
| **DCG@K** | [0, ∞) | Higher = better weighted sum | Raw score (use NDCG for comparison) |

### Production Evaluation

For production use with distributed computation:
- Use **torchmetrics** for PyTorch - see [evaluation-patterns.md](../evaluation-patterns.md#torchmetrics-for-pytorch)

## Regression Metrics

```python
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

def evaluate_regression(
    y_true: np.ndarray,
    y_pred: np.ndarray,
) -> dict[str, float]:
    return {
        "mse": mean_squared_error(y_true, y_pred),
        "rmse": np.sqrt(mean_squared_error(y_true, y_pred)),
        "mae": mean_absolute_error(y_true, y_pred),
        "r2": r2_score(y_true, y_pred),
    }
```

## Embedding Quality

### Nearest Neighbor Accuracy
```python
from sklearn.neighbors import NearestNeighbors

def nn_accuracy(
    embeddings: np.ndarray,
    labels: np.ndarray,
    k: int = 10,
) -> float:
    """Check if nearest neighbors have same label."""
    nn = NearestNeighbors(n_neighbors=k + 1)
    nn.fit(embeddings)
    _, indices = nn.kneighbors(embeddings)

    correct = 0
    for i, neighbors in enumerate(indices):
        neighbor_labels = labels[neighbors[1:]]  # Exclude self
        if labels[i] in neighbor_labels:
            correct += 1

    return correct / len(labels)
```

### Embedding Space Visualization
```python
from sklearn.manifold import TSNE
import matplotlib.pyplot as plt

def visualize_embeddings(
    embeddings: np.ndarray,
    labels: np.ndarray,
    save_path: str,
) -> None:
    tsne = TSNE(n_components=2, random_state=42)
    reduced = tsne.fit_transform(embeddings)

    plt.figure(figsize=(10, 10))
    scatter = plt.scatter(
        reduced[:, 0],
        reduced[:, 1],
        c=labels,
        cmap="tab10",
        alpha=0.6,
    )
    plt.colorbar(scatter)
    plt.savefig(save_path)
    plt.close()
```

## Fairness Metrics

```python
def evaluate_fairness(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    sensitive_attribute: np.ndarray,
) -> dict[str, float]:
    """Evaluate fairness across groups defined by sensitive attribute."""
    groups = np.unique(sensitive_attribute)
    metrics = {}

    # Per-group performance
    for group in groups:
        mask = sensitive_attribute == group
        metrics[f"accuracy_group_{group}"] = accuracy_score(
            y_true[mask], y_pred[mask]
        )

    # Demographic parity difference
    predictions_by_group = {
        group: y_pred[sensitive_attribute == group].mean()
        for group in groups
    }
    max_diff = max(predictions_by_group.values()) - min(predictions_by_group.values())
    metrics["demographic_parity_diff"] = max_diff

    # Equal opportunity difference
    for group in groups:
        mask = (sensitive_attribute == group) & (y_true == 1)
        metrics[f"tpr_group_{group}"] = y_pred[mask].mean()

    return metrics
```

## Online Evaluation

### A/B Test Metrics
```python
from scipy import stats

def analyze_ab_test(
    control_values: np.ndarray,
    treatment_values: np.ndarray,
    alpha: float = 0.05,
) -> dict:
    """Analyze A/B test results."""
    control_mean = control_values.mean()
    treatment_mean = treatment_values.mean()
    lift = (treatment_mean - control_mean) / control_mean

    # T-test
    t_stat, p_value = stats.ttest_ind(treatment_values, control_values)

    return {
        "control_mean": control_mean,
        "treatment_mean": treatment_mean,
        "lift": lift,
        "p_value": p_value,
        "significant": p_value < alpha,
    }
```

## Best Practices

1. **Use appropriate metrics**: Choose metrics aligned with business goals
2. **Report multiple metrics**: Don't rely on a single number
3. **Confidence intervals**: Report uncertainty in estimates
4. **Stratified evaluation**: Evaluate across segments
5. **Baseline comparison**: Always compare to baselines
6. **Statistical significance**: Use proper statistical tests
