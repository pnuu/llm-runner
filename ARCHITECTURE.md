# LLM Runner Architecture

## Overview

LLM Runner is organized into four key layers:

1. **CLI Layer** - Command parsing and routing
2. **Mode Handlers** - Mode-specific logic (interactive, plan, build, delegate)
3. **Core Abstraction** - LLM provider interface and agent system
4. **Implementation** - Ollama integration, agents, tools

## CLI Layer

### Entry Point: `cli.py`

Parses command-line arguments and routes to appropriate handlers:

```python
def parse_args(argv):
    # /ask "question"          -> ask mode
    # plan "task"              -> plan mode  
    # build "task"             -> build mode
    # delegate "task"          -> agent delegation
    # (default)                -> interactive chat
```

**Key responsibilities:**
- Argument parsing for all commands
- Configuration loading
- Model availability detection
- Error handling for Ollama connectivity

## Mode Handlers

### Interactive Mode: `chat.py`

Multi-turn conversation REPL:
- Maintains conversation history
- Supports `/clear` and `/quit` commands
- Graceful handling of errors and Ollama timeouts

### Plan Mode: `plan_handler.py`

Generates structured plans without execution:
- Calls LLM with planning prompt
- Writes results to plan.md
- Includes optional AGENTS.md context

### Build Mode: `build_handler.py`

Safe file/command execution:
- Provides tool system (create_file, run_command, etc.)
- Isolated workspace per task
- Error recovery strategies (abort/skip/retry)
- Tool outcomes tracked and validated

### Delegate Mode: `delegate_handler.py`

Multi-agent orchestration:
- Creates PlanAgent for task decomposition
- Orchestrates agent execution (sequential/parallel)
- Aggregates results into execution tree
- Enforces safety limits via AgentLimiter

## Core Abstraction

### LLM Provider Interface: `llm_provider.py`

Abstract base class enabling multiple LLM providers:

```python
class LLMProvider(ABC):
    @abstractmethod
    def send_prompt(self, prompt: str, model: str) -> str:
        """Send prompt and get response"""
    
    @abstractmethod
    def get_available_models(self) -> List[str]:
        """List available models"""
    
    @abstractmethod
    def estimate_cost(self, prompt: str, response: str) -> float:
        """Estimate API cost"""
```

**Current implementations:**
- OllamaProvider - Local Ollama server (free)
- Planned: OpenAIProvider, AnthropicProvider

### Agent System

#### Agent Base Class: `agent.py`

Core abstraction for all agent types:

```python
class Agent(ABC):
    def __init__(self, agent_id, agent_type, task, llm_client, workspace_dir):
        self.agent_id = agent_id
        self.agent_type = agent_type  # "PlanAgent", "CodeAgent", etc.
        self.task = task
        self.llm_client = llm_client
        self.workspace_dir = workspace_dir
    
    @abstractmethod
    def execute(self) -> str:
        """Execute the task and return result"""
    
    def spawn_agent(self, agent_type, task):
        """Create sub-agent (coordination via AgentManager)"""
    
    def wait_for_agent(self, agent_id):
        """Retrieve sub-agent result from result_store"""
```

#### Agent Manager: `agent_manager.py`

Manages agent lifecycle and safety:

```python
class AgentManager:
    def __init__(self):
        self.agents = {}           # id -> agent instance
        self.parent_child_graph = {} # child_id -> parent_id
        self.result_store = {}     # agent_id -> result
    
    def create_agent(self, agent_type, task, parent_id=None):
        """Create agent, checking for cycles"""
    
    def _would_create_cycle(self, parent_id, child_id):
        """Check if parent is descendant of child"""
```

**Safety checks:**
- Cycle detection: prevents `A -> B -> A` delegation
- Parent ancestry check: walks up parent chain to detect duplicates

#### Agent Orchestrator: `agent_orchestrator.py`

Coordinates multi-agent execution:

```python
class AgentOrchestrator:
    def execute_sequential(self, agents, error_strategy='abort'):
        """Run agents one-by-one, handling errors"""
    
    def execute_parallel(self, agents):
        """Run agents concurrently (simplified - no threads)"""
```

**Execution strategies:**
- `sequential`: Run tasks in order, abort on first error
- `parallel`: Run all tasks, return aggregated results
- Error recovery: abort/skip/retry per task

#### Agent Limiter: `agent_limiter.py`

Enforces resource and safety constraints:

```python
class AgentLimiter:
    def can_spawn_agent(self, current_depth, parent_chain):
        """Check depth, concurrency, and cycle limits"""
    
    def is_circular(self, parent_id, child_id):
        """Detect circular delegation chains"""
```

**Limits enforced:**
- `max_depth`: Prevent infinite recursion (default: 5)
- `max_agents`: Lifetime agent limit (default: 100)
- `max_concurrent`: Simultaneous agents (default: 10)
- Circular delegation: Always prevented

#### Specialized Agents: `agents/`

**PlanAgent** - Task decomposition:
```python
def decompose_task(self, task):
    """Call LLM to break task into sub-tasks
    Returns list of (agent_type, description) tuples
    """
```
Uses regex parsing: `- AgentType: description`

**CodeAgent** - Code writing and review:
- Writes code files
- Reviews existing code
- Suggests improvements

**ResearchAgent** - Information gathering:
- Researches topics
- Gathers information
- Analyzes data

**BuildAgent** - Build operations:
- Compiles code
- Installs dependencies
- Manages build artifacts

**TestAgent** - Testing:
- Creates test cases
- Runs tests
- Validates coverage

## Implementation Details

### LLM Integration: `llm.py`

Wraps Ollama API:

```python
class OllamaClient:
    def send_prompt(self, prompt, model, timeout=120):
        """POST to /api/generate, stream response"""
    
    def list_models(self):
        """GET /api/tags, return available models"""
```

**Behavior:**
- Streams responses for real-time output
- Detects Ollama unavailability
- Timeout handling for long requests
- Model availability detection on startup

### Configuration: `config.py`

YAML-based settings with defaults:

```yaml
model: mistral:7b                          # Default model
ollama_host: http://localhost:11434        # Ollama server
context: false                             # Include AGENTS.md
workspace_dir: ~/.llm_runner/workspace     # Isolated workspace
```

Stored in `~/.llm_runner/config.yaml`

### Tools: `tools/`

**executor.py** - Command execution:
- Runs shell commands
- Captures stdout/stderr
- Handles timeouts and failures

**plan_writer.py** - Plan generation:
- Formats structured plans
- Writes to markdown files
- Preserves formatting

## Data Flow Examples

### Interactive Mode
```
User Input
   ↓
cli.py (detect no command)
   ↓
chat.py (REPL loop)
   ↓
llm.py (send to Ollama)
   ↓
Display Response
```

### Plan Mode
```
User: "llm-runner plan 'Build REST API' --context"
   ↓
cli.py (parse arguments)
   ↓
plan_handler.py
   ├─ Load AGENTS.md (if --context)
   ├─ Create planning prompt
   ↓
llm.py (call Ollama)
   ↓
plan_writer.py (write to plan.md)
   ↓
Display "Plan saved to plan.md"
```

### Build Mode
```
User: "llm-runner build 'Add tests'"
   ↓
cli.py
   ↓
build_handler.py
   ├─ Create isolated workspace
   ├─ Provide tools: create_file, run_command, read_file
   ↓
llm.py (LLM executes tools)
   ↓
executor.py (validate + execute)
   ↓
Result aggregation
   ↓
Display results and created files
```

### Delegate Mode (Agent Orchestration)
```
User: "llm-runner delegate 'Create and test auth'"
   ↓
cli.py
   ↓
delegate_handler.py
   ├─ Create PlanAgent
   ↓
PlanAgent.decompose_task()
   ├─ Call LLM: "Break this into sub-tasks"
   ├─ Parse response: extract agent types
   ├─ Return: [(CodeAgent, task1), (TestAgent, task2)]
   ↓
agent_manager.py (create agents for each sub-task)
   ↓
agent_orchestrator.py
   ├─ Sequential execution with error handling
   ├─ Each agent executes independently
   ├─ Results aggregated
   ↓
AgentLimiter checks:
   ├─ Cycle detection
   ├─ Depth limits
   ├─ Concurrency limits
   ↓
Display execution tree and results
```

## Extension Points

### Adding New Agent Types

1. Create `agents/my_agent.py`:
```python
from llm_runner.agent import Agent

class MyAgent(Agent):
    def execute(self):
        prompt = f"Your task: {self.task}"
        return self.llm_client.send_prompt(prompt)
```

2. Register in `agent_manager.py`:
```python
AGENT_TYPES = {
    "MyAgent": MyAgent,
    # ... others
}
```

3. Add tests in `tests/test_my_agent.py`

### Adding New LLM Providers

1. Create `providers/openai_provider.py`:
```python
from llm_runner.llm_provider import LLMProvider

class OpenAIProvider(LLMProvider):
    def send_prompt(self, prompt, model):
        # Call OpenAI API
        pass
    
    def estimate_cost(self, prompt, response):
        # Calculate API costs
        pass
```

2. Register in CLI
3. Add tests with mocked API responses

## Testing Strategy

### Unit Tests
- Test individual components in isolation
- Mock external dependencies (Ollama, APIs)
- 100+ test cases covering happy paths and errors

### Integration Tests
- Test component interactions
- Real Ollama calls (with timeout handling)
- End-to-end workflows

### Test Organization
```
tests/
├── test_cli.py                 # CLI parsing
├── test_chat.py                # Interactive mode
├── test_llm.py                 # Ollama integration
├── test_config.py              # Configuration
├── test_agent.py               # Agent base class
├── test_agent_manager.py       # Agent lifecycle
├── test_agent_orchestration.py # Multi-agent execution
├── test_agent_limits.py        # Safety enforcement
├── test_plan_handler.py        # Plan mode
├── test_build_handler.py       # Build mode
├── test_delegate_handler.py    # Delegation mode
├── test_*_agent.py             # Specialized agents
└── test_llm_provider.py        # Provider interface
```

## Performance Considerations

- **Agent Spawning**: Lightweight - agents are objects, not processes
- **Result Aggregation**: Linear scan of result_store (acceptable for ~10 agents max)
- **Cycle Detection**: O(n) ancestry walk (acceptable for shallow trees)
- **Parallel Execution**: Simplified (no threads) - suitable for I/O bound LLM calls

## Security

- **Workspace Isolation**: Each agent/build has isolated directory
- **Command Execution**: Runs user LLM-generated commands (intentional for build mode)
- **Configuration**: Stored in user home directory (~/.llm_runner/)
- **No Secrets**: API keys deferred to Phase 4

## Future Enhancements

See README.md for planned phases (Phase 4-8).
