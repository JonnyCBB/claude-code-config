# claude-code-setup

A directory with my Claude Code setup - agents, commands, skills.

Follow the README for instructions on how to use these for your own use cases and hopefully be inspired by what's possible.

**Important Note:** The agents and commands are constantly evolving. I'll try to keep this README up-to-date but hopefully the content can be useful in inspiring others to leverage some more advanced features of Claude Code.

## Table of Contents

- [claude-code-setup](#claude-code-setup)
  - [Table of Contents](#table-of-contents)
  - [1. Inspiration](#1-inspiration)
  - [2. Getting Started](#2-getting-started)
    - [2.1. Prerequisites](#21-prerequisites)
      - [2.1.1. Install Claude Code](#211-install-claude-code)
      - [2.1.2. Copy the directories into your `~/.claude` folder](#212-copy-the-directories-into-your-claude-folder)
      - [2.1.3. Install the `gh` CLI tool](#213-install-the-gh-cli-tool)
  - [3. Using These Tools / My Workflows](#3-using-these-tools--my-workflows)
    - [3.1. Using Skills](#31-using-skills)
    - [3.2. Using Subagents](#32-using-subagents)
      - [3.2.1. Example usage - Using a single subagent](#321-example-usage---using-a-single-subagent)
      - [3.2.2. Example usage - Running two subagents in parallel](#322-example-usage---running-two-subagents-in-parallel)
    - [3.3. Using Custom Slash Commands](#33-using-custom-slash-commands)
      - [3.3.1. Example usage - Create a PR description and push to GitHub](#331-example-usage---create-a-pr-description-and-push-to-github)
      - [3.3.2. Example usage - Complex Multi-stage workflow with chained custom commands](#332-example-usage---complex-multi-stage-workflow-with-chained-custom-commands)
        - [3.3.2.1. /research-problem](#3321-research-problem)
        - [3.3.2.2. /create-plan](#3322-create-plan)
        - [3.3.2.3. /clarify (optional)](#3323-clarify-optional)
        - [3.3.2.4. /implement-plan](#3324-implement-plan)
        - [3.3.2.5. /tidy](#3325-tidy)
        - [3.3.2.6. /pr-description](#3326-pr-description)
        - [3.3.2.7. MANUAL REVIEW](#3327-manual-review)
  - [4. Roadmap for More Skills, Agents and Commands](#4-roadmap-for-more-skills-agents-and-commands)
  - [5. Tips for Creating Agents, Commands and Skills](#5-tips-for-creating-agents-commands-and-skills)
    - [5.1. Creating Agents, Commands and Skills](#51-creating-agents-commands-and-skills)
      - [5.1.1. Example - Creating a PR description custom command](#511-example---creating-a-pr-description-custom-command)
    - [5.2. Tweaking agents, commands and/or skills](#52-tweaking-agents-commands-andor-skills)
      - [5.2.1. Example - Tweaking the "PR description" command](#521-example---tweaking-the-pr-description-command)
    - [5.3. When should I create custom commands vs agents vs skills](#53-when-should-i-create-custom-commands-vs-agents-vs-skills)
      - [5.3.1. When to create a (sub)agent](#531-when-to-create-a-subagent)
        - [Summary](#summary)
      - [5.3.2. When to create a Skill](#532-when-to-create-a-skill)
        - [Summary](#summary-1)
      - [5.3.3. When to create a custom command](#533-when-to-create-a-custom-command)
        - [Summary](#summary-2)
  - [6. Final Words](#6-final-words)
  - [7. Getting in Touch](#7-getting-in-touch)

## 1. Inspiration

Many of the agents, commands, skills and ultimately my current philosophy about creating workflows with Claude Code were **heavily** inspired by this article by Human Layer: [Getting AI to Work in Complex Codebases](https://github.com/humanlayer/advanced-context-engineering-for-coding-agents/blob/main/ace-fca.md). I've tweaked a few commands and agents to work for my use cases and I strongly encourage you to do the same. Pick the pieces from this repo that you like and tweak those that don't work so well for you in its current form.

I can't wait to see what you come up with.

## 2. Getting Started

### 2.1. Prerequisites

#### 2.1.1. Install Claude Code

Follow the [official Claude Code documentation](https://code.claude.com/docs/en/getting-started) for installing Claude Code.

#### 2.1.2. Copy the directories into your `~/.claude` folder

Copy each of the `agents` and `commands` folders, along with their contents, into your `~/.claude` directory. If you already have these directories set up then you only need to copy the contents into your corresponding local directories.

```bash
# Clone this repo
git clone https://github.com/JonnyCBB/claude-code-config.git

# Copy the directories to your ~/.claude folder
cp -r claude-code-config/agents ~/.claude/
cp -r claude-code-config/commands ~/.claude/
```

If you already have existing agents or commands, you may want to back them up first:

```bash
# Optional: backup existing directories
mv ~/.claude/agents ~/.claude/agents.backup
mv ~/.claude/commands ~/.claude/commands.backup
```

**Note:** As of writing I'm not certain that [Claude Code Plugin marketplaces](https://code.claude.com/docs/en/plugin-marketplaces) are available/secure enough to use. However, once I find out that they are available then I can add these as a plugin and you shouldn't have to worry about doing the manual "copy-paste" process.

#### 2.1.3. Install the `gh` CLI tool

Install the GitHub CLI tool `gh`:

```sh
brew install gh
gh auth login
```

## 3. Using These Tools / My Workflows

Claude Code is incredibly customisable and therefore you can use these tools in more ways than I can list here and likely even more than I have conceptualised. These suggestions merely serve as both a blueprint for how I currently use Claude Code as well as an introduction for what's possible.

### 3.1. Using Skills

[Skills](https://code.claude.com/docs/en/skills) are automatically invoked by the model. Based on the prompt and the description given for each Skill the model will decide on when it should use a Skill (this doesn't always work perfectly but it's improved over time).

This repository doesn't currently contain any skills, but the documentation below covers when and how to create them.

### 3.2. Using Subagents

[Subagents](https://code.claude.com/docs/en/sub-agents) are invoked when "Claude Code encounters a task that matches a subagent's expertise". I usually explicitly tell Claude Code when to use a subagent to ensure it does.

#### 3.2.1. Example usage - Using a single subagent

The subagent I invoke directly more than any other is by far the web-search-researcher subagent. This is one that I've written to search the web to find out information about tooling, libraries, and best practices.

Let's suppose I want to find out what the best practices are for implementing OAuth 2.0 in a Python web application. I can use the [web-search-researcher agent](/agents/web-search-researcher.md) for it by prompting with:

```
Use the web-search-researcher subagent to find out what the best practices are for implementing OAuth 2.0 in a Python web application.
```

#### 3.2.2. Example usage - Running two subagents in parallel

In Claude Code you can run subagents in parallel simply by prompting it. For example, navigate to the root of any repository that exists locally and you can run both the [codebase-analyser](/agents/codebase-analyzer.md) and [codebase-locator](/agents/codebase-locator.md) subagents on it in parallel by simply prompting:

```
Can you spin up both the codebase-analyser and codebase-locator subagents to run in parallel on this repository and give a summary of the core request flow in the service and the important steps of that flow
```

### 3.3. Using Custom Slash Commands

For the most part, my interaction with Skills and Subagents is via Custom Slash Commands. This is because slash commands can orchestrate Skills and Subagents to form potentially complex and multi-step workflows, which typically align with most real world use cases. I tend to write custom commands to automate tasks/workflows that I tend to perform often. Simple ones include creating commits and generating PR descriptions. But these can also be complex multistage workflows from researching and planning through to implementation and post implementation tidying up.

#### 3.3.1. Example usage - Create a PR description and push to GitHub

If I've already got several code changes in a branch that are pretty self-explanatory then we can use the [PR description command](/commands/pr-description.md) to generate a PR description and push to GitHub. The great thing about Claude Code (and any intelligent agent) is that it can figure out that if you haven't committed the changes then it should commit them. Additionally, if the remote branch hasn't been created then it will create it for you. So you only need to do this to generate the PR description:

```
/pr-description
```

Additionally, this custom command utilises the [codebase-locator subagent](/agents/codebase-locator.md) to search the repo for PR templates so if one exists it will write the PR according to the required template.

#### 3.3.2. Example usage - Complex Multi-stage workflow with chained custom commands

One of my most common workflows when implementing features is a pretty complex one that involves a sequence of custom commands each with their own orchestration of agents/skills. The steps are:

1. `/research-problem`
2. `/create-plan`
3. `/clarify (optional)`
4. `/implement-plan`
5. `/tidy`
6. `/pr-description`
7. MANUAL REVIEW!!!

##### 3.3.2.1. /research-problem

This is **the most important step in the entire process**. This is where you give all of the relevant context to the agent (e.g. RFCs, design documents, your own notes and questions) and it runs a bunch of parallel agents to understand the problem and outline a high-level solution (or several). The output is a markdown document of its findings. You should read this document carefully and ensure you address any issues or open questions at this stage.
**REMEMBER:** a single bad line of code is just a single bad line of code. A single bad plan is potentially hundreds/thousands of lines of bad code (shamelessly paraphrased from [Getting AI to Work in Complex Codebases](https://github.com/humanlayer/advanced-context-engineering-for-coding-agents/blob/main/ace-fca.md)).
It's not uncommon for me to run two or three rounds of `/research-problem` just to make sure that I'm happy with the high-level plan.

Example usage:

```
/research-problem <TEXT_DESCRIBING_THE_PROBLEM_ALONG_WITH_LINKS_TO_RELEVANT_DOCS>
```

**Important:** I can't stress enough how important this step is. This is essentially Planning mode but with the addition of agents that can help you with the research required for the problem (You could say Planning Mode Plus). It's critical that you [give the required context](https://runnercode.com/blog/context-is-the-bottleneck-for-coding-agents-now) for the agents to be able to answer the question adequately and DO NOT be afraid to ask follow up questions. You can (and should) run this step in a "loop" until you are happy with the plan BEFORE proceeding.

##### 3.3.2.2. /create-plan

Once you're happy with the high-level plan it's time to create a more detailed plan. Typically I just pass the research document to this command and no other information.

```
/create-plan <LINK_TO_RESEARCH_DOC_PRODUCED_PREVIOUSLY>
```

This command produces another doc which is much more technical and contains lots of code. It's worth reviewing this because it basically outlines what will be implemented before the agent actually implements it. It's your chance to get on the same page as the agent proactively.

##### 3.3.2.3. /clarify (optional)

You may or may not run this command depending on how confident you are that the plan is solid and what you expect. If you want more reassurance that the plan is solid then running the following command in Claude is a good step.

```
/clarify <LINK_TO_IMPLEMENTATION_PLAN_FROM_PREVIOUS_STEP>
```

This does not produce a document but instead presents clarifying questions to the user about the plan.

##### 3.3.2.4. /implement-plan

Does what it says on the tin. Importantly, it makes sure that the agent keeps a todo list of tasks for implementing the plan and checks it off as it goes along so if it gets stuck or hangs at any point it knows where it left off. The command also forces the agent to stop and notify the user if it feels that it needs to diverge from the agreed plan.

You can use it by running:

```
/implement-plan <LINK_TO_IMPLEMENTATION_PLAN_FROM_THE_CREATE_PLAN_STEP>
```

##### 3.3.2.5. /tidy

Implementing the plan should hopefully produce something that solves the original problem but this doesn't guarantee that the code is of good enough quality for PR review (please do think about your peers). This is why I created the `/tidy` command. This is a (potentially frustratingly) interactive flow where the agent calls on code simplification and test reviewer agents to review the code changes and provide recommendations for which the user is then asked which of the recommendations they would like implemented. This should hopefully improve code quality. You can invoke this by prompting with:

```
/tidy current code changes against <TARGET_BRANCH>
```

where `<TARGET_BRANCH>` is typically `main` or `master`.

##### 3.3.2.6. /pr-description

This is basically the [same discussed above](#331-example-usage---create-a-pr-description-and-push-to-github) regarding creating a PR description.

##### 3.3.2.7. MANUAL REVIEW

There is no substitute for reviewing this code yourself BEFORE sending the PR for review by your team members. Make sure you empathise with your team and don't forget this important step.

## 4. Roadmap for More Skills, Agents and Commands

This repository is far from finished, nor are any of the existing Skills, Agents and Commands in a finished state. I found that I've tweaked the entire setup A LOT over the last couple of months and I expect to do the same in the foreseeable future. Some changes/additions I know I want to make are:

- Python/ML focussed agents. Despite being an ML engineer I haven't worked in an ML repo for a while so I haven't written any ML/Python focussed agents. I hope to write some of these pretty soon.
- More specialised code review agents for different languages and frameworks.
- Agents for working with specific cloud providers (AWS, GCP, Azure).

## 5. Tips for Creating Agents, Commands and Skills

If you find these agents useful then you may be inspired to create your own agents, commands and/or skills. However, it can be quite confusing as to knowing when something should be an agent vs command vs skill. Also, you may be wondering "How do I even create my own agent?"

Well here are my tips as to when to do this:

### 5.1. Creating Agents, Commands and Skills

My advice for creating an agent, command or skill would be to **Let Claude do it.** Point Claude to its own documentation so that it brings that into context and then just define what you want the agent, command or skill to do.

#### 5.1.1. Example - Creating a PR description custom command

When I wanted to write a command to write PR descriptions, which you can see in `commands/pr-description`, I needed to find out what made a good PR so I researched the dimensions of a good PR description. Once I was happy with my research I went to Claude Code and wrote a prompt like:

```
Create a command that creates PR descriptions based on these guidelines <INSERT RESEARCH HERE>.

Make sure to read the documentation on how to create claude code custom commands here: https://code.claude.com/docs/en/slash-commands

I want to be able to select the branch for which the pr description should be written and it should gather context about the PR from any documents that I pass.
```

This will give Claude Code enough information to create a suitable PR Description agent for you.

### 5.2. Tweaking agents, commands and/or skills

Once you create/use the agent (or command or skill) you might find that it doesn't always work as expected or the way that you want it. Rather than accept these issues the best thing to do is to let Claude Code know and then try to fix it. I find these steps work well:
1. Tell Claude Code what the issue is
2. Tell it to "reflect" on what went wrong
3. Ask it to then suggest how it can amend the agent/command/skill to fix the problem
4. If you're happy then ask it to make the changes to fix it.

Steps 1-3 can be done in a single prompt. In "complex" cases (where I'm not completely certain myself what the fix should look like) I like to see what it thinks the problem is and how it intends to fix it before telling it to implement the fix.

#### 5.2.1. Example - Tweaking the "PR description" command

The PR description subagent I initially wrote was good; however, there was a problem when I came to a repository that contained a `pull_request_template.md` because the PR description structure that was initially written didn't respect templates. Rather than ignore the command, I simply asked Claude Code to amend the command to look for PR templates BEFORE writing the PR description. Here is the EXACT prompt I gave to Claude Code to respect PR templates:

```
I have a `/pr-description` custom command (as defined in the docs: https://docs.claude.com/en/docs/claude-code/slash-commands) which generates pull
requests. However, I want to change the flow. The first 2 instructions: i.e. 1. **Fetch and analyze changes** and 2. **Auto-detect key information**
should remain the same but then I want step 3 to use the code-locator subagent to find any pull request template files. If it doesn't find any then we should use the current PR description template defined in the file. However, if it does find a PR template file then it should write a PR according
to the template provided.

Can you update the custom command to follow this flow please
```

### 5.3. When should I create custom commands vs agents vs skills

This can be one of the hardest decisions to make and to a certain extent the decision can be very subjective and very much depends on your philosophy about how to work with agents. I'll give my thoughts here but these are not all completely objective so if it's still ambiguous after reading these tips it likely is because it's still an art and not a science:

#### 5.3.1. When to create a (sub)agent

[(Sub)Agents](https://code.claude.com/docs/en/sub-agents) work in their own isolated context window which means that when you invoke them via the main Claude Code agent, the main agent does not receive all of the subagent context. The main agent only gets the final summary. This is very important for managing context and therefore agents are a critical component of developing long-running workflows (at least they are in Claude Code). See the article on [Getting AI to Work in Complex Codebases](https://github.com/humanlayer/advanced-context-engineering-for-coding-agents/blob/main/ace-fca.md) for a more detailed explanation about this.

Therefore, I typically write agents whenever the task will produce LOTS of redundant tokens in a context. For example, if I want to find examples of how particular libraries/packages have been integrated within a codebase I will likely search through many files. The response from extensive code searching can typically consume ~10,000s tokens. Claude models typically have a context window of 128k tokens meaning a significant amount of the available context is taken up by this response and most of it may not be relevant. Claude may only need a handful of examples to understand how to use the library. For this reason many of my workflows that involve extensive searching are subagents.
Another example is web searching. It's likely that most of the information on webpages is not relevant to answering a given question. Perhaps only a few sentences in an article are relevant. Therefore, web researching is a good candidate for a subagent.

I like having a level of control over what changes an agent is allowed to make. Therefore, all of my (sub)agents are typically documentors or reviewers. **They are not explicitly allowed to make edits** (even if I've been too lazy to force this using agent permission settings). The outputs of the subagents are usually recommendations or documentation which I can then choose to act on as part of a custom command workflow. I know that there are many people that may disagree with this approach because the promise of intelligent machines is that they *SHOULD* be able to do these sorts of things for us. Call me old fashioned but my experience is that it's not uncommon for AI to get things wrong enough as for me to warrant some level of caution about what I allow it to edit.

##### Summary

Create a subagent whenever most of the tokens produced by a task are **redundant** given the end goal. This helps manage the context of the main agent and enables longer running workflows

#### 5.3.2. When to create a Skill

The utility of [Claude Code Skills](https://code.claude.com/docs/en/skills) isn't immediately obvious but it's been argued that they ["maybe a bigger deal than MCP"](https://simonwillison.net/2025/Oct/16/claude-skills/). The way I think about it is:

> **Skills** = Expand in your current context
> **Sub-agents** = Get their own separate context.

I recommend using skills when you need to maintain context from your current workflow/conversation, and subagents when you want parallel processing of individual tasks and can have context isolation.

The way I think about it is "**If I think that the majority of the tokens produced by a command/task is useful to keep in context then use a Skill, if not, then use a Subagent.**"

For example, if you have a Skill for fetching API schemas, most of the tokens from the skill are the output schema and using a skill doesn't carry the additional latency and token cost of spawning a subagent with its own isolated context and prompt, nor do I need to specify the output format for the subagent to ensure that it returns the required data.

##### Summary

Create a Skill whenever most of the tokens produced by a task are **useful** given the end goal.

#### 5.3.3. When to create a custom command

[Custom (slash) commands](https://code.claude.com/docs/en/slash-commands) can invoke agents and skills whereas subagents CANNOT invoke other subagents (this is my understanding as of writing). I'm also not sure that Skills can invoke other skills. Given this information, I find custom commands are most useful for orchestrating skills and subagents to carry out complex workflows. For example, the `/research-problem` custom command orchestrates several subagents to work in parallel to research a codebase whilst performing web research to answer questions about a problem. In fact, most of my use of subagents at the moment is via custom slash commands.

Furthermore, the tokens produced by a custom command stay within the main agent context window and hence you can also define workflows in which the user can interact and direct the agent. For example, the `/tidy` custom command asks for direction/permissions from the user on several occasions within its workflow.

##### Summary

Create a custom slash command if:
- You need to orchestrate agents and skills to carry out a workflow
- You desire high levels of interactivity/user input as part of a particular workflow.

## 6. Final Words

**IMPORTANT:** Remember these are my personal tips and not all of these tips are necessarily objective. You may have different conclusions/philosophies as to how to work with agents which are perfectly valid.

I'm loving working with Claude Code and its configurable agentic capabilities. I hope this repo can inspire you to get more joy out of your agentic coding experience and encourage you to GO WILD with all of its possibilities!!!

## 7. Getting in Touch

If you have any questions or feedback about anything in this repository or just want to chat about coding agents/Claude Code, feel free to reach out to me via email at jonnybrooks04@gmail.com.
