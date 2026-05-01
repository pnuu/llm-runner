# Copilot Instructions for llm-runner

## Project Overview

**llm-runner** is a CLI tool similar to Claude Code, Copilot CLI, and OpenCode. It provides a command-line interface for accessing both local and online LLMs, with agents that can read files, write files, run shell commands, ask user questions, and create sub-agents.

The application is a Python package (`llm_runner`) built with `pyproject.toml` and `hatchling`.

## Development Approach: Test-Driven Development (TDD)

This project uses strict TDD methodology:

1. **Write tests first**: Create a high-level test before any implementation
2. **Minimal implementation**: Write only the minimal code needed to make the test pass
3. **Incremental progress**: One test at a time; run the full test suite after each change
4. **Only test application code**: Apply TDD to the application itself, not test infrastructure

## Build, Test, and Lint Commands

### Testing
- **Run all tests**: `pytest` (via the `py314` conda environment)
- **Run a single test**: `pytest tests/test_module.py::test_function_name`
- **Run with coverage**: `pytest --cov=llm_runner`

### Environment
- Use the conda environment `py314` for all test runs and development

### Dependencies
- If a required package is not installed, request the user to install it via conda or pip
- Core dependencies are managed in `pyproject.toml` with `hatchling` as the build backend

## Architecture & Key Concepts

### Two Default Modes
- **Plan mode**: Analyzes requirements and creates a plan without writing files (except the plan itself)
- **Build mode**: Executes requests and creates output directly

### Core Tooling
The application provides configurable tools that agents can use:
- **File operations**: Reading and writing files
- **Shell execution**: Running shell commands
- **Agents**: Creating and managing sub-agents
- **User interaction**: Asking questions and getting responses

### Configuration Hierarchy
1. **Project-level** (`AGENTS.md`): Takes precedence over global config
2. **Global-level**: Default settings unless overridden by project config
3. **Special case**: Global instructions marked as "The Law" always apply

### Agent Configuration
- Agents can be configured to use specific LLM models
- Tools can be enabled/disabled on a per-agent basis

## Key Conventions

### Project Configuration File: AGENTS.md
- The CLI looks for `AGENTS.md` in the project directory as guidance for agents
- This file contains project-specific instructions and conventions for AI tools working on the codebase
- Format: Markdown with clear sections for different instruction types

### LLM Model Selection
- Both local models (via Ollama) and online models are supported
- Local testing uses the existing Ollama installation with small, readily available models
- This allows for quick iteration without external API calls

### Package Structure
- Main package: `llm_runner`
- Build system: `pyproject.toml` with hatchling
- Testing: pytest with full code coverage expectations

## Verification & Local Testing

When testing CLI functionality with LLMs:
- Use the local Ollama installation for verification
- Choose small, readily available models for fast iteration
- Verify CLI can successfully interface with LLM endpoints before considering features complete

## Git Workflow

- **Commit when features are complete**: Commit only after a feature has been fully implemented and tested successfully
- **Avoid frequent small commits**: Do not commit every small addition, change, or intermediate step
- **One logical unit per commit**: Each commit should represent a complete, working feature or significant bug fix
- **Meaningful commit messages**: Use clear, descriptive commit messages that explain what was implemented
