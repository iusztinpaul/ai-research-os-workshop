## Title Ideas:

Agentic Harness: The new way of building software using LLMs as the OS
Agentic Harness Engineering

## Outline

1. Introduction - Why Do We Need a Harness?
   1. Personal story: To be researched
   2. Problem + Agitation: ...
   3. Transformation + Solution: ...
   4. Intuitively, Mitchell Hashimoto has the best definition of a harness: "the idea that anytime you find an agent makes a mistake, you take the time to engineer a solution such that the agent never makes that mistake again."
   5. 200 words
2. Introduction - What the Hell Is A Harness?
   1. Let's remember what an Agent: a model + a prompt + tools + planning (e.g., ReAct). A harness is an extension of that, adding the agent memory, guardrails and advanced orchestration and context engineering. Or even creating a multi-agent system. Or even serving the agent as a server hooking it to different types of UIs, such as TUIs, classic frontends or WhatsApp/Telegram. Ultimately, it's a fancy word for building REAL software applications using LLMs as the OS that can actually be shipped through production. Still, how we interact with the computer has completely changed relative to standard web/desktop apps.
   2. Examples: Claude Code, OpenCode, OpenClaw, Codex, Junie CLI, etc.
   3. Analogy to "Harnessing a horse" (inspiration from Jonathan Gimick from Manning)
   4. Now we are "Harness a model" with tools, memory, state, guardrails, and more to properly "put them to work to gain the most out of the model while minimizing errors."
   5. 200 words
3. How does a Harness Look?
   1. Key components: LLM, tools, planning loop, context engineering, sandbox, memory, orchestration layer, serving layer, interfaces
   2. The agent loop: Powered by planning techniques like ReAct
   3. Context management: Building the prompt, while paying special consideration to the context window
   4. The multi-surface architecture allows serving many different interfaces: Serving the harness through TUIs, web apps, plugins for VS Code or JetBrains, or even accessing it from WhatsApp/Telegram
      1. Challenges: Multiple messages coming in parallel from all the clients. Also, the user can ask questions while the model is still processing the old one.
      2. Solved: Message busses and priority queues
   5. Running in parallel tasks in isolated local/cloud sandboxes and monitor their progress
   6. The filesystem is KING
   7. How is it different from an agent?
   8. Isn't this just orchestration?
   9. Prompt Engineering vs. Context Engineering vs. Harness Engineering
   10. 300 words
4. Planning & Orchestration
   1. The core agent loop is powered by ReAct. Explain how the agent loop works in 1-2 sentences...
   2. Most multi-agent orchestration logic is based on Recursive Language Models (RLM). Even if not implemented 100% as stated in the initial paper, it acted as the core source of inspiration. Explain RLM in 1-2 sentences...
   3. For example, Claude Code implements "Ralph Loops" which is a natural progression of the same idea. Explain Ralph Loops in 1-2 sentences...
   4. 200 words
5. Key Tools
   - BashTool\*\* – Runs shell commands (e.g., tests, linters) inside the project environment.
   - **EditTool** – Applies edits to existing files (insert, replace, delete ranges).
   - **WebFetchTool** – Fetches and returns the content of web URLs.
   - **GlobTool** – Finds files matching patterns like `**/*.js` in a directory.
   - **GrepTool** – Searches files (filtered by pattern) for text/regex matches.
   - **ListTool** – Lists files in a directory.
   - **ReadTool** – Reads file contents (with safety checks, size limits, etc.).
   - **WriteTool** – Writes new file contents.
   - **TodoWriteTool** – Creates/updates a session‑scoped TODO list.
   - **TodoReadTool** – Returns the current TODO list for the session.
   - **TaskTool** – Launches a sub‑agent (another agent with its own tools/prompt) to handle a task.
   1. 200 words
6. Sandbox Environment
   1. What is a sandbox environment and why it's so critical
   2. Local vs. remote
   3. Tools for local: Open
   4. Tools for remote: Vanilla Python for simpler examples and for production OpenShell, Modal, E2B
   5. 150 words
7. Memory
   1. Filesystem as long-term memory + state
   2. RAM as short-term memory
   3. Context window is what gets pushed inside the motel through context engineering
   4. The dynamics between the 3:
      1. Filesystem -> RAM -> context window -> LLM
      2. LLM -> RAM -> Filesystem
      3. Repeat
   5. 200 words
8. Let's Look at OpenCode's Architecture
   1. High-level diagram of the architecture
   2. Explain in 3-4 sentences the diagram while referencing and showing in practice how the components from above work
   3. One sentence on an end-to-end example of how a harness works using all the components from above
   4. 225 words
9. Let's Look at OpenClaw's Architecture
   1. High-level diagram of the architecture
   2. Explain in 3-4 sentences the diagram while referencing and showing in practice how the components from above work
   3. 225 words
10. Conclusion - The Future of Harness
    1. The new way of building software. Instead of software engineers building frontend/backend applications, we will start building harnesses.
    2. Popular tools such as Claude Code are just the beginning, but in reality, as Hamza Tahir, CEO of ZenML, stated, in the long run, no company or product will want to depend on proprietary harnesses such as Claude Code, or even if there are open-source solutions such as OpenCode they will want to build their own custom type of harness. At ZTRON, we did something similar, without even realizing, building a custom React engine specialized in working with tools, guardrails around finance, plus specialized context engineering to get the most out of it, coupled to a very custom UI/UX and RAG logic.
    3. 150 words

# Resources

1. [My AI Adoption Journey](https://mitchellh.com/writing/my-ai-adoption-journey)
2. [Effective harnesses for long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)
3. [Building your own AI Agent with LangChain and Nvidia](https://youtube.com/watch?v=BEYEWw1Mkmw&is=DdXgvzCyMZtxb5zl)

Create the research directory within the same directory as this file.
