# Agent Verification Pattern

## Purpose

This pattern ensures that when a command declares it will spawn certain agents based on domain detection, those agents are actually spawned, and any deviations are communicated to the user.

## Pattern Components

### 1. Agent Type Verification (after domain detection)

After detecting domains and determining which agents to spawn, create an explicit contract:

```
## Agent Type Verification

Based on the domains detected above, I will spawn the following agents:

**Language-based agents** (always included for [language]):
- [agent-1]
- [agent-2]

**Domain-based agents** (added based on detection):
- [domain-1] detected → [agent-3]
- [domain-2] detected → [agent-4]

**Full agent list for Step [N]:**
1. [agent-1]
2. [agent-2]
3. [agent-3]
4. [agent-4]

Total agents to spawn: [N]

⚠️ This list is my CONTRACT. All agents listed here MUST be spawned before synthesis.
```

### 2. Pre-Spawn Verification Table (before spawning agents)

Immediately before making Task tool calls, output a verification table:

```
## Pre-Spawn Verification

Cross-checking Agent Type Verification against Task calls I'm about to make:

| # | Agent Type (from Contract) | Will Spawn? | Reason if Skipping |
|---|---------------------------|-------------|-------------------|
| 1 | [agent-1] | ✓ Yes | - |
| 2 | [agent-2] | ✓ Yes | - |
| 3 | [agent-3] | ✗ No | [REQUIRED: explanation] |

**Verification Result:**
- Agents in contract: [N]
- Agents to spawn: [M]
- Agents skipped: [N-M]

✓ All agents will be spawned? [YES/NO]
✗ If NO: User has been informed of skipped agents and reasons above.
```

**Rules:**
- If skipping ANY agent from the contract, you MUST fill in the "Reason if Skipping" column
- Empty "Reason if Skipping" cells are NOT allowed for skipped agents
- Proceed only after outputting this table

### 3. Pre-Synthesis Verification Checkpoint (before synthesizing findings)

Before synthesizing agent outputs, verify all contracted agents completed:

```
## Pre-Synthesis Agent Verification

Checking that all contracted agents have been spawned and completed:

From Agent Type Verification:
- Total agents contracted: [N]
- Agents actually spawned: [List]
- Total spawned: [M]

✓ Verification: N = M? [YES/NO]

If NO:
- STOP synthesis
- List missing agents
- Either spawn them now OR explain to user why they're being skipped
- Only proceed after resolution
```

### 4. Transparency Requirements

When skipping an agent that was in the contract:

**REQUIRED**: Before proceeding, output:
```
⚠️ **Agent Skip Notice**

I am skipping [agent-name] which was in my contract because:
- [Specific, concrete reason]
- [What context made this unnecessary]

This means the review/analysis may lack:
- [What insight this agent would have provided]
```

## Integration Instructions

To add this pattern to a command:

1. After domain detection, add Agent Type Verification section
2. Before spawning, add Pre-Spawn Verification Table
3. Before synthesis, add Pre-Synthesis Verification Checkpoint
4. For any skipped agent, add Agent Skip Notice

