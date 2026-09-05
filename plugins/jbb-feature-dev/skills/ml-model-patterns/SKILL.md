---
name: ml-model-patterns
description: >
  Common ML model patterns. Covers model architecture, training patterns,
  evaluation metrics, and production considerations. Use when (1) reviewing ML training
  code, (2) discussing model architecture choices, (3) evaluating metrics or evaluation
  strategies, or (4) discussing production ML considerations like serving latency or
  model size tradeoffs.
allowed-tools:
  - Read
---

# ML Model Patterns

Common patterns for machine learning models across teams.

## Quick Reference

### Common Model Types

| Type           | Use Case                   | Framework              |
| -------------- | -------------------------- | ---------------------- |
| Ranking        | Search, recommendations    | PyTorch/TensorFlow     |
| Classification | Content moderation, intent | PyTorch                |
| Embeddings     | User/item similarity       | PyTorch                |
| Sequence       | Playlist generation        | PyTorch (Transformers) |
| Regression     | Engagement prediction      | XGBoost/PyTorch        |

### Model Serving Considerations

- Latency requirements (p50, p99)
- Throughput needs
- Model size constraints
- Feature dependencies

## Skill Files

1. **[architecture-patterns.md](architecture-patterns.md)** - Common model architectures
2. **[training-patterns.md](training-patterns.md)** - Training best practices
3. **[evaluation-patterns.md](evaluation-patterns.md)** - Metrics and evaluation
4. **[production-patterns.md](production-patterns.md)** - Production considerations
5. **[troubleshooting.md](troubleshooting.md)** - Common issues
6. **[testing-patterns.md](testing-patterns.md)** - Framework-agnostic testing

## Model Selection Guide

```
┌─────────────────────────────────────────────────────────────┐
│                    Model Selection                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Structured Data                 Sequential Data            │
│  ┌───────────────┐               ┌───────────────┐         │
│  │   XGBoost/    │               │  Transformer  │         │
│  │   LightGBM    │               │  LSTM/GRU     │         │
│  └───────────────┘               └───────────────┘         │
│         │                               │                   │
│         ▼                               ▼                   │
│  High interpretability           Sequential patterns        │
│  Fast inference                  Variable length input      │
│                                                              │
│  Dense Features                  Sparse Features            │
│  ┌───────────────┐               ┌───────────────┐         │
│  │     MLP       │               │   Two-Tower   │         │
│  │    (DNN)      │               │   Embeddings  │         │
│  └───────────────┘               └───────────────┘         │
│         │                               │                   │
│         ▼                               ▼                   │
│  Continuous features             High cardinality           │
│  Non-linear relationships        User/item matching         │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Common Architectures

### Two-Tower Model (Recommendations)

```python
class TwoTowerModel(nn.Module):
    def __init__(self, user_dim, item_dim, embedding_dim):
        super().__init__()
        self.user_tower = nn.Sequential(
            nn.Linear(user_dim, 256),
            nn.ReLU(),
            nn.Linear(256, embedding_dim),
        )
        self.item_tower = nn.Sequential(
            nn.Linear(item_dim, 256),
            nn.ReLU(),
            nn.Linear(256, embedding_dim),
        )

    def forward(self, user_features, item_features):
        user_embedding = self.user_tower(user_features)
        item_embedding = self.item_tower(item_features)
        return torch.sum(user_embedding * item_embedding, dim=-1)
```

### Transformer for Sequences

```python
class SequenceModel(nn.Module):
    def __init__(self, vocab_size, d_model, nhead, num_layers):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, d_model)
        encoder_layer = nn.TransformerEncoderLayer(d_model, nhead)
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers)
        self.fc = nn.Linear(d_model, vocab_size)

    def forward(self, x):
        x = self.embedding(x)
        x = self.transformer(x)
        return self.fc(x)
```

## Evaluation Checklist

- [ ] Offline metrics (AUC, NDCG, MRR)
- [ ] Online A/B test design
- [ ] Fairness evaluation
- [ ] Latency benchmarks
- [ ] Model size constraints
- [ ] Error analysis

## Production Readiness

### Pre-deployment

1. Model validated on holdout set
2. Latency meets SLA
3. Memory usage acceptable
4. Feature pipeline stable
5. Monitoring configured

### Post-deployment

1. A/B test running
2. Metrics dashboard available
3. Alerts configured
4. Rollback plan ready

## Documentation Links

- [ML Best Practices](https://your-internal-docs.example/)
