# Domain-Agent Registry

This registry maps technical domains to their corresponding expert agents. Commands use this to dynamically spawn domain-specific agents based on file and content analysis.

## Detection Procedure

Follow these steps IN ORDER when detecting domains. Each pass is independent — a domain detected in any pass should be spawned.

### Pass 1: File triggers (deterministic — no judgment)

Check every changed/referenced file path against the **File Triggers** column. If ANY file matches a glob pattern, the domain is detected. Do not skip this pass or apply judgment — file triggers are definitive.

### Pass 2: Strong signals (one match = detected)

Check import statements, API calls, and content of changed lines for **Strong Signals**. These are specific enough that a single match confirms the domain.

### Pass 3: Corroborating signals (2+ matches needed)

Check content for **Corroborating Signals**. These are common terms that need reinforcement — require EITHER:

- 2+ distinct corroborating signals from the same domain, OR
- 1 corroborating signal + a file in a related directory (see Directory Signals below)

### Pass 4: Report detections

Show the user which domains were detected and which pass triggered them:

```
## Domains Detected
- ml-pipelines: Pass 1 — file trigger `model.pt`
```

## Domain Mappings

| Domain ID      | File Triggers  | Strong Signals (1 match)                                                                 | Corroborating Signals (2+ needed)                                                                                                     | Expert Agent           | Status    |
| -------------- | -------------- | ---------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------- | ---------------------- | --------- |
| `ml-pipelines` | `*.pt`, `*.pth` | `torch.nn`, `DataLoader`, `from transformers import`, `from sklearn import`, `lightning` | `model`, `training`, `evaluation`, `loss`, `optimizer`, `trainer`, `epoch`, `batch_size`, `learning_rate`, `validation`, `checkpoint` | `jbb-feature-dev:ml-pipeline-reviewer` | Available |

> This registry is deliberately small. Add a row only when you have an agent that genuinely knows a
> domain better than the general reviewers — otherwise language detection (see
> `language-agent-registry.md`) already covers it.

## Directory Signals

| Directory Pattern            | Reinforces Domain | Rationale                |
| ---------------------------- | ----------------- | ------------------------ |
| `ml/`, `training/`, `model/` | `ml-pipelines`    | ML-related code location |

## Overlap Warnings

No signal currently maps to more than one domain. If you add a domain whose signals overlap an
existing one, record the tie-break here and spawn both agents when the context is ambiguous.

## Special Cases

### `ml-pipelines`

Most corroborating signals (`model`, `training`, `loss`, etc.) are extremely common outside ML contexts. Only trigger when:

- A file trigger matches (`*.pt`, `*.pth`), OR
- A strong signal matches (actual ML framework imports), OR
- 3+ corroborating signals appear together in the same file

## Agent Prompt Templates

When spawning domain experts, use these prompt patterns:

### For RFC Review:

```
Review the [DOMAIN] aspects of this RFC:
- Evaluate alignment with [DOMAIN] best practices
- Identify potential issues or anti-patterns specific to [DOMAIN]
- Suggest improvements based on [DOMAIN] expertise
- Check for missing considerations typical in [DOMAIN] proposals
```

### For PR Review:

```
Review the [DOMAIN] code changes in this PR:
- Check adherence to [DOMAIN] patterns and conventions
- Identify [DOMAIN]-specific issues or anti-patterns
- Suggest [DOMAIN] best practices where applicable
- Verify proper use of [DOMAIN] APIs and configurations
```

### For Planning/Research:

```
Provide [DOMAIN] expertise for this task:
- Identify [DOMAIN]-specific considerations
- Suggest [DOMAIN] patterns and approaches
- Highlight [DOMAIN] risks or constraints
- Reference [DOMAIN] documentation and examples
```

## User Override Support

Commands should support these override patterns:

- `--include-domains=ml-pipelines` - Force include specific domain experts
- `--exclude-domains=ml-pipelines` - Exclude specific domain experts
- `--no-domain-experts` - Skip all domain expert spawning
- `--all-domain-experts` - Spawn all available domain experts

## Maintenance

When adding new domain experts:

1. Add a row to the Domain Mappings table with file triggers, strong signals, and corroborating signals
2. Ensure strong signals are specific enough that a single match won't produce false positives
3. If the domain has canonical files, always add them as file triggers
4. Update Overlap Warnings if signals conflict with existing domains
5. Test detection with sample content that should and should NOT trigger the domain
