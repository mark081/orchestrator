# Multi-Agent Orchestration POC

A minimal Python proof-of-concept demonstrating how to build a multi-agent workflow using the [Anthropic SDK](https://github.com/anthropics/anthropic-sdk-python). An orchestrator agent coordinates two specialized sub-agents in sequence: one that researches a topic, and one that writes a polished report from that research.

---

## What This Demonstrates

- **Orchestration pattern**: A coordinator that breaks a task into sub-tasks and hands results between agents
- **Agent specialization**: Each agent has a distinct role, system prompt, and output format
- **Sequential handoff**: Output from one agent becomes input to the next
- **Prompt caching**: System prompts are marked for caching to reduce token costs on repeated runs

---

## Architecture

```
main.py
  └── orchestrator.run_pipeline(client, topic)
        ├── research_agent.run_research(client, topic)
        │     └── Claude API call → structured bullet-point notes
        └── writer_agent.run_writer(client, topic, research_notes)
              └── Claude API call → polished prose report
```

### Files

| File | Role |
|---|---|
| `main.py` | Entry point. Loads env, accepts topic input, creates the Anthropic client, calls the orchestrator, prints the final report. |
| `orchestrator.py` | Pure coordination. No API calls. Calls research agent, passes results to writer agent, returns final output. |
| `research_agent.py` | Research specialist. Calls Claude with a detailed research analyst system prompt. Returns structured bullet-point notes. |
| `writer_agent.py` | Writing specialist. Calls Claude with a detailed technical writer system prompt. Receives topic + research notes, returns a polished prose report. |
| `requirements.txt` | Python dependencies: `anthropic`, `python-dotenv`. |

### Data flow

```
topic (str from CLI or input())
  │
  ▼
run_research(client, topic)
  │  Claude API call
  │  system: research analyst instructions [cached]
  │  user:   "Research this topic: {topic}"
  ▼
research_notes (str)
  │
  ▼
run_writer(client, topic, research_notes)
  │  Claude API call
  │  system: technical writer instructions [cached]
  │  user:   "Topic: {topic}\nNotes: {research_notes}"
  ▼
final_report (str) → printed to stdout
```

All inter-agent data is plain Python strings. There is no shared state, no global variables, and no disk I/O between agents. The orchestrator owns the data and passes it explicitly as function arguments.

---

## Setup

### 1. Clone and enter the directory

```bash
cd orchestrator
```

### 2. Create a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set your API key

Create a `.env` file in the project root:

```
ANTHROPIC_API_KEY=sk-ant-...
```

Or export it directly:

```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

---

## Usage

Pass a topic as a command-line argument:

```bash
python main.py "the history of jazz"
```

Or run without arguments to be prompted:

```bash
python main.py
# Enter topic: the history of jazz
```

### Example output

```
[Orchestrator] Starting pipeline for topic: 'the history of jazz'
[Orchestrator] Calling research agent...
[Research Agent] Tokens — input: 582, output: 1024, cache_created: 0, cache_read: 0
[Orchestrator] Calling writer agent...
[Writer Agent] Tokens — input: 1878, output: 1918, cache_created: 0, cache_read: 0
[Orchestrator] Pipeline complete.

============================================================
FINAL REPORT
============================================================
# How America Invented Jazz — and Then Forgot to Keep Listening
...
```

---

## Prompt Caching

Both agents mark their system prompts with `cache_control: {"type": "ephemeral"}`:

```python
system=[
    {
        "type": "text",
        "text": SYSTEM_PROMPT,
        "cache_control": {"type": "ephemeral"},  # cache this block
    }
]
```

This tells the Anthropic API to store everything up to that block on their servers for approximately 5 minutes. On subsequent requests that send the same prefix, the cached tokens are served at roughly 10% of the normal input token cost instead of being processed fresh.

**Why cache the system prompt?**

The system prompt is the largest static block in each agent call — detailed role instructions that never change between runs. The user message (the topic and research notes) changes on every call, so it is left uncached. This is the correct placement: cache what is reused, don't cache what changes.

**Minimum token threshold**

The Anthropic API requires at least 1,024 tokens in a cacheable block before it will store it. If your system prompts are shorter than this, caching is silently skipped — no error, just no benefit. Each agent prints its token usage after every call so you can verify whether caching is active:

```
cache_created: N   # tokens written to cache on a cache miss (first call)
cache_read: N      # tokens served from cache on a cache hit (subsequent calls)
```

When both values are 0, the system prompts are below the threshold. To activate caching, extend the system prompts with more detailed instructions, output format specifications, or examples until each exceeds 1,024 tokens.

---

## Extending This POC

This project is intentionally minimal. Some natural next steps:

- **Add a third agent** — for example, a fact-checker that reviews the writer's output before it is returned
- **Parallel agents** — modify the orchestrator to call multiple agents concurrently using `asyncio` and `client.messages.create` with the async client, then merge results
- **Tool use** — give the research agent tools like web search or a calculator so it can retrieve live data instead of relying on the model's training knowledge
- **Structured outputs** — have the research agent return a typed dataclass or JSON object instead of a plain string, so the writer agent receives reliably structured input
- **Streaming** — replace `client.messages.create` with `client.messages.stream` to print output token-by-token as it arrives, rather than waiting for the full response
- **Retry and error handling** — wrap each agent call in retry logic with exponential backoff for `anthropic.APIStatusError` to handle transient API errors gracefully

---

## Model

Both agents use `claude-sonnet-4-6`. To switch models, change the `MODEL` constant at the top of `research_agent.py` and `writer_agent.py`.

Current Anthropic model IDs:
- `claude-opus-4-7` — most capable
- `claude-sonnet-4-6` — balanced performance and cost (default in this POC)
- `claude-haiku-4-5-20251001` — fastest and least expensive
