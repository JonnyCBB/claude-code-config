---
name: write-feedback
description: Transform feedback notes into a polished, coherent feedback document for a colleague. Use when writing performance feedback or peer reviews.
argument-hint: [colleague-name]
---

# Write Colleague Feedback

Transform rough feedback notes into a well-written, coherent feedback document.

## Input

The user will provide:

1. **Colleague's name** (as the argument: $ARGUMENTS)
2. **Feedback notes** (in a follow-up message or inline) containing:
   - The colleague's self-identified areas of growth (if any)
   - Strengths with examples/bullet points
   - Areas for improvement with examples/bullet points

## Output Format

Generate a feedback document with this structure:

```
[Name]'s Feedback
~~~~~~~~~~~~~~~~~

Summary
~~~~~~~

[1-2 paragraphs capturing the high-level strengths and areas for improvement.
Express genuine appreciation. Be warm but not overly formal.]


[If the colleague identified areas of growth, include this section:]
[Name]'s Self-Identified Areas of Growth
----------------------------------------

[For each area, write 1-2 paragraphs:
- Reference the specific evidence/examples from the notes
- Make inferences about impact (on them, you, the team) but don't invent facts
- State whether they've addressed it or made progress]


Strengths
~~~~~~~~~

1. [Strength Title]

[Write 1-3 paragraphs per strength:
- Include ALL examples from the input
- Add "filler" that makes inferences about impact (e.g., "This skill is underrated
  because it shows professional empathy...")
- NEVER invent specific events or facts not in the input
- Conversational, friendly tone - like a colleague would write]

2. [Next Strength Title]
...


Areas for Improvement
~~~~~~~~~~~~~~~~~~~~~

[If struggling to find improvements, acknowledge that honestly]

1. [Improvement Title]

[Write 1-2 paragraphs per area:
- Frame constructively and actionably
- Include ALL examples from the input
- Suggest what addressing this could enable
- If it's subjective or optional, say so explicitly
- Maintain warm, supportive tone]

2. [Next Improvement Title]
...
```

## Writing Guidelines

### Tone

- Natural and conversational, like a friendly work colleague
- Not overly formal - avoid corporate speak
- Genuine and warm, but not sycophantic
- Direct but supportive, especially for improvements

### Content Rules

1. **Include ALL examples** from the input - never omit provided evidence
2. **Never hallucinate facts** - don't invent meetings, conversations, or events
3. **Inferences are OK** - you CAN make logical inferences about impact:
   - "Leading a project like this only serves to increase confidence"
   - "This skill is underrated and shows professional empathy"
   - "By thinking more about X, it will make Y clearer"
4. **Constructive improvements** - frame areas for growth positively:
   - What could they gain by improving?
   - What would it enable for them/team?
5. **Acknowledge subjectivity** when relevant:
   - "This is more of a personal thing that isn't strictly necessary"
   - "Of course this is subjective..."

### Structure

- Use section dividers (~~~, ---, etc.) to separate major sections
- Number strengths and improvements
- Paragraphs should flow naturally, not read like bullet points
- Connect related points within paragraphs

## Process

1. **Wait for notes**: If the user hasn't provided feedback notes yet, ask for them
2. **Parse the input**: Identify:
   - Self-identified growth areas (if present)
   - Each strength and its supporting examples
   - Each area for improvement and its supporting examples
3. **Generate the document**: Transform notes into flowing prose following the format above
4. **Present for review**: Show the complete feedback document

## Example Transformation

Input bullet:

```
- Strong project management and leadership
    - Held meetings with both myself and Sam to orchestrate workload effectively
    - got a working backend system ready for testing within 4 weeks
    - Regular comms with frontend teams to align on the project
```

Output:

```
2. Strong project management and leadership

[Colleague] has demonstrated a really strong project management and leadership
ability during the lifecycle of the project. They held meetings with both myself
and Sam (a BE eng who was embedding in the team) to ensure that we understood
the work that needed to be done and make sure that we parallelised effectively.
This meant that a working backend system was ready for testing within 4 weeks
of creating the repository i.e. starting the work which is insanely fast.

[Colleague] was also constantly in touch with the frontend teams to make sure
that everyone was aligned on expectations and timelines with regard to the
project...
```

Note how the output:

- Keeps all examples from input
- Adds context/inference ("which is insanely fast")
- Flows as natural prose, not bullet points
- Maintains warm, genuine tone
