# Testing Patterns

Framework-agnostic ML testing patterns applicable to both PyTorch and TensorFlow.

## Overview

This document covers testing patterns that transcend specific ML frameworks:

| Pattern | Use Case | Applicable To |
|---------|----------|---------------|
| Test data factories | Reusable test fixture generation | All frameworks |
| YAML-based scenarios | Declarative test definitions | All frameworks |
| Latency measurement | Performance validation | Production systems |
| Distributed math tests | Partitioning correctness | Multi-worker training |
| Server lifecycle tests | Model serving validation | Inference servers |

## Test Data Factory Pattern

Create reusable factory functions for test data with sensible defaults:

```python
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

@dataclass
class AudiobookMetadataBase:
    title: str
    contributors_authors: str
    duration_hours: float
    territories: List[str]
    last_modified: datetime

def create_audiobook_metadata_base(**kwargs) -> AudiobookMetadataBase:
    """Factory function with sensible defaults and kwargs override."""
    return AudiobookMetadataBase(
        title=kwargs.get("title", "Default Title"),
        contributors_authors=kwargs.get("contributors_authors", "Default Author"),
        duration_hours=kwargs.get("duration_hours", 1.0),
        territories=kwargs.get("territories", ["CA", "US"]),
        last_modified=kwargs.get("last_modified", datetime.utcnow()),
    )

@dataclass
class AudiobookMetadataResponse:
    title: str
    contributors_authors: str
    duration_hours: float
    territories: List[str]
    last_modified: datetime
    confidence_score: float

def create_audiobook_metadata_response(**kwargs) -> AudiobookMetadataResponse:
    """Composition of factory functions."""
    base = create_audiobook_metadata_base(**kwargs)
    return AudiobookMetadataResponse(
        **vars(base),
        confidence_score=kwargs.get("confidence_score", 0.95)
    )
```

**Reference**: `Findaway/audiobook-matches-backend/tests/utils/factory/audiobook_metadata.py:8-40`

### Factory Pattern Benefits

- **Sensible defaults**: Tests focus on what's different, not boilerplate
- **Type safety**: IDE support and static analysis
- **Composition**: Build complex objects from simpler ones
- **Override flexibility**: Customize specific fields via kwargs

### Usage Examples

```python
def test_with_factory():
    # Use all defaults
    metadata = create_audiobook_metadata_base()

    # Override specific fields
    long_book = create_audiobook_metadata_base(duration_hours=12.5)

    # Edge cases
    empty_territories = create_audiobook_metadata_base(territories=[])
```

## YAML-Based Test Scenarios

Define test scenarios declaratively for easier maintenance:

```python
from pathlib import Path
import pytest
import yaml

@pytest.fixture
def sample_scenarios_yaml(tmp_path: Path) -> Path:
    """Create YAML test scenarios fixture."""
    yaml_content = """scenarios:
  - scenario_name: "Test scenario with dates"
    comment: "Testing date macros"
    question: "How many users on {today:%Y-%m-%d}?"
    expected_sql: |
      SELECT COUNT(*) FROM users_{today:%Y%m%d}
      WHERE date = '{yesterday:%Y-%m-%d}'

  - scenario_name: "Aggregation query"
    question: "What is the average stream count by country?"
    expected_sql: |
      SELECT country, AVG(stream_count)
      FROM streams
      GROUP BY country

variants:
  - variant_name: "Test variant"
    changes:
      - description: "Add instructions"
        docs: |
          Use partition {today:%Y%m%d} for latest data.
"""
    scenarios_file = tmp_path / "scenarios.yaml"
    scenarios_file.write_text(yaml_content)
    return scenarios_file

def test_scenarios(sample_scenarios_yaml):
    with open(sample_scenarios_yaml) as f:
        config = yaml.safe_load(f)

    for scenario in config["scenarios"]:
        result = execute_query(scenario["question"])
        assert result == scenario["expected_sql"]
```

**Reference**: `analytics-platform-tooling/insights-service/tests/eval/conftest.py:8-48`

### Scenario Schema

```yaml
scenarios:
  - scenario_name: str        # Human-readable name
    comment: str              # Optional description
    question: str             # Input to test
    expected_sql: str         # Expected output
    tags: [str]               # Optional categorization
```

### Date Macro Support

```python
from datetime import datetime, timedelta

def expand_date_macros(template: str) -> str:
    """Expand date macros in templates."""
    today = datetime.now()
    yesterday = today - timedelta(days=1)

    return template.format(
        today=today,
        yesterday=yesterday,
    )

# Usage
template = "SELECT * FROM data_{today:%Y%m%d}"
expanded = expand_date_macros(template)
# "SELECT * FROM data_20260121"
```

## End-to-End Latency Measurement

Measure processing latency for ML pipelines:

```python
import numpy as np
import pandas as pd
import yaml
from google.cloud import bigquery

QUERY = """
SELECT
    file_id,
    start_time,
    time_added,
    audio_length_secs
FROM `project.dataset.processing_metrics`
WHERE date = @date
"""

def download_data_from_bigquery(query: str, date: str) -> pd.DataFrame:
    client = bigquery.Client()
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("date", "STRING", date)
        ]
    )
    return client.query(query, job_config=job_config).to_dataframe()

def calculate_time_difference(start_time, end_time) -> float:
    """Calculate processing time in seconds."""
    return (end_time - start_time).total_seconds()

def main():
    df = download_data_from_bigquery(QUERY, "2026-01-20")

    processing_times = []
    for index, row in df.iterrows():
        time_diff_seconds = calculate_time_difference(
            row["start_time"],
            row["time_added"]
        )
        # Normalize by audio length
        percentage = (time_diff_seconds / float(row["audio_length_secs"])) * 100
        processing_times.append(percentage)

    output_data = {
        "latency_average": float(np.mean(processing_times)),
        "latency_p50": float(np.percentile(processing_times, 50)),
        "latency_p95": float(np.percentile(processing_times, 95)),
        "latency_p99": float(np.percentile(processing_times, 99)),
        "min_processing_time": float(min(processing_times)),
        "max_processing_time": float(max(processing_times)),
        "sample_count": len(processing_times),
    }

    # Write results for CI/CD analysis
    with open(f"results_{date}.yaml", "w") as f:
        yaml.dump(output_data, f)

    # Assert SLA requirements
    assert output_data["latency_p99"] < 200, "P99 latency exceeds SLA"
```

**Reference**: `BrandSafetyML/sensitive-topics-inference-pipeline/tests/integration/end_to_end_latency.py:66-123`

### Latency Test Pattern

```python
import pytest

@pytest.mark.integration
class TestLatencySLA:
    def test_inference_latency_p99(self, model_server):
        latencies = []
        for _ in range(1000):
            start = time.time()
            model_server.predict(sample_input)
            latencies.append(time.time() - start)

        p99 = np.percentile(latencies, 99)
        assert p99 < 0.100, f"P99 latency {p99:.3f}s exceeds 100ms SLA"

    def test_throughput(self, model_server):
        start = time.time()
        count = 0
        while time.time() - start < 10:  # 10 second window
            model_server.predict(sample_input)
            count += 1

        qps = count / 10
        assert qps > 100, f"Throughput {qps:.1f} QPS below 100 QPS requirement"
```

## Distributed Partitioning Math Tests

Test correctness of distributed data partitioning:

```python
import pytest

def _compute_local_row_range(global_rows: int, world_size: int, rank: int):
    """Compute start, end, and local_rows for a given rank."""
    rows_per_rank = global_rows // world_size
    remainder = global_rows % world_size

    # Distribute remainder across first N ranks
    if rank < remainder:
        local_rows = rows_per_rank + 1
        start = rank * (rows_per_rank + 1)
    else:
        local_rows = rows_per_rank
        start = remainder * (rows_per_rank + 1) + (rank - remainder) * rows_per_rank

    end = start + local_rows
    return (start, end, local_rows)

class TestComputeLocalRowRange:
    def test_uneven_split_with_remainder(self):
        """Test partitioning when rows don't divide evenly."""
        global_rows = 1025
        world_size = 4

        rank_0 = _compute_local_row_range(global_rows, world_size, 0)
        rank_1 = _compute_local_row_range(global_rows, world_size, 1)
        rank_2 = _compute_local_row_range(global_rows, world_size, 2)
        rank_3 = _compute_local_row_range(global_rows, world_size, 3)

        # First rank gets extra row (1025 = 4*256 + 1)
        assert rank_0 == (0, 257, 257), f"Rank 0 expected (0, 257, 257)"
        assert rank_1 == (257, 513, 256), f"Rank 1 expected (257, 513, 256)"
        assert rank_2 == (513, 769, 256), f"Rank 2 expected (513, 769, 256)"
        assert rank_3 == (769, 1025, 256), f"Rank 3 expected (769, 1025, 256)"

    def test_coverage_all_rows(self):
        """Verify all rows are covered with no gaps or overlaps."""
        global_rows = 1025
        world_size = 4

        ranges = [
            _compute_local_row_range(global_rows, world_size, r)
            for r in range(world_size)
        ]

        # Check no gaps between ranks
        for i in range(len(ranges) - 1):
            assert ranges[i][1] == ranges[i + 1][0], \
                f"Gap between rank {i} (end={ranges[i][1]}) and rank {i+1} (start={ranges[i+1][0]})"

        # Check first starts at 0, last ends at global_rows
        assert ranges[0][0] == 0, "First rank should start at 0"
        assert ranges[-1][1] == global_rows, "Last rank should end at global_rows"

        # Check total coverage
        total_local_rows = sum(r[2] for r in ranges)
        assert total_local_rows == global_rows, \
            f"Total local rows {total_local_rows} != global rows {global_rows}"

    @pytest.mark.parametrize("global_rows,world_size", [
        (100, 4),
        (101, 4),
        (1000, 8),
        (1, 1),
        (3, 10),  # More workers than rows
    ])
    def test_various_configurations(self, global_rows, world_size):
        """Test various row/worker configurations."""
        ranges = [
            _compute_local_row_range(global_rows, world_size, r)
            for r in range(world_size)
        ]

        total = sum(r[2] for r in ranges)
        assert total == global_rows
```

**Reference**: `foundation-models/prolific-fm/tests/config/test_model_config.py:74-150`

## Model Server Lifecycle Testing

Test model server startup, inference, and shutdown:

```python
import subprocess
import requests
import time
import signal
import os

DEFAULT_TIMEOUT = 120  # seconds

def popen_launch_server(model: str, base_url: str, timeout: int, **kwargs):
    """Launch model server subprocess."""
    cmd = [
        "python", "-m", "model_server",
        "--model", model,
        "--host", "localhost",
        "--port", base_url.split(":")[-1],
    ]

    # Add extra arguments
    for key, value in kwargs.items():
        cmd.extend([f"--{key.replace('_', '-')}", str(value)])

    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # Wait for server to be ready
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(f"{base_url}/health")
            if response.status_code == 200:
                return process
        except requests.exceptions.ConnectionError:
            time.sleep(0.5)

    raise TimeoutError(f"Server did not start within {timeout} seconds")

def kill_process_tree(pid: int):
    """Kill process and all children."""
    import psutil
    try:
        parent = psutil.Process(pid)
        children = parent.children(recursive=True)
        for child in children:
            child.terminate()
        parent.terminate()
        parent.wait(timeout=5)
    except psutil.NoSuchProcess:
        pass

class TestModelServer:
    @classmethod
    def setUpClass(cls):
        cls.model = "test-model"
        cls.base_url = "http://localhost:8080"
        cls.process = popen_launch_server(
            cls.model,
            cls.base_url,
            timeout=DEFAULT_TIMEOUT,
            sampling_backend="pytorch",
            disable_radix_cache=True,
        )

    @classmethod
    def tearDownClass(cls):
        kill_process_tree(cls.process.pid)

    def test_health_endpoint(self):
        response = requests.get(f"{self.base_url}/health")
        assert response.status_code == 200

    def test_greedy_decoding(self):
        """Test deterministic generation."""
        first_response = None
        for _ in range(5):
            response = requests.post(
                f"{self.base_url}/generate",
                json={
                    "text": "The capital of Germany is",
                    "sampling_params": {"temperature": 0}
                },
            ).json()

            if first_response is None:
                first_response = response["text"]
            else:
                # Greedy decoding should be deterministic
                assert response["text"] == first_response
```

**Reference**: `foundation-models/sglang/test/registered/sampling/test_pytorch_sampling_backend.py:21-91`

## When to Use Each Pattern

| Pattern | When to Use |
|---------|-------------|
| **Test data factory** | Need reusable, type-safe test fixtures |
| **YAML scenarios** | Many similar test cases with variations |
| **Latency measurement** | Validating production SLAs |
| **Distributed math** | Multi-worker data partitioning |
| **Server lifecycle** | Testing model serving endpoints |

## Parameterized Testing

Combine patterns with pytest parametrization:

```python
import pytest

@pytest.mark.parametrize(
    "config_file,expected_output",
    [
        ("configs/test_small.yaml", 100),
        ("configs/test_large.yaml", 10000),
        ("configs/test_edge.yaml", 1),
    ],
)
def test_config_processing(config_file, expected_output):
    result = process_config(config_file)
    assert result.row_count == expected_output
```

**Reference**: your ML SDK's own `tests/test_utils.py` helpers

## Related Patterns

- [skf-tensorflow-pipelines/testing-patterns.md](../skf-tensorflow-pipelines/testing-patterns.md) - TensorFlow/SKF patterns

## Documentation Links

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-benchmark](https://pytest-benchmark.readthedocs.io/) - Performance testing
- [YAML Specification](https://yaml.org/spec/)
