# Interactive Chat Mode Guide

Interactive chat is the default mode of LLM Runner, providing a persistent conversation with an LLM where you can execute specialized commands without losing context.

## Getting Started

### Start Interactive Chat
```bash
llm-runner
```

With a specific model:
```bash
llm-runner --model llama3:8b
llm-runner --model mistral:7b
```

With a custom config:
```bash
llm-runner --config ~/.llm_runner/custom.yaml
```

### First Chat Session

```
Connected to Ollama at http://localhost:11434
Available models: mistral:7b, llama3:8b, qwen:7b
Using model: mistral:7b
Commands: '/quit' (exit), '/clear' (history), '/context' (info), '/model' (select),
          '/plan' (plan mode), '/build' (build mode), '/ask' (non-storing ask)

You: Hello! What's the weather today?
Assistant: I don't have access to real-time weather data as I'm an offline AI. However, if you tell me your location...

You: /quit
Goodbye!
```

## Available Commands

### `/model` - Interactive Model Selection

Switch between available models without exiting chat.

**Usage**:
```
You: /model
Available models:
  1. mistral:7b  ← current
  2. llama3:8b
  3. neural-chat
Select model (number or Enter for current): 2
Switched to model: llama3:8b

You: Now I'm using llama3!
```

**Behavior**:
- Shows list of all available models from Ollama
- Current model marked with `← current`
- Enter number to switch
- Press Enter with no selection to keep current model
- Press Ctrl+C to cancel

**Use Cases**:
- Compare responses from different models
- Switch to faster model for quick queries
- Try specialized models (e.g., code-focused models)

### `/plan` - Plan Mode Within Chat

Generate a structured plan without switching modes.

**Usage**:
```
You: /plan
Enter plan request: Design a user authentication system

Plan mode: 'Design a user authentication system' - complete in main mode for persistence
```

**Behavior**:
- Prompts for plan request
- Generates plan using current context
- Returns to chat after completion
- Context remains intact

**Difference from Main Mode**:
- Chat mode: `/plan` is for quick planning within conversation
- Main mode: `llm-runner plan "request"` creates persistent plan.md file

### `/build` - Build Mode Within Chat

Execute build tasks without exiting chat.

**Usage**:
```
You: /build
Enter build request: Create a hello world in Python

Build mode: 'Create a hello world in Python' - complete in main mode for persistence
```

**Behavior**:
- Prompts for build request
- Executes with current context
- Returns to chat with results
- Context remains intact

**Difference from Main Mode**:
- Chat mode: `/build` focuses on context-aware execution
- Main mode: `llm-runner build "request"` with full file system operations

### `/ask` - Context-Aware Non-Storing Query

Ask questions using conversation context without adding to history.

**Usage**:
```
You: I'm building a REST API. What endpoints should I have?
Assistant: For a complete REST API, consider...

You: /ask
Ask (with context): Should I use POST or PUT for updates?
[Not stored in history]
Assistant: POST is typically used for creating resources, while PUT is for updates...

You: /context
=== Context Usage ===
Messages: 2
Tokens: 1250 / 32768
```

**Key Difference**:
- Regular questions: Stored in history, add to context for future messages
- `/ask` queries: Use current context but NOT stored for future messages
- Perfect for: Clarifications, fact-checking, side questions

**When to Use `/ask`**:
- Asking about implementation details without polluting main topic
- Quick clarifications that don't need to persist
- Exploring alternatives without committing to them
- Testing ideas without affecting conversation flow

### `/context` - View Context Information

Display current conversation context usage.

**Output**:
```
You: /context

=== Context Usage ===
Messages: 42
Tokens: 28456 / 32768
Bytes: 185,234
Usage: 87%

⚠️  Context Over Threshold
Excess tokens: 3,688
Recommendation: Compact context or start new session
Use /clear to reset conversation
```

**Information Provided**:
- **Messages**: Number of messages in conversation
- **Tokens**: Current usage vs. model's max context window
- **Bytes**: Size of conversation in memory
- **Usage**: Percentage of context window used
- **Recommendations**: Warnings if approaching limits

**When to Check**:
- Before long operations
- When chat seems slow or responses are short
- To understand model's capabilities

### `/clear` - Clear Conversation History

Remove all messages from current session.

**Usage**:
```
You: /clear
Conversation history cleared.
```

**Effect**:
- Removes all user and assistant messages
- Fresh start with same model and config
- Context window resets to 0 tokens

**When to Use**:
- Starting a completely new topic
- Reducing context before complex operations
- Removing sensitive information
- Recovering from confusing conversation flow

### `/quit` - Exit Chat

Gracefully exit interactive mode.

**Usage**:
```
You: /quit
Goodbye!
(returns to command line)
```

## Common Workflows

### Workflow 1: Multi-Model Comparison

Compare how different models respond to the same question.

```
You: Explain machine learning in 2 sentences
Assistant: [mistral's response...]

You: /model
Available models:
  1. mistral:7b ← current
  2. llama3:8b
Select: 2

You: Can you repeat that 2-sentence explanation?
Assistant: [llama3's response - same topic, different perspective]

You: /model
Select: 1
(switch back to mistral)
```

**Benefits**:
- Find best model for your use case
- Compare quality/speed trade-offs
- Test before changing config

### Workflow 2: Plan → Execute → Chat

Use planning mode to structure work, then execute.

```
You: I need to refactor my authentication module
Assistant: Here are the key refactoring points...

You: /plan
Enter plan request: Refactor authentication module to use JWT

[plan generated based on current context]

You: /build
Enter build request: Implement JWT refactoring from the plan

[build executed, files created]

You: How should I test the new JWT implementation?
Assistant: [continues with context about your refactoring...]
```

**Benefits**:
- Generate plans within conversation flow
- Execute immediately with full context
- Track decisions in main conversation

### Workflow 3: Context-Aware Investigation

Use `/ask` for exploratory questions without disrupting main flow.

```
You: I'm building an e-commerce platform. Should I use PostgreSQL?
Assistant: PostgreSQL is excellent for... [detailed response]

You: /ask
Ask: What about MongoDB as an alternative?
[Not stored in history]
Assistant: MongoDB is a NoSQL option... [comparison]

You: What's your recommendation for my project?
Assistant: Based on our discussion about e-commerce platforms...
(Note: The MongoDB question isn't in the history, but context is available)
```

**Benefits**:
- Explore alternatives without cluttering history
- Keep main topic thread clean
- Test ideas informally

### Workflow 4: Monitoring Context with Complex Conversations

Track context usage during long conversations.

```
You: [long explanation of your project - message 1]
Assistant: [response - message 2]

You: [more details - message 3]
Assistant: [response - message 4]

You: /context
Messages: 4
Tokens: 8,234 / 32,768
Usage: 25%

You: [continue until...]

You: /context
Messages: 85
Tokens: 29,456 / 32,768
Usage: 90%
⚠️  Context Over Threshold

You: /clear
(Fresh start, or summarize before continuing)
```

**Benefits**:
- Proactively manage context window
- Know when to summarize or start fresh
- Avoid hitting token limits

## Tips & Tricks

### Switching Models Effectively

```bash
# Start with a fast model for brainstorming
llm-runner --model mistral:7b

You: /model
# Switch to more capable model when needing deep analysis
Select: 2 (llama3:8b)
```

**Model Selection Tips**:
- **mistral:7b**: Fast, good for general queries, ~7B parameters
- **llama3:8b**: Balanced quality/speed, ~8B parameters
- **llama3:70b**: Slowest but most capable, if available
- **qwen:7b**: Specialized for code, multilingual support

### Reducing Context Size

When approaching token limits:

```bash
You: /context
# See usage at 85%+

# Option 1: Clear and start fresh
You: /clear

# Option 2: Start a new session in another terminal
# (preserve current session for reference)

# Option 3: Ask for summaries before clearing
You: Before I clear, can you summarize our discussion?
Assistant: Here's a summary...
```

### Asking Better Questions with Context

The `/ask` command is powerful when you want context but not history:

```bash
You: I'm building authentication for a SaaS app
Assistant: Here are the key considerations...

# Now explore implementation details without adding to history
You: /ask
Ask: Should I implement refresh tokens or just access tokens?

# Back to main topic (question not stored)
You: What database should I use?
# (response still focused on SaaS auth, not refresh tokens)
```

### Using Model Selection for Problem Solving

```bash
You: Why is my code slow?
Assistant: [initial analysis on mistral]

You: /model
# Try another model's perspective
Select: 2 (llama3)

You: Why is my code slow?
Assistant: [different analysis, might catch something mistral missed]

You: /model
# Back to original
Select: 1
```

## Keyboard Navigation

Some terminals support arrow keys in `/model` selection:

```
You: /model
Available models:
  1. mistral:7b
  2. llama3:8b  ← arrow down here
  3. neural-chat
Select: [type number and press Enter]
```

Alternatively, just type the number directly.

## Session Persistence

Interactive sessions can be automatically preserved and restored:

```bash
# Start chat
$ llm-runner
You: [conversation]
You: /quit

# Later: can restore session manually or start fresh
$ llm-runner
```

Sessions allow you to pause and resume conversations across multiple sessions.

## Troubleshooting

### "No models available"
- Ensure Ollama is running: `ollama serve`
- Check connection: `ollama list`
- Verify correct host in config: `~/.llm_runner/config.yaml`

### `/model` shows wrong models
- Run `ollama list` to verify available models
- Some models may need pulling: `ollama pull llama3:8b`

### Context usage showing very high
- This is normal in long conversations
- Use `/context` to see exact usage
- Use `/clear` when reaching limits
- Or start a new session

### Chat seems slow
- Could be model loading
- Could be context approaching limit
- Try `/model` to switch to faster model
- Check system resources

## See Also

- [CLI_REFERENCE.md](CLI_REFERENCE.md) - Complete command line reference
- [README.md](README.md) - Main documentation
- [API_REFERENCE.md](API_REFERENCE.md) - Python API for extending
- [ARCHITECTURE.md](ARCHITECTURE.md) - Design and internals
