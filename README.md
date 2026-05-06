# LLM Runner

A fully-featured CLI tool for autonomous task execution using local LLMs via Ollama. Supports interactive chat, plan generation, build automation, and multi-agent delegation.

## Features

- **Interactive Chat**: Multi-turn conversations with Ollama-hosted models
  - Built-in commands: `/model` (switch models), `/plan` (plan mode), `/build` (build mode), `/ask` (context-aware queries)
  - Automatic context compaction when exceeding token limits
  - Session preservation across restarts
- **Single Prompt Mode**: Quick queries with `ask` command (formerly `/ask`)
- **Plan Generation**: Structured task planning
- **Build Mode**: Safe file/command execution
- **Agent Delegation**: Autonomous multi-agent task execution
  - Task decomposition via LLM
  - Sequential and parallel execution
  - Sub-agent coordination with cycle detection
  - Safety limits (depth, concurrency, timeouts)
- **Streaming Output**: Real-time token streaming for long-running operations
  - Visible thinking model output as tokens arrive
  - Reduces perceived latency
  - Works seamlessly in all modes
- **Timeout Enforcement**: Asyncio-based timeout protection
  - Prevents tasks from running indefinitely
  - Configurable per-task or global defaults
  - Graceful cancellation and cleanup

## Installation

```bash
pip install -e .
```

Requires:
- Python 3.14+
- Ollama running locally on localhost:11434
- PyYAML, requests, httpx, pytest-asyncio

## Quick Start

```bash
# Interactive chat (default)
llm-runner

# Single prompt (ask mode)
llm-runner ask "What is Python?"        # New: without slash
llm-runner /ask "What is Python?"       # Still works for backwards compatibility

# Generate a plan
llm-runner plan "Build a REST API"

# Execute build tasks
llm-runner build "Add unit tests"

# Delegate to agents (multi-agent execution)
llm-runner delegate "Create and test a user authentication system"

# Override model for any command
llm-runner --model llama3:8b ask "Quick question"
llm-runner --model mistral:7b plan "My project"
```

See [CLI_REFERENCE.md](CLI_REFERENCE.md) for complete command documentation.

## CLI Commands

### Interactive Mode
```
llm-runner [--model MODEL] [--config CONFIG]
```

Multi-turn chat with full history and context management.

**Interactive Commands** (type inside chat):
- `/model` - Interactive model selector (switch between available models)
- `/plan` - Switch to plan mode, then return to chat
- `/build` - Switch to build mode, then return to chat
- `/ask` - Ask a question using conversation context (not stored in history)
- `/context` - Show context usage and token statistics
- `/clear` - Clear conversation history
- `/quit` - Exit chat

Example session:
```
You: How do I build a REST API?
Assistant: [response]
You: /model
  1. mistral:7b  ← current
  2. llama3:8b
  3. neural-chat
Select: 2
You: Same question to llama3
Assistant: [different response from llama3]
```

See [INTERACTIVE_CHAT.md](INTERACTIVE_CHAT.md) for detailed guide and workflows.

### Single Prompt (Ask Mode)
```
llm-runner ask "Your question here"
llm-runner ask "What is Python?" --model llama3:8b
```

Quick one-shot queries without storing in history. Use `ask` (or `/ask` for backwards compatibility).

### Plan Mode
```
llm-runner plan "Task description"
llm-runner plan "Build a REST API" --context              # Include AGENTS.md
llm-runner plan "Task" --model mistral:7b                # Use specific model
```

Generates a structured `plan.md` file without execution.

### Build Mode
```
llm-runner build "Task description"
llm-runner build "Add unit tests" --context              # Include AGENTS.md
llm-runner build "Create file" --model neural-chat       # Use specific model
```

Safely executes file operations and commands with error recovery.

### Delegate Mode (Agent Orchestration)
```
llm-runner delegate "Complex task"
llm-runner delegate "Create auth system" --context
llm-runner delegate "Task" --model mistral:7b
```

Decomposes task into sub-tasks and orchestrates multi-agent execution.

## Global Flags

- `--model MODEL` - Override configured default model (works with all modes)
- `--config PATH` - Load config from custom path (instead of `~/.llm_runner/config.yaml`)
- `--context` - Include `AGENTS.md` in context (plan/build/delegate modes only)

## Architecture

```
llm-runner/
├── cli.py                 # Entry point and command routing
├── chat.py               # Interactive REPL with streaming support
├── llm.py                # Ollama integration (async + streaming)
├── async_executor.py     # Timeout enforcement and async task runner
├── config.py             # Configuration management
├── agent.py              # Agent base class
├── agent_manager.py      # Lifecycle and cycle detection
├── agent_orchestrator.py # Multi-agent execution
├── agent_limiter.py      # Safety enforcement (with timeout)
├── handlers/             # Mode-specific logic
│   ├── plan_handler.py
│   ├── build_handler.py
│   └── delegate_handler.py
├── agents/               # Specialized agent types
│   ├── code_agent.py
│   ├── plan_agent.py
│   ├── research_agent.py
│   ├── build_agent.py
│   └── test_agent.py
├── tools/                # Tool implementations
│   ├── executor.py       # Command execution
│   └── plan_writer.py    # Plan file generation
└── llm_provider.py       # Abstract LLM provider interface
```

## Configuration

Configuration is stored in `~/.llm_runner/config.yaml`. Sensible defaults are provided.

```yaml
model: mistral:7b
ollama_host: http://localhost:11434
context: false           # Include AGENTS.md by default
```

## Agent System

The agent system enables autonomous multi-agent task execution:

- **PlanAgent**: Decomposes tasks into sub-tasks
- **CodeAgent**: Writes and reviews code
- **ResearchAgent**: Gathers and analyzes information
- **BuildAgent**: Executes build operations
- **TestAgent**: Creates and runs tests

Agents can spawn sub-agents to delegate work. The system includes:
- Cycle detection (prevents infinite delegation loops)
- Depth limits (prevents excessive recursion)
- Concurrency limits (manages resource usage)
- Timeout enforcement (prevents hung tasks)

Example flow:
```
User: "Create and test authentication"
  └─ PlanAgent: Decomposes into subtasks
      ├─ CodeAgent: Write auth module
      ├─ TestAgent: Create tests
      └─ BuildAgent: Integrate and verify
```

## Testing

Run all tests:
```bash
pytest
```

Run specific test file:
```bash
pytest tests/test_agent_orchestration.py
```

Run with coverage:
```bash
pytest --cov=llm_runner
```

Current status: **281 tests** across 25+ test files (100% passing)

## Development

This project uses test-driven development (TDD):
1. Write a test first
2. Implement minimal code to make it pass
3. Run all tests to verify
4. Refactor if needed

Commit only after a feature is completely implemented and tested (not for every small change).

## Streaming and Timeout Configuration

### Streaming Output

All LLM requests support real-time streaming output. When streaming is enabled:
- Tokens appear in the chat as they arrive from Ollama
- Thinking model outputs become visible instead of appearing only at completion
- Perceived latency is reduced significantly

Streaming is enabled by default and works automatically in all modes (chat, plan, build, ask).

### Timeout Enforcement

Long-running tasks are protected by asyncio-based timeout enforcement:
- Default task timeout: 30 seconds (configurable per agent/limiter)
- Prevents indefinite hangs from unresponsive LLMs or commands
- Tasks are gracefully cancelled with proper cleanup
- Timeout errors are reported clearly to the user

**Disabling Timeout:**

Timeout can be disabled at startup or toggled at runtime when needed for long-running operations:

```bash
# Start chat without timeout enforcement
llm-runner --disable-timeout-check
```

In interactive mode, toggle timeout with:
```
/timeout off   # Disable timeout for long-running tasks
/timeout on    # Re-enable timeout
/timeout status # Show current timeout state
```

To customize timeout programmatically:

```python
from llm_runner.agent import Agent
from llm_runner.agent_limiter import AgentLimiter

# Per-agent timeout
agent = Agent(model="mistral", task_timeout=60)

# Per-limiter timeout (affects all agents it manages)
limiter = AgentLimiter(task_timeout=120, max_concurrent=3)
```

## Future Phases

- **Phase 4**: Online LLM support (OpenAI, Anthropic, etc.) - *planned*
- **Phase 5**: Interactive configuration wizard
- **Phase 6**: Multi-user project hierarchies
- **Phase 7**: Advanced session context preservation
- **Phase 8**: Specialized agent roles and team coordination
