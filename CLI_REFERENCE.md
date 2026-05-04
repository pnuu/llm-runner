# CLI Reference

Complete command-line reference for LLM Runner.

## Global Flags

These flags work with all commands:

### `--model MODEL`
Override the default model from config.

```bash
llm-runner --model mistral:7b
llm-runner ask "question" --model llama3:8b
llm-runner plan "task" --model neural-chat:7b
```

**Effect**: Uses specified model instead of config default.

**Available Models**: Depends on local Ollama installation.
```bash
ollama list  # See what's installed
```

### `--config PATH`
Load configuration from a custom location (instead of `~/.llm_runner/config.yaml`).

```bash
llm-runner --config ~/.llm_runner/work.yaml
llm-runner plan "task" --config /etc/llm_runner/config.yaml
```

**Default**: `~/.llm_runner/config.yaml`

### `--context`
Include `AGENTS.md` context in plan, build, or delegate operations. Only works in plan/build/delegate modes.

```bash
llm-runner plan "task" --context
llm-runner build "task" --context
llm-runner delegate "complex task" --context
```

**Effect**: Reads AGENTS.md from current directory and provides as context to the operation.

## Modes

### Interactive (Default)
Start multi-turn chat with full command support.

```bash
llm-runner
llm-runner --model mistral:7b
llm-runner --config ~/.config/llm.yaml
```

**Commands Inside Chat**:
- `/model` - Select different model
- `/plan` - Switch to plan mode
- `/build` - Switch to build mode
- `/ask` - Context-aware query (not stored)
- `/context` - Show context usage
- `/clear` - Clear history
- `/quit` - Exit

See [INTERACTIVE_CHAT.md](INTERACTIVE_CHAT.md) for detailed guide.

### Ask (Single Prompt)
Send a one-off query without interactive mode.

```bash
llm-runner ask "What is Python?"
llm-runner ask "Explain quantum computing" --model llama3:8b
```

**Aliases**: `ask` or `/ask` (backwards compatible)
```bash
llm-runner /ask "question"  # Still works
llm-runner ask "question"   # Preferred
```

**Behavior**:
- Sends prompt to model
- Returns single response
- Exits immediately
- No history stored

### Plan (Task Planning)
Generate a structured plan for a task.

```bash
llm-runner plan "Build a REST API"
llm-runner plan "Refactor authentication" --model mistral:7b
llm-runner plan "Create CLI tool" --context
```

**Output**: Creates `plan.md` in current directory with:
- Task description
- Step-by-step breakdown
- Resource estimates
- Potential challenges
- Success criteria

**Flags**:
- `--model MODEL` - Use specific model
- `--context` - Include AGENTS.md

**Example Output File**:
```markdown
# Plan: Build a REST API

## Overview
Build a production-ready REST API with authentication...

## Steps
1. Design database schema
2. Create API endpoints
3. Add authentication
4. Write tests
...
```

### Build (Task Execution)
Execute build operations safely.

```bash
llm-runner build "Add unit tests"
llm-runner build "Create database schema" --model llama3:8b
llm-runner build "Implement feature" --context
```

**Behavior**:
- Analyzes task with LLM
- Extracts file operations and commands
- Executes safely with validation
- Reports results and errors

**Supported Operations**:
- File creation and modification
- Directory operations
- Command execution (with safety checks)
- Code generation and testing

**Flags**:
- `--model MODEL` - Use specific model
- `--context` - Include AGENTS.md

**Safety Features**:
- Validates file paths
- Prevents dangerous commands
- Error recovery
- Status reporting

### Delegate (Multi-Agent Execution)
Decompose complex tasks into sub-tasks and execute with multiple agents.

```bash
llm-runner delegate "Create and test a user authentication system"
llm-runner delegate "Build a blog platform" --model mistral:7b
llm-runner delegate "Implement payment system" --context
```

**Behavior**:
- Analyzes task complexity
- Decomposes into sub-tasks
- Spawns specialized agents
- Coordinates execution
- Returns final results and reports

**Agent Types**:
- **PlanAgent**: Task decomposition
- **CodeAgent**: Code writing
- **TestAgent**: Test creation
- **BuildAgent**: Build operations
- **ResearchAgent**: Information gathering

**Flags**:
- `--model MODEL` - Use specific model
- `--context` - Include AGENTS.md

**Advanced Behaviors**:
- Cycle detection (prevents infinite loops)
- Depth limiting (controls recursion)
- Concurrency management
- Timeout enforcement

## Exit Codes

| Code | Meaning | Example |
|------|---------|---------|
| 0 | Success | Command completed normally |
| 1 | Configuration Error | Invalid config file or settings |
| 2 | Ollama Connection Error | Cannot connect to Ollama |
| 3 | Model Not Found | Specified model not available |
| 4 | Invalid Arguments | Wrong command syntax |
| 5 | Execution Error | Build/delegate operation failed |

## Configuration Precedence

Settings are resolved in this order (first match wins):

1. **Command-line flags** (highest priority)
   ```bash
   llm-runner --model llama3:8b
   ```

2. **Environment variables** (if supported)
   ```bash
   export LLM_MODEL=mistral:7b
   llm-runner
   ```

3. **Config file** (`~/.llm_runner/config.yaml`)
   ```yaml
   model: neural-chat:7b
   ```

4. **Defaults** (lowest priority)
   ```
   model: mistral:7b
   ```

## Configuration File

Default location: `~/.llm_runner/config.yaml`

```yaml
# Model to use (must be available in Ollama)
model: mistral:7b

# Ollama server URL
ollama_host: http://localhost:11434

# Temperature (0.0=deterministic, 1.0=creative)
temperature: 0.7

# Include AGENTS.md by default (plan/build/delegate)
context: false

# Session preservation settings
session:
  enabled: true
  auto_restore: true
  max_sessions: 10
```

Override any setting with `--config` flag:
```bash
llm-runner --config ~/.llm_runner/work.yaml
```

## Usage Examples

### Quick Answer
```bash
$ llm-runner ask "What's the capital of France?"
Paris is the capital and most populated city of France...
```

### Plan a Project
```bash
$ llm-runner plan "Create a CLI tool"
Generating plan for: Create a CLI tool
✓ Plan written to: plan.md
```

### Build with Context
```bash
$ llm-runner build "Add error handling" --context
(uses AGENTS.md to understand project)
✓ Created file: src/error_handler.py
✓ Executed 3 commands successfully
```

### Compare Models
```bash
$ llm-runner --model mistral:7b
You: Explain recursion
Assistant: [mistral's response]
You: /model
Select: 2 (llama3:8b)
You: Explain recursion
Assistant: [llama3's response - different perspective]
```

### Delegate Complex Task
```bash
$ llm-runner delegate "Create user authentication system"
Decomposing task...
  ├─ PlanAgent: Create plan
  ├─ CodeAgent: Write auth module
  ├─ TestAgent: Create tests
  └─ BuildAgent: Integrate
✓ Task completed successfully
```

## Troubleshooting

### "Cannot connect to Ollama"
```bash
# Check Ollama is running
ollama serve

# Verify host in config
cat ~/.llm_runner/config.yaml

# Test connection
curl http://localhost:11434/api/tags
```

### "Model not found"
```bash
# List available models
ollama list

# Pull a model
ollama pull mistral:7b

# Try pulling and using
llm-runner --model mistral:7b
```

### "Command not found"
```bash
# Check installation
pip install -e .

# Verify executable
which llm-runner

# Try full path if needed
python -m llm_runner.cli
```

### "Invalid config"
```bash
# Validate YAML syntax
cat ~/.llm_runner/config.yaml

# Reset to defaults
rm ~/.llm_runner/config.yaml
llm-runner  # Recreates with defaults
```

## Advanced Usage

### Custom Config for Different Workflows
```bash
# Professional work (fast model)
llm-runner --config ~/.llm_runner/work.yaml

# Experimentation (best model)
llm-runner --config ~/.llm_runner/research.yaml

# Testing (smallest model)
llm-runner --config ~/.llm_runner/test.yaml
```

### Batch Operations
```bash
# Generate multiple plans
for task in task1 task2 task3; do
  llm-runner plan "$task"
done

# Ask multiple questions
for question in $(cat questions.txt); do
  llm-runner ask "$question"
done
```

### Piping Output
```bash
# Chain with other tools
llm-runner ask "List 10 Python tips" | head -5

# Save output
llm-runner ask "Generate HTML template" > template.html

# Process output
llm-runner plan "My project" | grep "Step"
```

## Environment Variables

Supported environment variables (if config supports):

```bash
export LLM_MODEL=mistral:7b
export LLM_OLLAMA_HOST=http://localhost:11434
export LLM_CONFIG=~/.llm_runner/custom.yaml
llm-runner ask "question"
```

## Shell Integration

Add to `.bashrc` or `.zshrc` for convenient access:

```bash
# Quick question shortcut
function ask() {
  llm-runner ask "$@"
}

# Plan shortcut
function plan() {
  llm-runner plan "$@"
}

# Build shortcut
function build() {
  llm-runner build "$@"
}

# Usage:
# ask "What is Python?"
# plan "Build a REST API"
# build "Add tests"
```

## See Also

- [README.md](README.md) - Overview
- [INTERACTIVE_CHAT.md](INTERACTIVE_CHAT.md) - Interactive mode guide
- [API_REFERENCE.md](API_REFERENCE.md) - Python API
- [ARCHITECTURE.md](ARCHITECTURE.md) - Design internals
