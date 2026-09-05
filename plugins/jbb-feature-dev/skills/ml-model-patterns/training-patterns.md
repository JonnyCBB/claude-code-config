# Training Patterns

Best practices for training ML models.

## Data Loading

### Efficient DataLoader
```python
from torch.utils.data import DataLoader, Dataset
import ray.data

class StreamingDataset(Dataset):
    """Dataset that streams from Ray Data."""

    def __init__(self, ray_dataset: ray.data.Dataset):
        self.dataset = ray_dataset

    def __len__(self):
        return self.dataset.count()

    def __getitem__(self, idx):
        row = self.dataset.take(1)[0]
        return {
            "features": torch.tensor(row["features"]),
            "label": torch.tensor(row["label"]),
        }


def create_dataloader(dataset_path: str, batch_size: int = 256) -> DataLoader:
    ds = ray.data.read_parquet(dataset_path)
    dataset = StreamingDataset(ds)

    return DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=4,
        pin_memory=True,
    )
```

### Ray Data Integration
```python
import ray.data

def prepare_data(path: str, batch_size: int) -> tuple:
    ds = ray.data.read_parquet(path)

    # Preprocessing
    ds = ds.map(preprocess_fn)

    # Split
    train_ds, val_ds = ds.train_test_split(test_size=0.1)

    # Convert to torch iterators
    train_iter = train_ds.iter_torch_batches(batch_size=batch_size)
    val_iter = val_ds.iter_torch_batches(batch_size=batch_size)

    return train_iter, val_iter
```

## Training Loop

### Standard Training Loop
```python
def train_epoch(
    model: nn.Module,
    dataloader: DataLoader,
    optimizer: torch.optim.Optimizer,
    criterion: nn.Module,
    device: torch.device,
) -> float:
    model.train()
    total_loss = 0.0

    for batch in dataloader:
        features = batch["features"].to(device)
        labels = batch["label"].to(device)

        optimizer.zero_grad()

        outputs = model(features)
        loss = criterion(outputs, labels)

        loss.backward()
        optimizer.step()

        total_loss += loss.item()

    return total_loss / len(dataloader)
```

### With Gradient Accumulation
```python
def train_with_accumulation(
    model: nn.Module,
    dataloader: DataLoader,
    optimizer: torch.optim.Optimizer,
    criterion: nn.Module,
    accumulation_steps: int = 4,
) -> float:
    model.train()
    total_loss = 0.0
    optimizer.zero_grad()

    for i, batch in enumerate(dataloader):
        outputs = model(batch["features"])
        loss = criterion(outputs, batch["label"])
        loss = loss / accumulation_steps
        loss.backward()

        if (i + 1) % accumulation_steps == 0:
            optimizer.step()
            optimizer.zero_grad()

        total_loss += loss.item() * accumulation_steps

    return total_loss / len(dataloader)
```

### Mixed Precision Training
```python
from torch.cuda.amp import autocast, GradScaler

def train_with_amp(
    model: nn.Module,
    dataloader: DataLoader,
    optimizer: torch.optim.Optimizer,
    criterion: nn.Module,
) -> float:
    model.train()
    scaler = GradScaler()
    total_loss = 0.0

    for batch in dataloader:
        optimizer.zero_grad()

        with autocast():
            outputs = model(batch["features"])
            loss = criterion(outputs, batch["label"])

        scaler.scale(loss).backward()
        scaler.step(optimizer)
        scaler.update()

        total_loss += loss.item()

    return total_loss / len(dataloader)
```

## Learning Rate Scheduling

### Warmup + Cosine Decay
```python
from torch.optim.lr_scheduler import CosineAnnealingLR, LinearLR, SequentialLR

def create_scheduler(
    optimizer: torch.optim.Optimizer,
    warmup_steps: int,
    total_steps: int,
) -> torch.optim.lr_scheduler.LRScheduler:
    warmup = LinearLR(
        optimizer,
        start_factor=0.1,
        end_factor=1.0,
        total_iters=warmup_steps,
    )

    cosine = CosineAnnealingLR(
        optimizer,
        T_max=total_steps - warmup_steps,
    )

    return SequentialLR(
        optimizer,
        schedulers=[warmup, cosine],
        milestones=[warmup_steps],
    )
```

### OneCycleLR
```python
scheduler = torch.optim.lr_scheduler.OneCycleLR(
    optimizer,
    max_lr=0.01,
    total_steps=num_epochs * len(dataloader),
    pct_start=0.1,
    anneal_strategy="cos",
)
```

## Early Stopping

```python
class EarlyStopping:
    def __init__(self, patience: int = 5, min_delta: float = 0.0):
        self.patience = patience
        self.min_delta = min_delta
        self.counter = 0
        self.best_score = None
        self.should_stop = False

    def __call__(self, score: float) -> bool:
        if self.best_score is None:
            self.best_score = score
        elif score < self.best_score + self.min_delta:
            self.counter += 1
            if self.counter >= self.patience:
                self.should_stop = True
        else:
            self.best_score = score
            self.counter = 0

        return self.should_stop
```

## Regularization

### Dropout and Weight Decay
```python
model = nn.Sequential(
    nn.Linear(input_dim, 256),
    nn.ReLU(),
    nn.Dropout(0.3),  # Dropout
    nn.Linear(256, 128),
    nn.ReLU(),
    nn.Dropout(0.2),
    nn.Linear(128, output_dim),
)

optimizer = torch.optim.AdamW(
    model.parameters(),
    lr=0.001,
    weight_decay=0.01,  # L2 regularization
)
```

### Label Smoothing
```python
criterion = nn.CrossEntropyLoss(label_smoothing=0.1)
```

## Distributed Training

### With Ray Train
```python
from ray.train.torch import TorchTrainer
from ray.train import ScalingConfig

def train_loop_per_worker(config):
    model = create_model()
    model = ray.train.torch.prepare_model(model)

    dataloader = create_dataloader(config["batch_size"])
    dataloader = ray.train.torch.prepare_data_loader(dataloader)

    optimizer = torch.optim.Adam(model.parameters(), lr=config["lr"])

    for epoch in range(config["epochs"]):
        loss = train_epoch(model, dataloader, optimizer)
        ray.train.report({"loss": loss})


trainer = TorchTrainer(
    train_loop_per_worker=train_loop_per_worker,
    train_loop_config={"epochs": 10, "lr": 0.001, "batch_size": 256},
    scaling_config=ScalingConfig(num_workers=4, use_gpu=True),
)

result = trainer.fit()
```

## Checkpointing

### Save and Resume
```python
def save_checkpoint(
    model: nn.Module,
    optimizer: torch.optim.Optimizer,
    epoch: int,
    loss: float,
    path: str,
) -> None:
    torch.save({
        "epoch": epoch,
        "model_state_dict": model.state_dict(),
        "optimizer_state_dict": optimizer.state_dict(),
        "loss": loss,
    }, path)


def load_checkpoint(
    model: nn.Module,
    optimizer: torch.optim.Optimizer,
    path: str,
) -> int:
    checkpoint = torch.load(path)
    model.load_state_dict(checkpoint["model_state_dict"])
    optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
    return checkpoint["epoch"]
```

## Best Practices

1. **Start with good defaults**: Adam/AdamW, LR 1e-3 to 1e-4
2. **Use validation set**: Monitor for overfitting
3. **Gradient clipping**: Prevent exploding gradients
4. **Learning rate finder**: Find optimal LR range
5. **Mixed precision**: Faster training, less memory
6. **Reproducibility**: Set seeds for torch, numpy, random
