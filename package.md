# Description of the application

This documents is a description for AI tools what the application should do.

## Packaging

* The application should be an installable Python package using pyproject.toml, hatchiling and a pytest testing suite with full code coverage.
* The Python package is named llm_runner.

## Overall description

* The software is named LLM-Runner.
* The application should be a CLI similar to Claud Code, Copilot CLI, OpenCode, Codex etc.
* The main use-case would be to access local LLMs, but also online models should be usable.
* There should be two default modes, build and plan.
* Plan mode will not write files, other than possibly the plan it self.
* Build mode would create the requested output directly.
* The application should have tooling for
  * reading files
  * writing files
  * running shell commands
  * creating agents
  * asking questions from the user

## Finer details

* The tooling should be possible to disable/enable per agent.
* The agents should be possible to configure to use a specific model.
* The CLI should use AGENTS.md as guidance if it exists.
* There should be both global and per-project configuration.
* The instructions on the project should take precendece over global instructions, unless there are global instructions given as The Law.
