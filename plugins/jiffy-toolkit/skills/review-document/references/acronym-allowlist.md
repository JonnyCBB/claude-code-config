# Acronym Allowlist

## Purpose

Acronyms on this list are considered universally known for the target audience and do not need expansion on first use. The prose-quality-reviewer agent loads this list when enforcing acronym definition rules and only flags acronyms **not** present here.

## Universal Allowlist

API, URL, HTTP, HTTPS, HTML, CSS, JSON, XML, YAML, SQL, CLI, SDK, REST, gRPC, TCP, UDP, IP, DNS, SSH, SSL, TLS, UI, UX, OS, CPU, GPU, RAM, SSD, PDF, CSV, PNG, JPG, SVG, GIF, UUID, GUID, IDE, CI, CD, FAQ, SLA, SLO, SLI, KPI, OKR, RFC, PR, MR, MVP, POC, ETA, FYI, TBD, TL;DR, ASAP, EOD

## Extension Examples

Domain-specific extensions can be added by the consuming agent based on the detected audience of the document under review. Starting material for common domains:

- **ML/AI**: ML, AI, NLP, LLM, RAG, GPT, CNN, RNN, LSTM, GAN
- **Data Engineering**: ETL, DAG, ELT, CDC, OLAP, OLTP
- **Security**: OWASP, CVE, PII, SSO, MFA, RBAC, IAM
- **Cloud/Infrastructure**: AWS, GCP, K8s, VM, VPC, CDN, LB

Audience-aware selection logic and non-allowlisted handling behavior belong in the prose-quality-reviewer agent definition, not in this reference file. This file is a static list; the agent defines the behavior.
