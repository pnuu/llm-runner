# API Reference

Python API reference for LLM Runner. Use this to integrate LLM Runner into your own applications or extend its functionality.

## Core Classes

### InteractiveChat

Interactive chat session with Ollama.

#### Constructor

```python
from llm_runner.chat import InteractiveChat

chat = InteractiveChat(
    ollama_url="http://localhost:11434",
    model="mistral:7b",
    temperature=0.7,
    max_context_tokens=4096
)
```

**Parameters**:
- `ollama_url` (str, optional): Ollama API endpoint. Default: `http://localhost:11434`
- `model` (str, optional): Model name. Default: `mistral`
- `temperature` (float, optional): Response creativity (0.0-1.0). Default: `0.7`
- `max_context_tokens` (int, optional): Max tokens before compaction. Default: `4096`

**Raises**:
- `Exception`: If Ollama is not accessible

#### Methods

##### `send_message(user_message)`

Send a message and get response, storing both in history.

```python
response = chat.send_message("What is machine learning?")
print(response)
```

**Parameters**:
- `user_message` (str): User's message text

**Returns**:
- `str`: Assistant's response

**Side Effects**:
- Adds message to conversation history
- Auto-compacts context if threshold exceeded

##### `process_input(user_input)`

Process user input, handling commands.

```python
command, output = chat.process_input("/model")
if command == "model_command":
    print(output)
elif command == "quit":
    print("Exiting")
```

**Parameters**:
- `user_input` (str): User input (may start with `/`)

**Returns**:
- `tuple`: `(command, output)` where command is result type

**Command Types**:
- `"quit"`: Exit signal
- `"clear"`: History cleared
- `"context"`: Context display
- `"model_command"`: Model switched
- `"plan_command"`: Plan executed
- `"build_command"`: Build executed
- `"ask_command"`: Query answered
- `"unknown"`: Unknown command
- `None`: Regular message (not a command)

#### Properties

##### `model`

Get or set the current model.

```python
print(chat.model)  # "mistral:7b"
chat.model = "llama3:8b"
```

##### `temperature`

Get or set temperature for responses.

```python
chat.temperature = 0.5  # More deterministic
chat.temperature = 0.9  # More creative
```

##### `history`

Access conversation history.

```python
history = chat.history
messages = history.messages
print(f"Messages: {len(messages)}")
```

### ConversationHistory

Manages conversation messages with context awareness.

#### Constructor

```python
from llm_runner.chat import ConversationHistory

history = ConversationHistory(max_tokens=4096)
```

**Parameters**:
- `max_tokens` (int, optional): Maximum tokens for context window

#### Methods

##### `add_user_message(content)`

Add user message to history.

```python
history.add_user_message("Tell me about Python")
```

##### `add_assistant_message(content)`

Add assistant response to history.

```python
history.add_assistant_message("Python is a programming language...")
```

##### `get_context()`

Get formatted conversation context.

```python
context = history.get_context()
# Returns formatted conversation for LLM
```

**Returns**:
- `str`: Formatted conversation context

##### `get_context_info()`

Get context statistics.

```python
info = history.get_context_info()
print(f"Messages: {info['message_count']}")
print(f"Tokens: {info['token_count']}")
print(f"Usage: {info['percent_of_max']}%")
```

**Returns**:
- `dict`: Contains `message_count`, `token_count`, `max_tokens`, `byte_count`, `percent_of_max`

##### `is_over_threshold()`

Check if context exceeds 90% of max.

```python
if history.is_over_threshold():
    print("Context usage high!")
    history.compact_context()
```

**Returns**:
- `bool`: True if over threshold

##### `compact_context(recent_messages=4)`

Summarize old messages to reduce context size.

```python
history.compact_context(recent_messages=8)
```

**Parameters**:
- `recent_messages` (int): Number of recent messages to preserve

##### `clear()`

Remove all messages.

```python
history.clear()
```

### OllamaClient

Low-level Ollama integration.

#### Constructor

```python
from llm_runner.llm import OllamaClient

client = OllamaClient(url="http://localhost:11434")
```

**Parameters**:
- `url` (str, optional): Ollama API endpoint

#### Methods

##### `send_prompt(prompt, model, temperature)`

Send prompt to Ollama and get response.

```python
response = client.send_prompt(
    prompt="What is AI?",
    model="mistral:7b",
    temperature=0.7
)
print(response)
```

**Parameters**:
- `prompt` (str): Input text
- `model` (str): Model name
- `temperature` (float): Response creativity

**Returns**:
- `str`: Model's response

**Raises**:
- `Exception`: If Ollama error occurs

##### `get_available_models()`

List available models.

```python
from llm_runner.llm import get_available_models

models = get_available_models(url="http://localhost:11434")
print(models)  # ["mistral:7b", "llama3:8b", ...]
```

**Returns**:
- `list`: Model names

##### `get_model_context_length(model)`

Get context window size for a model.

```python
length = client.get_model_context_length("mistral:7b")
print(f"Context length: {length} tokens")
```

**Parameters**:
- `model` (str): Model name

**Returns**:
- `int`: Context window size in tokens

**Default**: 4096 if unable to determine

## Utility Functions

### check_ollama_connection

Verify Ollama is accessible.

```python
from llm_runner.llm import check_ollama_connection

if check_ollama_connection("http://localhost:11434"):
    print("Ollama is running!")
else:
    print("Ollama is not accessible")
```

**Parameters**:
- `url` (str): Ollama endpoint

**Returns**:
- `bool`: True if accessible

### get_available_models

Get list of available models.

```python
from llm_runner.llm import get_available_models

models = get_available_models("http://localhost:11434")
for model in models:
    print(f"- {model}")
```

**Parameters**:
- `url` (str): Ollama endpoint

**Returns**:
- `list`: Available model names

### load_config

Load configuration from file.

```python
from llm_runner.config import load_config

config = load_config()  # Loads ~/.llm_runner/config.yaml
print(config["model"])

# Or custom path
config = load_config("~/.config/my_llm.yaml")
```

**Parameters**:
- `config_path` (str, optional): Path to config file

**Returns**:
- `dict`: Configuration settings

## Common Patterns

### Pattern 1: Simple Interactive Chat

```python
from llm_runner.chat import InteractiveChat

chat = InteractiveChat(model="mistral:7b")

# Send multiple messages
response1 = chat.send_message("What is Python?")
print(f"Assistant: {response1}")

response2 = chat.send_message("Tell me more about Python!")
print(f"Assistant: {response2}")
```

### Pattern 2: Model Comparison

```python
from llm_runner.chat import InteractiveChat

question = "Explain recursion simply"

for model in ["mistral:7b", "llama3:8b"]:
    chat = InteractiveChat(model=model)
    response = chat.send_message(question)
    print(f"\n{model}:")
    print(response)
```

### Pattern 3: Context-Aware Queries

```python
from llm_runner.chat import ConversationHistory

history = ConversationHistory(max_tokens=2048)

# Build up context
history.add_user_message("I'm building a web app")
history.add_assistant_message("Web apps require...")

history.add_user_message("Should I use React or Vue?")
history.add_assistant_message("React is popular because...")

# Get formatted context
context = history.get_context()
print(context)  # Full conversation formatted for LLM
```

### Pattern 4: Batch Processing

```python
from llm_runner.llm import OllamaClient

client = OllamaClient()
questions = [
    "What is Python?",
    "What is JavaScript?",
    "What is Go?"
]

for question in questions:
    response = client.send_prompt(
        prompt=question,
        model="mistral:7b",
        temperature=0.5
    )
    print(f"Q: {question}")
    print(f"A: {response}\n")
```

### Pattern 5: Context Management

```python
from llm_runner.chat import ConversationHistory

history = ConversationHistory(max_tokens=4096)

# Add messages
for i in range(100):
    history.add_user_message(f"Question {i}")
    history.add_assistant_message(f"Answer {i}")

# Check usage
info = history.get_context_info()
print(f"Usage: {info['percent_of_max']}%")

# Compact if needed
if history.is_over_threshold():
    history.compact_context(recent_messages=8)
    print("Context compacted")
```

## Extension Points

### Custom Command Handlers

Extend `InteractiveChat.process_input()` to add custom commands:

```python
from llm_runner.chat import InteractiveChat

class MyChat(InteractiveChat):
    def process_input(self, user_input):
        # Add custom command
        if user_input.startswith("/custom"):
            request = user_input[8:].strip()
            return ("custom", self._handle_custom(request))
        
        # Fall back to default
        return super().process_input(user_input)
    
    def _handle_custom(self, request):
        # Your custom logic
        return f"Custom result: {request}"
```

### Custom Model Selection

```python
from llm_runner.chat import InteractiveChat

class SelectiveChat(InteractiveChat):
    def __init__(self, allowed_models=None, **kwargs):
        super().__init__(**kwargs)
        self.allowed_models = allowed_models or []
    
    def _handle_model_command(self):
        # Only allow specific models
        models = [m for m in get_available_models() 
                 if m in self.allowed_models]
        # ... continue with limited selection
```

## Error Handling

```python
from llm_runner.llm import OllamaClient, check_ollama_connection
from llm_runner.chat import InteractiveChat

try:
    if not check_ollama_connection():
        raise ConnectionError("Ollama not running")
    
    chat = InteractiveChat(model="mistral:7b")
    response = chat.send_message("Hello!")
    
except ConnectionError as e:
    print(f"Connection error: {e}")
except Exception as e:
    print(f"Error: {e}")
```

## Performance Considerations

### Context Compaction

Large conversations slow down performance. Compact regularly:

```python
history = ConversationHistory(max_tokens=4096)

# Before reaching limits
if history.is_over_threshold():
    history.compact_context(recent_messages=4)
```

### Model Selection

Choose appropriate models for your needs:

```python
# Fast responses (good for real-time)
fast_chat = InteractiveChat(model="mistral:7b")

# High quality (good for analysis)
quality_chat = InteractiveChat(model="llama3:8b")
```

### Connection Pooling

Reuse `OllamaClient` instead of creating new instances:

```python
# Good: Single client
client = OllamaClient()
for question in questions:
    response = client.send_prompt(question, model="mistral:7b")

# Avoid: Multiple clients
for question in questions:
    client = OllamaClient()  # Don't do this
    response = client.send_prompt(question, model="mistral:7b")
```

## See Also

- [README.md](README.md) - Overview
- [CLI_REFERENCE.md](CLI_REFERENCE.md) - Command-line interface
- [INTERACTIVE_CHAT.md](INTERACTIVE_CHAT.md) - Interactive mode guide
- [ARCHITECTURE.md](ARCHITECTURE.md) - Design and internals
