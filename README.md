# LLM Runner

A fully-featured CLI tool for autonomous task execution using local LLMs via Ollama. Supports interactive chat, plan generation, build automation, and multi-agent delegation.

## Features

- **Interactive Chat**: Multi-turn conversations with Ollama-hosted models
- **Single Prompt Mode**: Quick queries with `/ask`
- **Plan Generation**: Structured task planning with `/plan`
- **Build Mode**: Safe file/command execution with `/build`
- **Agent Delegation**: Autonomous multi-agent task execution with `/delegate`
  - Task decomposition via LLM
  - Sequential and parallel execution
  - Sub-agent coordination with cycle detection
  - Safety limits (depth, concurrency, timeouts)

## Installation

```bash
pip install -e .
```

Requires:
- Python 3.14+
- Ollama running locally on localhost:11434
- PyYAML, requests

## Quick Start

```bash
# Interactive chat (default)
llm-runner

# Single prompt
llm-runner /ask "What is Python?"

# Generate a plan
llm-runner plan "Build a REST API"

# Execute build tasks
llm-runner build "Add unit tests"

# Delegate to agents (multi-agent execution)
llm-runner delegate "Create and test a user authentication system"
```

## CLI Commands

### Interactive Mode
```
llm-runner
```
Multi-turn chat with history. Commands:
- `/clear` - Clear conversation history
- `/quit` - Exit

### Single Prompt
```
llm-runner /ask "Your question here"
```

### Plan Mode
```
llm-runner plan "Task description"
llm-runner plan "Task" --context              # Include AGENTS.md context
llm-runner plan "Task" --model mistral:7b     # Use specific model
```
Generates a structured plan.md file without execution.

### Build Mode
```
llm-runner build "Task description"
llm-runner build "Task" --context             # Include AGENTS.md
llm-runner build "Task" --model neural-chat   # Use specific model
```
Safely executes file operations and commands with error recovery.

### Delegate Mode (Agent Orchestration)
```
llm-runner delegate "Complex task"
llm-runner delegate "Task" --context
llm-runner delegate "Task" --model mistral:7b
```
Decomposes task into sub-tasks and orchestrates multi-agent execution.

## Architecture

```
llm-runner/
├── cli.py                 # Entry point and command routing
├── chat.py               # Interactive REPL
├── llm.py                # Ollama integration
├── config.py             # Configuration management
├── agent.py              # Agent base class
├── agent_manager.py      # Lifecycle and cycle detection
├── agent_orchestrator.py # Multi-agent execution
├── agent_limiter.py      # Safety enforcement
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

Current status: **142 tests** across 23 test files (100% passing)

## Development

This project uses test-driven development (TDD):
1. Write a test first
2. Implement minimal code to make it pass
3. Run all tests to verify
4. Refactor if needed

Commit only after a feature is completely implemented and tested (not for every small change).

## Future Phases

- **Phase 4**: Online LLM support (OpenAI, Anthropic, etc.) - *planned*
- **Phase 5**: Interactive configuration wizard
- **Phase 6**: Multi-user project hierarchies
- **Phase 7**: Advanced session context preservation
- **Phase 8**: Specialized agent roles and team coordination
