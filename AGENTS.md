# Instructions for AI tools

## Test-driven development (TDD)

You are given a plan. Use test-driven development to implement the plan. First create a high-level test. Then create minimal implementation that makes the tests pass. Then progress incrementaly to more detailed tests. Only one test is created at a time. After creating a test, run all of the existing tests. Take note of the result. Create or modify application code so that the tests pass, but only add minimal amount of code. Only create application code if there are tests for it. Only create new tests after all the existing tests pass.

## General instructions for this project

* Use pyproject.toml and hatchling for packaging.
* Use pytest as testing framework.
* Create the applicaiton plan with test-driven development in mind.
* Use TDD only for the application it self.
* Use the existing conda environment py314 for running any tests.
* If a required package isn't available, request the user to install it.
* To verify that the new CLI can interface with LLMs, use the existing local ollama installation and a small readily available model.
