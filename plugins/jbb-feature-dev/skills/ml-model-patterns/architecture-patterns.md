# Model Architecture Patterns

Common model architectures used.

## Two-Tower Models

### Overview
Two-tower models separately encode query and candidate entities, enabling efficient retrieval.

```
┌─────────────┐    ┌─────────────┐
│  User Tower │    │ Item Tower  │
│             │    │             │
│   Dense     │    │   Dense     │
│   Layers    │    │   Layers    │
│             │    │             │
└──────┬──────┘    └──────┬──────┘
       │                  │
       ▼                  ▼
   User Embedding    Item Embedding
       │                  │
       └────────┬─────────┘
                │
         Dot Product / Cosine
                │
                ▼
             Score
```

### Implementation
```python
import torch
import torch.nn as nn

class TwoTowerModel(nn.Module):
    def __init__(
        self,
        user_features_dim: int,
        item_features_dim: int,
        embedding_dim: int = 128,
        hidden_dims: list[int] = [256, 128],
    ):
        super().__init__()

        # User tower
        user_layers = []
        in_dim = user_features_dim
        for hidden_dim in hidden_dims:
            user_layers.extend([
                nn.Linear(in_dim, hidden_dim),
                nn.ReLU(),
                nn.BatchNorm1d(hidden_dim),
            ])
            in_dim = hidden_dim
        user_layers.append(nn.Linear(in_dim, embedding_dim))
        self.user_tower = nn.Sequential(*user_layers)

        # Item tower (similar structure)
        item_layers = []
        in_dim = item_features_dim
        for hidden_dim in hidden_dims:
            item_layers.extend([
                nn.Linear(in_dim, hidden_dim),
                nn.ReLU(),
                nn.BatchNorm1d(hidden_dim),
            ])
            in_dim = hidden_dim
        item_layers.append(nn.Linear(in_dim, embedding_dim))
        self.item_tower = nn.Sequential(*item_layers)

    def forward(
        self,
        user_features: torch.Tensor,
        item_features: torch.Tensor,
    ) -> torch.Tensor:
        user_embedding = self.user_tower(user_features)
        item_embedding = self.item_tower(item_features)

        # Normalize for cosine similarity
        user_embedding = nn.functional.normalize(user_embedding, p=2, dim=-1)
        item_embedding = nn.functional.normalize(item_embedding, p=2, dim=-1)

        # Dot product
        return torch.sum(user_embedding * item_embedding, dim=-1)
```

### Use Cases
- Recommendation retrieval
- Search query-document matching
- Similar item finding

## Transformer Models

### Sequence Modeling
```python
class SequenceTransformer(nn.Module):
    def __init__(
        self,
        vocab_size: int,
        d_model: int = 256,
        nhead: int = 8,
        num_layers: int = 4,
        max_seq_len: int = 512,
    ):
        super().__init__()

        self.embedding = nn.Embedding(vocab_size, d_model)
        self.pos_encoding = nn.Embedding(max_seq_len, d_model)

        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=nhead,
            dim_feedforward=d_model * 4,
            batch_first=True,
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers)

        self.fc_out = nn.Linear(d_model, vocab_size)

    def forward(
        self,
        x: torch.Tensor,
        mask: torch.Tensor | None = None,
    ) -> torch.Tensor:
        seq_len = x.size(1)
        positions = torch.arange(seq_len, device=x.device).unsqueeze(0)

        x = self.embedding(x) + self.pos_encoding(positions)
        x = self.transformer(x, src_key_padding_mask=mask)
        return self.fc_out(x)
```

### Use Cases
- Playlist continuation
- Session modeling
- Sequential recommendations

## Multi-Task Models

### Shared Bottom
```python
class MultiTaskModel(nn.Module):
    def __init__(
        self,
        input_dim: int,
        shared_dims: list[int],
        task_dims: list[int],
        num_tasks: int,
    ):
        super().__init__()

        # Shared layers
        shared_layers = []
        in_dim = input_dim
        for dim in shared_dims:
            shared_layers.extend([
                nn.Linear(in_dim, dim),
                nn.ReLU(),
            ])
            in_dim = dim
        self.shared = nn.Sequential(*shared_layers)

        # Task-specific heads
        self.task_heads = nn.ModuleList()
        for _ in range(num_tasks):
            task_layers = []
            task_in_dim = shared_dims[-1]
            for dim in task_dims:
                task_layers.extend([
                    nn.Linear(task_in_dim, dim),
                    nn.ReLU(),
                ])
                task_in_dim = dim
            task_layers.append(nn.Linear(task_in_dim, 1))
            self.task_heads.append(nn.Sequential(*task_layers))

    def forward(self, x: torch.Tensor) -> list[torch.Tensor]:
        shared_output = self.shared(x)
        return [head(shared_output) for head in self.task_heads]
```

### Use Cases
- Multiple engagement metrics (stream, save, skip)
- Joint prediction tasks
- Knowledge sharing between related tasks

## Gradient Boosting

### XGBoost for Ranking
```python
import xgboost as xgb

def train_ranking_model(train_data, valid_data, params=None):
    params = params or {
        "objective": "rank:ndcg",
        "eval_metric": "ndcg@10",
        "learning_rate": 0.1,
        "max_depth": 6,
        "min_child_weight": 1,
        "subsample": 0.8,
        "colsample_bytree": 0.8,
    }

    dtrain = xgb.DMatrix(train_data["features"], label=train_data["labels"])
    dtrain.set_group(train_data["groups"])

    dvalid = xgb.DMatrix(valid_data["features"], label=valid_data["labels"])
    dvalid.set_group(valid_data["groups"])

    model = xgb.train(
        params,
        dtrain,
        num_boost_round=1000,
        evals=[(dvalid, "valid")],
        early_stopping_rounds=50,
    )

    return model
```

### Use Cases
- Tabular data ranking
- Feature importance analysis
- Quick baseline models

## Embedding Models

### Categorical Embeddings
```python
class EmbeddingModel(nn.Module):
    def __init__(
        self,
        categorical_dims: dict[str, tuple[int, int]],  # {name: (num_categories, embedding_dim)}
        numerical_dim: int,
        hidden_dims: list[int],
        output_dim: int,
    ):
        super().__init__()

        # Embeddings for categorical features
        self.embeddings = nn.ModuleDict({
            name: nn.Embedding(num_cat, emb_dim)
            for name, (num_cat, emb_dim) in categorical_dims.items()
        })

        # Calculate total input dimension
        total_emb_dim = sum(dim for _, dim in categorical_dims.values())
        input_dim = total_emb_dim + numerical_dim

        # MLP layers
        layers = []
        for hidden_dim in hidden_dims:
            layers.extend([
                nn.Linear(input_dim, hidden_dim),
                nn.ReLU(),
                nn.Dropout(0.1),
            ])
            input_dim = hidden_dim
        layers.append(nn.Linear(input_dim, output_dim))
        self.mlp = nn.Sequential(*layers)

    def forward(
        self,
        categorical_features: dict[str, torch.Tensor],
        numerical_features: torch.Tensor,
    ) -> torch.Tensor:
        # Embed categorical features
        embedded = [
            self.embeddings[name](categorical_features[name])
            for name in self.embeddings
        ]
        embedded = torch.cat(embedded, dim=-1)

        # Concatenate with numerical
        x = torch.cat([embedded, numerical_features], dim=-1)

        return self.mlp(x)
```

## Best Practices

1. **Start simple**: Begin with simpler architectures and add complexity as needed
2. **Batch normalization**: Use for stable training
3. **Dropout**: Add for regularization
4. **Residual connections**: Consider for deeper networks
5. **Layer normalization**: Often better than batch norm for transformers
6. **Weight initialization**: Use appropriate initialization (Xavier, Kaiming)
