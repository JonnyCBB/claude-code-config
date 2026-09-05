# Implementation pattern discovery

When planning or implementing a new feature, **always** search for existing reusable patterns in the codebase before writing new code:

1. **Search for existing abstractions** — Look for interfaces, abstract classes, protocols, traits, or base classes that new code should extend/implement.
2. **Search patterns**: `abstract class`, `interface`, `extends`, `implements`, `Protocol`, `trait`, `ABC` (Python), `@abstractmethod`.
3. **If an existing pattern is found**, the implementation MUST use it unless there's a documented reason not to.
4. **If the approach differs from a prior research doc**, explicitly call out the deviation and explain why.

Example: If implementing a new gRPC tool and `AbstractGrpcTool` exists with 10+ usages, extend it rather than implementing the raw `Tool` interface.
