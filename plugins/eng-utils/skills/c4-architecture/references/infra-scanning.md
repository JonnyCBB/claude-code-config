# Infrastructure Scanning Patterns

How to auto-generate Container-level C4 diagrams by scanning a repository's infrastructure files.
Use when you have access to a service repository and want a starting-point architecture
diagram without deep code reading.

## Section 1 — Scanning Strategy

Step-by-step workflow to generate a Container-level C4 diagram from source files:

1. Find a service catalog descriptor if the repo has one (`catalog-info.yaml`, `service.yaml`,
   `CODEOWNERS` plus a README) → extract system name, type, owner, declared dependencies
2. Find Kubernetes `Deployment` manifests → extract containers, environment variables (reveals
   external service URLs/addresses), port definitions
3. Find scheduled workflow definitions (Airflow DAGs, Argo/Kubernetes `CronJob` manifests, cron
   configs) → identify trigger schedules (indicates batch processes), task dependencies (reveals
   data flow between services)
4. Check `docker-compose.yml` if present → additional containers and their relationships
5. Draft Container-level diagram from extracted elements; flag human-review items

---

## Section 2 — Catalog Descriptor Extraction

What to look for and what it maps to (field names vary by catalog; these are the common ones):

```yaml
# catalog-info.yaml
kind: Component
metadata:
  name: playlist-service              # → Container name
spec:
  type: service                       # → Container type (service vs library vs website)
  owner: group:team-playlists         # → system boundary grouping
  system: playlist-platform           # → System_Boundary name
  dependsOn:
    - component:track-metadata-service  # → Rel() to external container
    - resource:playlist-db              # → ContainerDb()
```

---

## Section 3 — Kubernetes Manifest Extraction

Key fields to scan in `Deployment` manifests:

- `spec.template.spec.containers[].image` → container technology
- `spec.template.spec.containers[].env` → look for `*_URL`, `*_ENDPOINT`, `*_HOST` env vars
  (each is a likely external dependency → `Rel()`)
- `spec.template.spec.containers[].ports[].containerPort` → protocol hints:
  - 8080 = HTTP
  - 8443 = HTTPS
  - 50051 = gRPC
  - 6379 = Redis
  - 5432 = PostgreSQL
- Labels: `app.kubernetes.io/component` and `app.kubernetes.io/part-of` → boundary grouping

---

## Section 4 — Scheduled Workflow Extraction

For batch pipeline services:

- Each scheduled workflow definition → one `Container` (batch job)
- Its upstream dependencies (input datasets, sensor tasks) → `Rel()` from upstream data endpoints
- Its image or runtime field → container technology hint

---

## Section 5 — Auto-Generation Reliability by Level

| C4 Level | Auto-generation reliability | Notes |
|----------|-----------------------------|-------|
| System Context (L1) | High where a catalog descriptor exists | Declared dependencies + `system` field gives 80%+ |
| Container (L2) | Medium-High | K8s + catalog descriptor gives good starting point; needs human review for accuracy |
| Component (L3) | Low-Medium | Needs code reading; useful starting point from package structure |
| Code (L4) | Not recommended | Equivalent to reading source files; no efficiency gain |

Always mark auto-generated diagrams with `# Auto-generated from infrastructure files — review before publishing`
in the Structurizr DSL comment or as a note in the PlantUML diagram.
