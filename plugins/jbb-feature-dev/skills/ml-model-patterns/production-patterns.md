# Production Patterns

Considerations for deploying ML models to production.

## Model Optimization

### Quantization
```python
import torch

def quantize_model(model: torch.nn.Module) -> torch.nn.Module:
    """Quantize model for faster inference."""
    model.eval()

    # Dynamic quantization (easiest)
    quantized = torch.quantization.quantize_dynamic(
        model,
        {torch.nn.Linear},
        dtype=torch.qint8,
    )

    return quantized
```

### ONNX Export
```python
import torch.onnx

def export_to_onnx(
    model: torch.nn.Module,
    sample_input: torch.Tensor,
    output_path: str,
) -> None:
    """Export model to ONNX format."""
    model.eval()

    torch.onnx.export(
        model,
        sample_input,
        output_path,
        export_params=True,
        opset_version=14,
        do_constant_folding=True,
        input_names=["input"],
        output_names=["output"],
        dynamic_axes={
            "input": {0: "batch_size"},
            "output": {0: "batch_size"},
        },
    )
```

### TorchScript
```python
def script_model(
    model: torch.nn.Module,
    sample_input: torch.Tensor,
) -> torch.jit.ScriptModule:
    """Convert to TorchScript for deployment."""
    model.eval()

    # Trace-based (for models without control flow)
    traced = torch.jit.trace(model, sample_input)

    # Or script-based (for models with control flow)
    # scripted = torch.jit.script(model)

    return traced
```

## Latency Optimization

### Batching Strategies
```python
class BatchingInference:
    """Batch requests for efficient inference."""

    def __init__(
        self,
        model: torch.nn.Module,
        max_batch_size: int = 32,
        max_wait_ms: int = 10,
    ):
        self.model = model
        self.max_batch_size = max_batch_size
        self.max_wait_ms = max_wait_ms
        self.queue = []

    async def predict(self, input_data: torch.Tensor) -> torch.Tensor:
        self.queue.append(input_data)

        if len(self.queue) >= self.max_batch_size:
            return await self._process_batch()

        await asyncio.sleep(self.max_wait_ms / 1000)
        return await self._process_batch()

    async def _process_batch(self) -> torch.Tensor:
        if not self.queue:
            return None

        batch = torch.stack(self.queue)
        self.queue = []

        with torch.no_grad():
            return self.model(batch)
```

### Caching
```python
from functools import lru_cache
import hashlib

class CachedModel:
    """Cache model predictions."""

    def __init__(self, model: torch.nn.Module, cache_size: int = 10000):
        self.model = model
        self.cache_size = cache_size

    @lru_cache(maxsize=10000)
    def _cached_predict(self, input_hash: str) -> tuple:
        # In practice, you'd need to store the actual input somewhere
        pass

    def predict(self, input_data: torch.Tensor) -> torch.Tensor:
        # Hash input for cache key
        input_hash = hashlib.md5(input_data.numpy().tobytes()).hexdigest()

        if input_hash in self._cache:
            return self._cache[input_hash]

        with torch.no_grad():
            result = self.model(input_data)

        self._cache[input_hash] = result
        return result
```

## Error Handling

### Graceful Degradation
```python
class RobustPredictor:
    """Handle errors gracefully in production."""

    def __init__(
        self,
        model: torch.nn.Module,
        fallback_value: float = 0.5,
        timeout_seconds: float = 0.1,
    ):
        self.model = model
        self.fallback_value = fallback_value
        self.timeout_seconds = timeout_seconds

    def predict(self, input_data: torch.Tensor) -> torch.Tensor:
        try:
            with torch.no_grad():
                result = self.model(input_data)

            # Validate output
            if torch.isnan(result).any():
                logger.warning("NaN in model output, using fallback")
                return torch.full_like(result, self.fallback_value)

            return result

        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            return torch.full(
                (input_data.shape[0], 1),
                self.fallback_value
            )
```

### Input Validation
```python
def validate_input(
    input_data: torch.Tensor,
    expected_shape: tuple[int, ...],
    expected_dtype: torch.dtype = torch.float32,
) -> bool:
    """Validate input before inference."""
    if input_data.shape[1:] != expected_shape[1:]:
        raise ValueError(f"Expected shape {expected_shape}, got {input_data.shape}")

    if input_data.dtype != expected_dtype:
        raise ValueError(f"Expected dtype {expected_dtype}, got {input_data.dtype}")

    if torch.isnan(input_data).any():
        raise ValueError("Input contains NaN values")

    if torch.isinf(input_data).any():
        raise ValueError("Input contains infinite values")

    return True
```

## Monitoring

### Prediction Logging
```python
import time
from dataclasses import dataclass

@dataclass
class PredictionLog:
    timestamp: float
    input_hash: str
    prediction: float
    latency_ms: float
    model_version: str

class MonitoredModel:
    """Model wrapper with monitoring."""

    def __init__(self, model: torch.nn.Module, model_version: str):
        self.model = model
        self.model_version = model_version
        self.predictions = []

    def predict(self, input_data: torch.Tensor) -> torch.Tensor:
        start = time.time()

        with torch.no_grad():
            result = self.model(input_data)

        latency_ms = (time.time() - start) * 1000

        self.predictions.append(PredictionLog(
            timestamp=start,
            input_hash=hashlib.md5(input_data.numpy().tobytes()).hexdigest(),
            prediction=result.mean().item(),
            latency_ms=latency_ms,
            model_version=self.model_version,
        ))

        return result

    def get_metrics(self) -> dict:
        if not self.predictions:
            return {}

        latencies = [p.latency_ms for p in self.predictions]
        return {
            "prediction_count": len(self.predictions),
            "latency_p50": np.percentile(latencies, 50),
            "latency_p99": np.percentile(latencies, 99),
            "latency_mean": np.mean(latencies),
        }
```

### Data Drift Detection
```python
from scipy import stats

class DriftDetector:
    """Detect data drift in production."""

    def __init__(
        self,
        reference_stats: dict[str, tuple[float, float]],
        threshold: float = 0.05,
    ):
        self.reference_stats = reference_stats
        self.threshold = threshold

    def check_drift(
        self,
        current_data: dict[str, np.ndarray],
    ) -> dict[str, bool]:
        drift_detected = {}

        for feature, values in current_data.items():
            ref_mean, ref_std = self.reference_stats[feature]

            # Two-sample KS test
            _, p_value = stats.ks_2samp(
                np.random.normal(ref_mean, ref_std, len(values)),
                values
            )

            drift_detected[feature] = p_value < self.threshold

        return drift_detected
```

## A/B Testing

### Feature Flags
```python
class ModelSelector:
    """Select model version based on experiment."""

    def __init__(
        self,
        models: dict[str, torch.nn.Module],
        experiment_config: dict,
    ):
        self.models = models
        self.experiment_config = experiment_config

    def get_model(self, user_id: str) -> torch.nn.Module:
        # Hash user to bucket
        bucket = hash(user_id) % 100

        for variant, config in self.experiment_config.items():
            if config["start"] <= bucket < config["end"]:
                return self.models[config["model"]]

        return self.models["control"]
```

## Best Practices

1. **Load testing**: Test with production-like traffic
2. **Canary deployments**: Gradual rollout
3. **Feature flags**: Easy rollback capability
4. **Monitoring**: Track latency, throughput, errors
5. **Data validation**: Validate inputs before inference
6. **Graceful degradation**: Handle failures gracefully
7. **Version everything**: Track model, data, config versions
