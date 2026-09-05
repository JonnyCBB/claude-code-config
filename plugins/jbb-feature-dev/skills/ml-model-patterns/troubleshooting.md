# Troubleshooting

Common issues and solutions for ML models.

## Training Issues

### Loss Not Decreasing

**Symptoms**: Loss stays flat or oscillates.

**Solutions**:

1. **Check learning rate**:
   ```python
   # Try different learning rates
   for lr in [1e-5, 1e-4, 1e-3, 1e-2]:
       train_with_lr(lr)
   ```

2. **Verify data loading**:
   ```python
   # Check a batch
   batch = next(iter(dataloader))
   print(f"Features: {batch['features'].shape}")
   print(f"Labels: {batch['label'].unique()}")
   ```

3. **Check for data issues**:
   ```python
   # Look for NaN/Inf
   print(f"NaN in features: {torch.isnan(features).any()}")
   print(f"Inf in features: {torch.isinf(features).any()}")
   ```

4. **Simplify model**:
   ```python
   # Start with simpler architecture
   model = nn.Linear(input_dim, output_dim)
   ```

### Overfitting

**Symptoms**: Train loss decreases but validation loss increases.

**Solutions**:

1. **Add regularization**:
   ```python
   # Dropout
   nn.Dropout(0.3)

   # Weight decay
   optimizer = torch.optim.AdamW(params, weight_decay=0.01)
   ```

2. **Increase data**:
   - Data augmentation
   - More training examples

3. **Reduce model complexity**:
   ```python
   # Fewer layers/parameters
   hidden_dim = 64  # Reduced from 256
   ```

4. **Early stopping**:
   ```python
   if val_loss > best_val_loss:
       patience_counter += 1
       if patience_counter >= patience:
           break
   ```

### Exploding/Vanishing Gradients

**Symptoms**: Loss becomes NaN or gradients are 0.

**Solutions**:

1. **Gradient clipping**:
   ```python
   torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
   ```

2. **Batch normalization**:
   ```python
   nn.BatchNorm1d(hidden_dim)
   ```

3. **Residual connections**:
   ```python
   x = x + self.layer(x)  # Skip connection
   ```

4. **Better initialization**:
   ```python
   nn.init.xavier_uniform_(layer.weight)
   ```

## Inference Issues

### High Latency

**Symptoms**: Predictions are slow.

**Solutions**:

1. **Profile model**:
   ```python
   with torch.profiler.profile() as prof:
       model(input_data)
   print(prof.key_averages().table())
   ```

2. **Use GPU**:
   ```python
   model = model.to("cuda")
   input_data = input_data.to("cuda")
   ```

3. **Batch predictions**:
   ```python
   # Instead of one at a time
   predictions = model(batch_of_inputs)
   ```

4. **Model optimization**:
   ```python
   # Quantization
   model = torch.quantization.quantize_dynamic(model)
   ```

### Memory Issues

**Symptoms**: OOM errors during inference.

**Solutions**:

1. **Reduce batch size**:
   ```python
   batch_size = 16  # Down from 64
   ```

2. **Clear cache**:
   ```python
   torch.cuda.empty_cache()
   ```

3. **Use inference mode**:
   ```python
   with torch.inference_mode():
       predictions = model(input_data)
   ```

4. **Stream large datasets**:
   ```python
   for batch in dataloader:
       process(batch)
       del batch
   ```

### Inconsistent Predictions

**Symptoms**: Same input gives different outputs.

**Solutions**:

1. **Ensure eval mode**:
   ```python
   model.eval()
   ```

2. **Disable dropout**:
   ```python
   # In eval mode, dropout is disabled
   model.eval()
   ```

3. **Set seeds**:
   ```python
   torch.manual_seed(42)
   np.random.seed(42)
   ```

## Data Issues

### Feature Drift

**Symptoms**: Model performance degrades over time.

**Solutions**:

1. **Monitor feature distributions**:
   ```python
   def check_feature_drift(reference, current):
       _, p_value = stats.ks_2samp(reference, current)
       return p_value < 0.05
   ```

2. **Retrain regularly**:
   - Schedule periodic retraining
   - Trigger on drift detection

3. **Use robust features**:
   - Prefer stable features
   - Normalize with running stats

### Label Imbalance

**Symptoms**: Model predicts majority class.

**Solutions**:

1. **Class weights**:
   ```python
   weights = compute_class_weight("balanced", classes, y_train)
   criterion = nn.CrossEntropyLoss(weight=torch.tensor(weights))
   ```

2. **Oversampling**:
   ```python
   from imblearn.over_sampling import SMOTE
   X_resampled, y_resampled = SMOTE().fit_resample(X, y)
   ```

3. **Threshold adjustment**:
   ```python
   # Adjust decision threshold
   predictions = (probabilities > 0.3).astype(int)
   ```

## Deployment Issues

### Model Loading Failures

**Error**: `ModuleNotFoundError` or `RuntimeError: Error loading model`

**Solutions**:

1. **Version compatibility**:
   ```python
   # Save with version info
   torch.save({
       "model_state_dict": model.state_dict(),
       "pytorch_version": torch.__version__,
   }, path)
   ```

2. **Load with map_location**:
   ```python
   model.load_state_dict(torch.load(path, map_location="cpu"))
   ```

3. **Custom class registration**:
   ```python
   # Ensure custom modules are importable
   from my_module import CustomLayer
   ```

### Serving Issues

**Symptoms**: Model deployed but predictions fail.

**Solutions**:

1. **Check input format**:
   ```python
   # Ensure input matches expected schema
   print(f"Expected: {model.input_schema}")
   print(f"Got: {input_data.shape}")
   ```

2. **Verify model artifacts**:
   ```bash
   # Check model was saved correctly
   ls -la model_dir/
   ```

3. **Check logs**:
   ```bash
   kubectl logs -f deployment/my-model
   ```

## Getting Help

1. **Slack Channels**:
   - #ml-help - General ML questions

2. **Documentation**:
   - [ML Best Practices](https://your-internal-docs.example/)

3. **When asking for help, include**:
   - Model architecture summary
   - Training configuration
   - Error message and stack trace
   - Data sample (sanitized)
