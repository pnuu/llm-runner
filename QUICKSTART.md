# LLM Runner Quick Start

Get up and running with LLM Runner in 5 minutes.

## Installation

**Prerequisites:**
- Python 3.14+
- Ollama running locally (`ollama serve`)

**Install:**
```bash
pip install -e .
```

## Basic Usage

### 1. Interactive Chat (Default)
```bash
llm-runner
```
Chat with an LLM model. Type `/quit` to exit, `/clear` to reset history.

```
> What's the capital of France?
Assistant: The capital of France is Paris...

> Tell me more
Assistant: Paris is located on the Seine River...

/quit
```

### 2. Single Prompt
```bash
llm-runner /ask "What is Python?"
```
Get a quick answer without entering chat mode.

### 3. Generate a Plan
```bash
llm-runner plan "Build a REST API"
```
Creates a `plan.md` file with structured steps.

**With context:**
```bash
llm-runner plan "Build a REST API" --context
```
Includes `AGENTS.md` instructions in the context.

### 4. Execute Build Tasks
```bash
llm-runner build "Add unit tests to my project"
```
Safely creates files and runs commands. Results saved to isolated workspace.

### 5. Delegate to Agents (Autonomous)
```bash
llm-runner delegate "Create and test a user authentication system"
```
Breaks down complex tasks into sub-tasks and runs multiple agents:
- PlanAgent decomposes the task
- CodeAgent writes code
- TestAgent creates tests
- Other agents coordinate execution

## Common Options

All modes support these flags:

```bash
--model mistral:7b        # Use specific Ollama model (default: in config)
--context                 # Include AGENTS.md in context (for plan/build/delegate)
```

## Configuration

Settings stored in `~/.llm_runner/config.yaml`:

```yaml
model: mistral:7b
ollama_host: http://localhost:11434
context: false                          # Include AGENTS.md by default
workspace_dir: ~/.llm_runner/workspace
```

Edit this file to change defaults.

## Models

Check available Ollama models:
```bash
ollama list
```

Popular models:
- `mistral:7b` - Fast, general purpose (default)
- `neural-chat` - Optimized chat model
- `dolphin-mixtral` - Strong reasoning
- `llama2` - General purpose

Pull a model:
```bash
ollama pull dolphin-mixtral
```

Then use it:
```bash
llm-runner --model dolphin-mixtral /ask "Solve this puzzle..."
```

## Examples

### Generate a Project Plan
```bash
llm-runner plan "Build a Python CLI tool for file management"
```
Output: `plan.md` with tasks, steps, and considerations.

### Build a Feature
```bash
llm-runner build "Add authentication to the API"
```
The LLM can:
- Create new files
- Modify existing files
- Run tests
- Execute commands

### Research a Topic
```bash
llm-runner delegate "Research and summarize distributed consensus algorithms"
```
Agents work together to research and compile findings.

### Complex Task
```bash
llm-runner delegate "Design, implement, and test a caching layer for our database"
```
Orchestrates multiple agents for implementation.

## Troubleshooting

### "Error: Failed to connect to Ollama"
**Solution:** Start Ollama server
```bash
ollama serve
```

### "Model not found: mistral:7b"
**Solution:** Pull the model
```bash
ollama pull mistral:7b
```

### Configuration not working
**Solution:** Reset to defaults
```bash
rm ~/.llm_runner/config.yaml
```
Defaults will be created on next run.

### Agent delegation seems slow
**Solution:** Use a faster model
```bash
llm-runner delegate "task" --model neural-chat
```

## What's Each Mode For?

| Mode | Use Case | Output |
|------|----------|--------|
| Interactive (default) | Chat conversations | REPL session |
| `/ask` | Quick questions | Direct response |
| `plan` | Structured planning | `plan.md` file |
| `build` | File/command execution | Files created, commands run |
| `delegate` | Complex multi-step tasks | Execution tree + results |

## Next Steps

- Read **README.md** for full feature list
- Read **ARCHITECTURE.md** for system design details
- Read **DEVELOPMENT.md** to contribute

## Tips

1. **Use context for better results:**
   ```bash
   llm-runner plan "Task" --context
   ```

2. **Try different models for different tasks:**
   ```bash
   llm-runner /ask "Math problem" --model dolphin-mixtral
   ```

3. **Combine modes:**
   - First plan: `llm-runner plan "Create API"`
   - Then build: `llm-runner build "Implement the endpoints from plan.md"`

4. **Check agent logs in delegate mode** - Shows task decomposition and sub-task results

## Common Patterns

### Research then Implement
```bash
# First research
llm-runner delegate "Research best practices for REST API design"

# Then implement
llm-runner build "Create a REST API following the best practices"
```

### Plan then Build
```bash
# Generate plan
llm-runner plan "Build a data processing pipeline"

# Review plan.md, then execute
llm-runner build "Implement the data pipeline from plan.md"
```

### Iterate with Models
```bash
# Try one model
llm-runner /ask "Is this code correct?" --model mistral:7b

# Get second opinion from stronger model
llm-runner /ask "Is this code correct?" --model dolphin-mixtral
```

## Getting Help

- See model responses: `llm-runner --help`
- Read documentation: `README.md`, `ARCHITECTURE.md`, `DEVELOPMENT.md`
- Check config: `cat ~/.llm_runner/config.yaml`

## Performance Tips

1. **Faster responses:** Use `neural-chat` or `mistral:7b`
2. **Better quality:** Use `dolphin-mixtral` (slower)
3. **For coding:** Try `neural-chat` or `dolphin-mixtral`
4. **For planning:** Use `mistral:7b` (good balance)

## What LLM Runner Can Do

✅ Multi-turn conversations
✅ Plan generation and formatting
✅ Safe file creation and modification
✅ Command execution with validation
✅ Multi-agent task decomposition
✅ Complex workflows with sub-agents
✅ Error recovery and retry logic
✅ Workspace isolation for safety

## What LLM Runner Cannot Do

❌ Access the internet
❌ Use paid APIs (only local Ollama)
❌ Modify read-only files
❌ Run privileged commands without permission
❌ Access other users' data

---

Ready to start? Run `llm-runner` and chat with your local LLM!
