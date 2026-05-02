# Development Guide

This guide is for developers working on LLM Runner.

## Getting Started

### Prerequisites
- Python 3.14+
- Ollama running locally on localhost:11434
- Conda environment `py314`

### Setup
```bash
cd llm-runner
pip install -e .
pytest  # Verify all 142 tests pass
```

## Test-Driven Development (TDD)

All features in LLM Runner use strict TDD:

1. **Write a test first** - Create a test file or add test to existing file
   ```python
   def test_feature_does_something():
       # Arrange
       result = feature.do_something()
       # Assert
       assert result == expected
   ```

2. **Verify test fails** - Run the test, confirm it fails
   ```bash
   pytest tests/test_feature.py::test_feature_does_something -v
   ```

3. **Implement minimal code** - Add only what's needed to pass the test
   ```python
   def do_something():
       return expected
   ```

4. **Run all tests** - Verify nothing broke
   ```bash
   pytest
   ```

5. **Refactor** - Improve code quality while tests pass

6. **Commit** - Only commit when a feature is complete (not for every small change)
   ```bash
   git add .
   git commit -m "feat: feature name with context" -m "Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
   ```

## Project Structure

```
llm_runner/
├── __init__.py              # Package exports
├── cli.py                   # Entry point (300+ lines)
├── chat.py                  # Interactive REPL
├── llm.py                   # Ollama client
├── config.py                # Configuration management
├── agent.py                 # Agent base class
├── agent_manager.py         # Lifecycle and cycle detection
├── agent_orchestrator.py    # Multi-agent execution
├── agent_limiter.py         # Safety enforcement
├── llm_provider.py          # Abstract provider interface
├── handlers/
│   ├── __init__.py
│   ├── plan_handler.py
│   ├── build_handler.py
│   └── delegate_handler.py
├── agents/
│   ├── __init__.py
│   ├── code_agent.py
│   ├── plan_agent.py
│   ├── research_agent.py
│   ├── build_agent.py
│   └── test_agent.py
├── providers/
│   ├── __init__.py
│   └── ollama_provider.py    # (Partial - Phase 4 deferred)
└── tools/
    ├── __init__.py
    ├── executor.py
    └── plan_writer.py

tests/
├── test_cli.py                  # 15 tests
├── test_chat.py                 # 8 tests
├── test_llm.py                  # 8 tests
├── test_config.py               # 6 tests
├── test_agent.py                # 7 tests
├── test_agent_manager.py        # 9 tests
├── test_agent_orchestration.py  # 12 tests
├── test_agent_limits.py         # 8 tests
├── test_plan_handler.py         # 7 tests
├── test_build_handler.py        # 14 tests
├── test_delegate_handler.py     # 9 tests
├── test_plan_agent.py           # 4 tests
├── test_code_agent.py           # 4 tests
├── test_research_agent.py       # 4 tests
├── test_build_agent.py          # 4 tests
├── test_test_agent.py           # 4 tests
├── test_tool_executor.py        # 8 tests
├── test_tool_plan_writer.py     # 5 tests
└── test_llm_provider.py         # 7 tests

Total: 23 test files, 142 tests
```

## Key Design Decisions

### 1. No Sub-process Execution for Agents
Agents are Python objects, not separate processes. This keeps the system simple and suitable for a CLI tool. For I/O-bound LLM calls, lightweight coordination works well.

**Rationale:**
- Simpler architecture
- Easier testing and debugging
- Lower resource overhead
- Appropriate for Ollama-based local execution

### 2. Result Store Pattern
Agents store results in a shared dictionary accessible by parent agents via `wait_for_agent()`.

**Implementation:**
```python
# In AgentManager
self.result_store[agent_id] = result

# In Agent
def wait_for_agent(self, agent_id):
    return self.agent_manager.result_store[agent_id]
```

**Rationale:**
- Decouples sub-agent execution from parent
- Allows time-shifted retrieval
- Simple and testable

### 3. Regex Parsing for Task Decomposition
PlanAgent parses LLM responses using regex to extract sub-tasks:

```python
# Response format: "- AgentType: description"
# Regex: r'[-\d.]+\s*(\w+Agent):\s*(.+?)(?=\n|$)'
```

**Rationale:**
- Deterministic parsing (no JSON dependencies)
- Works with various LLM response formats
- Clear contract between LLM and system

### 4. Cycle Detection via Ancestry Chain
Prevents infinite delegation by checking if parent is already in child's ancestor chain.

```python
def _would_create_cycle(self, parent_id, child_id):
    # Walk up from parent_id to root
    # If we see child_id in ancestors, it would create a cycle
```

**Rationale:**
- O(n) complexity acceptable for shallow trees
- Direct prevention of cycles
- Clear failure messages

### 5. Phase Separation with Linear Dependencies
Each phase builds on previous phases with no backtracking:

- Phase 1: Core chat (32 tests)
- Phase 2: Plan/build modes (84 tests, +52)
- Phase 3: Agent system (142 tests, +58)
- Phase 4+: Extensions (deferred)

**Rationale:**
- Clear progress and milestone tracking
- Prevents scope creep
- Easier to test and validate each phase

## Common Tasks

### Adding a New Agent Type

1. Create `llm_runner/agents/my_agent.py`:
```python
from llm_runner.agent import Agent

class MyAgent(Agent):
    def execute(self) -> str:
        # Implement your agent logic
        prompt = f"Task: {self.task}"
        return self.llm_client.send_prompt(prompt, self.model or "mistral:7b")
```

2. Register in `llm_runner/agent_manager.py`:
```python
AGENT_TYPES = {
    "PlanAgent": PlanAgent,
    "CodeAgent": CodeAgent,
    "MyAgent": MyAgent,  # Add here
    # ...
}
```

3. Create `tests/test_my_agent.py`:
```python
import pytest
from llm_runner.agents.my_agent import MyAgent
from unittest.mock import MagicMock

def test_my_agent_executes_task():
    llm_client = MagicMock()
    llm_client.send_prompt.return_value = "Result"
    
    agent = MyAgent(
        agent_id="test-1",
        task="Do something",
        llm_client=llm_client,
        workspace_dir="/tmp"
    )
    
    result = agent.execute()
    assert result == "Result"
    llm_client.send_prompt.assert_called_once()
```

4. Run tests:
```bash
pytest tests/test_my_agent.py -v
```

### Adding a New CLI Command

1. Update argument parser in `llm_runner/cli.py`:
```python
def parse_args(argv):
    # ... existing code ...
    
    if len(argv) > 0 and argv[0] == "mycommand":
        return {
            "mode": "mycommand",
            "argument": argv[1] if len(argv) > 1 else None,
            # ... other args ...
        }
```

2. Create handler in `llm_runner/handlers/my_handler.py`:
```python
class MyHandler:
    def handle_my_mode(self, task, llm_client, config):
        # Implement your mode
        result = llm_client.send_prompt(task)
        return result
```

3. Route in `cli.py`:
```python
def run_cli():
    # ... existing code ...
    
    if args["mode"] == "mycommand":
        from llm_runner.handlers.my_handler import MyHandler
        handler = MyHandler()
        handler.handle_my_mode(args["argument"], llm_client, config)
```

4. Add tests in `tests/test_my_handler.py`

### Debugging Tests

```bash
# Run single test with output
pytest tests/test_file.py::test_function -v -s

# Run with Python debugger
pytest tests/test_file.py::test_function --pdb

# Run with coverage
pytest tests/test_file.py --cov=llm_runner --cov-report=html
```

### Running Integration Tests

Integration tests make real Ollama calls:

```bash
# Run only integration tests
pytest -m integration

# Run specific integration test
pytest tests/test_llm.py::test_ollama_sends_prompt -v
```

All integration tests include timeout handling.

## Testing Best Practices

### 1. Mock External Dependencies
```python
def test_agent_with_mocked_llm():
    llm_client = MagicMock()
    llm_client.send_prompt.return_value = "response"
    
    agent = CodeAgent(
        agent_id="1",
        task="write code",
        llm_client=llm_client,
        workspace_dir="/tmp"
    )
    
    result = agent.execute()
    assert result == "response"
```

### 2. Test Error Paths
```python
def test_agent_handles_llm_timeout():
    llm_client = MagicMock()
    llm_client.send_prompt.side_effect = TimeoutError("LLM timeout")
    
    agent = CodeAgent(...)
    
    with pytest.raises(TimeoutError):
        agent.execute()
```

### 3. Use Fixtures for Common Setup
```python
@pytest.fixture
def mock_llm_client():
    client = MagicMock()
    client.send_prompt.return_value = "response"
    return client

def test_something(mock_llm_client):
    # Use mock_llm_client
    pass
```

### 4. Test Isolation
- Each test is independent
- Use temporary directories for file operations
- Mock time-dependent functions
- Clean up resources in teardown

## Performance Guidelines

- **Agent spawn time**: < 10ms (object creation)
- **LLM response time**: Typical 2-5 seconds (Ollama dependent)
- **Result aggregation**: < 100ms for 10 agents
- **Cycle detection**: < 1ms for trees up to depth 5

If you add features that violate these guidelines, add performance tests.

## Commit Guidelines

Commits should be:
- **Atomic**: One logical feature per commit
- **Complete**: Feature fully implemented and tested
- **Well-described**: Clear message explaining what and why
- **Include trailer**: Co-authored-by trailer for Copilot

Example:
```
feat: add agent spawning with cycle detection

- Implement spawn_agent() and wait_for_agent() in Agent base class
- Add cycle detection via _would_create_cycle() in AgentManager
- Add 9 tests covering normal and error cases
- Resolves parent->child->parent infinite delegation

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
```

## Code Style

- **PEP 8 compliant** (follow existing code)
- **Type hints** in function signatures (Python 3.10+)
- **Docstrings** for public classes/functions (but not trivial ones)
- **No over-commenting** - code should be self-documenting

## Documentation

When adding features, update:
- README.md - If user-facing feature
- ARCHITECTURE.md - If architectural change
- DEVELOPMENT.md - If development process change
- Docstrings - Function/class documentation

## Troubleshooting

### Tests fail with "Ollama not running"
```bash
# Start Ollama
ollama serve

# Or skip integration tests
pytest -m "not integration"
```

### Import errors in tests
```bash
# Ensure package is installed in dev mode
pip install -e .

# Clear Python cache
find . -type d -name __pycache__ -exec rm -r {} +
```

### Agent cycles detected in tests
If tests detect cycles unexpectedly:
- Check parent-child relationships
- Use `agent_manager._would_create_cycle()` to debug
- Print parent_child_graph to visualize structure

## Next Steps for Contributors

1. Read ARCHITECTURE.md for system design
2. Review existing tests to understand testing patterns
3. Start with a small feature in plan mode or build mode
4. Follow TDD: test first, then implement
5. Ensure all 142 tests pass before committing
6. Submit PR with clear description

## Questions?

See README.md and ARCHITECTURE.md for more details. Look at existing code for patterns.
