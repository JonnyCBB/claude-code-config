# Prerequisite Reasoning

## Table of Contents
- DAG Generation Prompt Template
- Audience Assessment Heuristics
- Topological Sort (Kahn's Algorithm)
- Scaffolded Content Generation
- Example: ADAM Optimizer for a PM

## DAG Generation Prompt Template

Use this prompt to generate the prerequisite DAG:

```
You are an expert curriculum designer. Given the concept "[TARGET_CONCEPT]",
produce a JSON prerequisite graph where each node is a concept and edges
represent "must understand before" relationships.

Rules:
- Recurse until you reach concepts that require only general knowledge
- Each concept should be a single, clearly-defined idea
- Aim for 4-8 prerequisite concepts (not too granular)
- Include only concepts that are genuinely necessary, not tangentially related

Output format (JSON):
{
  "target": "TARGET_CONCEPT",
  "prerequisites": {
    "concept_name": ["prereq_1", "prereq_2"],
    "prereq_1": ["deeper_prereq"],
    "prereq_2": [],
    "deeper_prereq": []
  }
}

Empty array [] means the concept requires only general knowledge.
```

## Audience Assessment Heuristics

Map stated role/background to assumed knowledge:

| Audience Signal | Assumed Known | Start From |
|---|---|---|
| "product manager" / "PM" | Business metrics, user flows, A/B testing | Technical concepts from scratch |
| "software engineer" | Programming, data structures, APIs | Domain-specific concepts |
| "data scientist" | Statistics, Python, basic ML | Advanced ML/specialized topics |
| "designer" | UX patterns, visual hierarchy, color theory | Technical implementation |
| "non-technical" / "beginner" | Everyday analogies only | Absolute fundamentals |
| "knows basic programming" | Variables, loops, functions, arrays | Algorithm/system concepts |
| No audience specified | General adult knowledge | Ask user to clarify |

## Topological Sort (Kahn's Algorithm)

```python
def topological_sort(graph):
    """
    graph: dict mapping concept -> list of prerequisites
    Returns: list of concepts in teaching order (foundations first)
    """
    # Count incoming edges (how many things depend on this)
    in_degree = {node: 0 for node in graph}
    for node, prereqs in graph.items():
        for prereq in prereqs:
            if prereq in in_degree:
                in_degree[node] += 1

    # Start with nodes that have no prerequisites
    queue = [n for n in in_degree if in_degree[n] == 0]
    result = []

    while queue:
        # Pick the node with no unmet prerequisites
        node = queue.pop(0)
        result.append(node)
        # "Teach" this concept — reduce in_degree for dependents
        for dependent, prereqs in graph.items():
            if node in prereqs:
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)

    return result
```

This naturally produces a teaching order: concepts with no prerequisites come first, building up to the target concept.

## Scaffolded Content Generation

For each concept in the linearized sequence, generate:

```json
{
  "concept": "Gradient",
  "plain_name": "Gradient (Direction of Steepest Change)",
  "analogy": "Imagine you're blindfolded on a hilly field. The gradient tells you which direction feels most steeply downhill under your feet.",
  "explanation": "A gradient is a vector that points in the direction of greatest increase of a function. In ML, we care about the gradient of the loss function — it tells us which way to adjust our model's parameters to reduce error the fastest.",
  "bridge": "Now that we know which direction reduces error, we need a strategy for actually walking that direction...",
  "animation_spec": {
    "type": "build-up",
    "description": "3D surface with a point. Show arrows pointing in different directions. Highlight the steepest direction. The gradient arrow grows larger as the slope gets steeper."
  }
}
```

Key principles:
- **Analogy first, definition second** — present the intuitive analogy before the technical explanation
- **One concept per step** — never introduce two new ideas simultaneously
- **Bridge sentence** — always connect to the next concept in the chain
- **Animation spec** — describe what the visualization should show, matching the concept type

## Example: ADAM Optimizer for a Product Manager

```
Level 0 (assumed known): making predictions, measuring success, iterative improvement

Level 1: ML Model
  Analogy: "A formula that learns from data — like a spreadsheet that improves itself"
  Animation: process-flow (data in → model → predictions out)

Level 2: Loss Function
  Analogy: "A score measuring how wrong predictions are — lower is better, like golf"
  Animation: comparison (predicted vs actual, with error highlighted)

Level 3: Gradient
  Analogy: "The direction that reduces error most — feeling which way is downhill blindfolded"
  Animation: build-up (surface with directional arrows)

Level 4: Gradient Descent
  Analogy: "Walking downhill step by step to find the lowest valley"
  Animation: mathematical (ball rolling down curve — Manim candidate)

Level 5: Learning Rate
  Analogy: "How big each step is — giant steps are fast but overshoot, tiny steps are slow but safe"
  Animation: comparison (large vs small steps on same curve)

Level 6: Momentum + Adaptive LR
  Analogy: "A ball that builds speed through bumps" + "Some knobs need tiny turns, others big ones"
  Animation: build-up (adding momentum arrows to gradient descent)

Level 7: ADAM
  Analogy: "Combines momentum AND adaptive rates — the automatic transmission of optimizers"
  Animation: build-up (all components assembled into one diagram)
```
