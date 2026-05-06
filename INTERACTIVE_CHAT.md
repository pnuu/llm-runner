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

### `/plan` - Plan Refinement Mode

Enter interactive plan refinement mode to discuss and refine an existing plan.md file, or create a new plan with full context preservation.

**Usage**:
```
You: /plan

=== Current Plan Summary ===

• Microservices Deployment
  • Architecture Review
    - Service dependencies
    - Load balancer strategy
  • Deployment Strategy
    - Blue-green deployment
    - Canary releases
  • Testing Plan
    - Integration tests
    - Performance tests

Plan added to conversation context. You can now refine it.

You: Add a section about monitoring
AI: I'll add comprehensive monitoring to the plan...

You: /build
Plan refined and saved to: ./plan.md
  Backup saved to: ./backups/plan.md.20250505_150000.backup
```

**Features**:
- **Automatic Outline Display**: Shows condensed summary of plan.md on entry (max 30 lines)
- **Plan Context Injection**: Plan content automatically added to conversation for seamless discussion
- **Change Detection**: Intelligently detects when you refine the plan during conversation
- **Auto-Save**: Refinements automatically saved to plan.md with timestamp-based backups
- **Backup Creation**: Original plan preserved in ./backups/ before refinements
- **Mode Transitions**: Automatically exits plan mode when using other commands (/build, /ask, /model, /quit)

**How It Works**:

1. **Enter Plan Mode**: Type `/plan` to enter refinement mode
   - If plan.md exists, its outline is displayed
   - Plan content added to conversation context
   - Ready for discussion and refinement

2. **Discuss and Refine**: Have natural conversation about the plan
   - Add new sections: "Add a monitoring section"
   - Modify existing content: "Change the timeline to 6 weeks"
   - Ask clarifying questions: "What about error handling?"

3. **Automatic Detection**: LLM Runner detects meaningful refinements
   - Monitors for keywords: add, create, modify, update, remove, etc.
   - Analyzes structural changes (new sections, bullet points)
   - Uses confidence scoring (0.65 threshold) to distinguish discussion from refinement

4. **Auto-Save**: When exiting plan mode or using other commands
   - Detected refinements automatically saved to plan.md
   - Original plan backed up to ./backups/plan.md.TIMESTAMP.backup
   - Confirmation message shows backup location

**Refinement Keywords Detected**:
- **Adding**: "add", "create", "new", "include", "implement"
- **Removing**: "remove", "delete", "eliminate", "drop"
- **Modifying**: "change", "update", "modify", "revise"
- **Structural**: Section markers (##), bullet points, numbered lists

**Example Session**:
```
You: /plan

=== Current Plan Summary ===

• API Development
  • Phase 1: Design
    - Architecture review
    - API specification
  • Phase 2: Implementation
    - Backend development
    - Testing

Plan added to conversation context. You can now refine it.

You: Let's add security considerations to Phase 1
AI: Good idea. I'll add a section on security considerations including 
authentication, authorization, data encryption, and API rate limiting.

## Security Considerations
- OAuth 2.0 for authentication
- Role-based access control
- End-to-end encryption
- Rate limiting and DDoS protection

You: /build
✓ Plan refined and saved to: ./plan.md
  Backup saved to: ./backups/plan.md.20250505_150812.backup

Switched to build mode...
```

**Difference from Main Mode**:
- **Chat mode** (`/plan`): Interactive refinement with context, auto-save on exit, displays outline
- **Main mode** (`llm-runner plan "request"`): Creates new plan.md from scratch, full-screen focused mode

**Tips**:
- Use explicit language ("add", "create", "modify") to ensure refinements are detected
- Plan context persists through your entire conversation
- Multiple refinement iterations are tracked with timestamped backups
- To view context usage, use `/context` command
- To exit without saving changes, use `/quit` or other commands - refinements only save if detected

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

## Plan Refinement Workflow

The plan refinement feature enables iterative plan improvement through natural conversation.

### Complete Workflow Example

```
# Step 1: Enter plan mode (displays existing plan summary)
You: /plan

=== Current Plan Summary ===

• Q2 Development Roadmap
  • Frontend Enhancements
    - Dashboard redesign
    - Performance optimization
  • Backend Services
    - API optimization
    - Database migration
  • DevOps
    - CI/CD pipeline improvements
    - Monitoring setup

Plan added to conversation context. You can now refine it.

# Step 2: Discuss and refine
You: Let's add security testing to the frontend enhancements
AI: Great idea. I'll add security testing as a subtask in the Frontend 
Enhancements section. This should include penetration testing, OWASP compliance 
checks, and security code review.

# Step 3: Continue refining
You: Also add load testing to backend
AI: I'll add load testing and stress testing to the Backend Services section...

# Step 4: Exit to save (or use another command)
You: /build

✓ Plan refined and saved to: ./plan.md
  Backup saved to: ./backups/plan.md.20250505_150812.backup

# Plan.md now includes both new sections and original content preserved
```

### How Refinement Detection Works

The system uses intelligent analysis to distinguish between discussion and refinement:

**1. Keyword Analysis**
- Explicit change keywords: "add", "create", "modify", "remove", "update"
- Weighted scoring: Different keywords have different confidence weights

**2. Structural Analysis**
- Detects new markdown sections (##)
- Counts bullet points and numbered lists
- Identifies new structured content

**3. Confidence Scoring**
- Combines keyword and structural analysis
- Threshold: 0.65 confidence required
- Only meaningful changes trigger auto-save

**Example: What Triggers Refinement**
```
✅ "Add a section on error handling" → Detected (explicit keyword)
✅ "Create a new testing phase" → Detected (create keyword + structure)
✅ "Update the timeline to 8 weeks" → Detected (update keyword)
❌ "What's the timeline?" → Not detected (question, no change keywords)
❌ "That sounds good" → Not detected (discussion, no change keywords)
```

### Backup Management

Refinements are saved with automatic backups:

```bash
# Directory structure after refinement
.
├── plan.md                                    # Current refined version
└── backups/
    ├── plan.md.20250505_143000.backup        # First backup
    ├── plan.md.20250505_143500.backup        # Second backup
    └── plan.md.20250505_150812.backup        # Latest backup

# Backups are timestamped (YYYYMMDD_HHMMSS format)
# Each refinement creates a new backup of the previous version
```

You can manually restore from backups:
```bash
cp backups/plan.md.20250505_143000.backup plan.md
```

### Best Practices

1. **Be Explicit**: Use clear language when refining
   - ✅ "Add a performance testing section"
   - ❌ "We should probably think about testing"

2. **Preserve Context**: Plan remains available throughout conversation
   - Reference existing sections by name
   - Build on previous decisions
   - Maintain consistency

3. **Check Progress**: Use `/context` to monitor token usage
   - Long plans consume more context space
   - May need to `/clear` in very long sessions

4. **Review Backups**: Check backups if unexpected changes occur
   ```bash
   ls -la backups/
   cat backups/plan.md.20250505_143000.backup
   ```

5. **Transition Modes**: Exit plan mode intentionally
   - Using `/build`: Saves refinements then switches to build mode
   - Using `/ask`: Automatically exits plan mode first
   - Using `/quit`: Saves refinements then exits application

### Limitations & Considerations

- **Refinement Detection**: May not detect implicit changes (e.g., "let's discuss deployment")
- **Context Space**: Large plans consume more conversation context
- **Single Plan**: Each directory has one plan.md; starting new mode creates new entry
- **Overwrite Protection**: Original content preserved in backups before any updates

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

## Streaming Output

LLM responses are streamed in real-time, meaning you see tokens appear as they are generated:

### What You'll Notice

When you send a message, the assistant's response appears **progressively** rather than all at once:

```
User: /ask What are the top 3 programming languages to learn?

AI:
1. Python - Versatile,
 easy to learn, wi...
```

Notice how tokens appear continuously as the model generates them. This is especially visible with:
- **Longer responses** - You see output building up line by line
- **Thinking models** (like deepseek-r1) - Reasoning is visible in `<think>` tags as it happens
- **Slow models** - Instead of waiting silently, you see incremental progress

### Perceived Latency

Streaming makes responses *feel* much faster:
- First tokens appear quickly (within 100-500ms)
- Full response takes same time, but feels shorter due to progressive display
- Thinking model output gives confidence that the model is working

### Examples

**Fast Response (stays on one line):**
```
> What is 2+2?
> 2 + 2 = 4
```

**Longer Response (streams multiple lines):**
```
> Write a Python function to check if a number is prime
> def is_prime(n):
>     if n < 2:
>         return False
>     for i in range(2, int(n**0.5) + 1):
>         if n % i == 0:
>             return False
>     return True
```

**Thinking Model Output (reasoning visible):**
```
> Explain quantum entanglement
> <think>
> The user is asking about quantum entanglement. I should explain...
> * Correlation between particles
> * Non-locality
> * Bell's theorem
> * Applications in quantum computing
> </think>
>
> Quantum entanglement is a phenomenon where...
```

### Timeout Protection

If a response takes longer than expected, there's a safety timeout:
- Default: 30 seconds per request
- If exceeded, the request is cancelled and you're notified
- Prevents indefinite hangs from unresponsive models

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
