# Persistent Memory (infinite-memory)

The `infinite-memory` MCP tools (`recall`, `remember`, `forget`, `forget_matching`,
`update_memory`, `get_memory`, `list_memories`, `memory_stats`, `get_related`)
are available as a supplementary store. The harness-native auto-memory
(`~/.claude/projects/<hash>/memory/`) is the canonical persistence layer.

Use `infinite-memory` only when semantic search across a large corpus of stored
facts would add value that the auto-memory index cannot provide. Do not
duplicate content already in auto-memory. Do not narrate individual
recall/remember calls — treat them as invisible infrastructure.
