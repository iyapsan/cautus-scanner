
<!--
This file defines workspace-specific instructions for AI tools (e.g., GitHub Copilot, ChatGPT, Claude).
It ensures generated code and tests follow our team's standards for style, structure, and quality.
-->


# **All generated code and tests must be production-ready, review-quality, and require no further manual improvement to meet the standards below.**

## Code & Test Quality Checklist
- [ ] Production-ready and review-quality
- [ ] Maximal branch and condition coverage (for tests), and robust error/edge case handling (for code)
- [ ] Idiomatic, modern, and maintainable Python
- [ ] Ready for CI and code review with no further manual improvement needed
- [ ] Consistent terminology, file naming, and structure
- [ ] All code and tests follow the detailed standards below

## What Not To Do
- Do NOT generate trivial or “minimum example” code or tests
- Do NOT skip edge cases or error handling
- Do NOT use non-idiomatic or legacy patterns
- Do NOT require manual improvement after generation
- Do NOT ignore any part of these instructions


# Python Code Standards
# General Code Quality

- All application logic must be robust, maintainable, and idiomatic.
- Always place all imports at the top of the file, except in rare cases where function-local imports are required (e.g., to avoid circular dependencies or for heavy, optional dependencies). Justify any function-local imports with a comment.
- Handle all expected and edge-case inputs gracefully.
- Use clear, concise docstrings and comments for all functions and classes.
- Prefer composition, clear separation of concerns, and single responsibility.
- Validate both output and side effects where applicable.
- Ensure all code integrates well with existing modules and follows project conventions.

- All code must strictly follow **PEP8**, including import order, whitespace, and line length.
- Use `snake_case` for variables/functions, `PascalCase` for classes.
- Always use **type hints** for all function arguments and return values, even in scripts and tests.

- Prefer modern Python features:
  - Use `pathlib.Path` for all filesystem operations.
    - Use `.glob()` or `.rglob()` for file discovery.
    - Avoid `os.path`, `os.walk`, and `glob.glob` unless absolutely necessary.
  - Use `ast` for parsing Python code (e.g., finding functions) — never use regex for code parsing.
  - Use fstrings for all string formatting — avoid `%` and `.format()`.
  - Use `@dataclass` for data containers instead of writing manual `__init__`, `__repr__`, etc.
  - Use comprehensions and generator expressions (`[x for x in ...]`, `{k: v for ...}`, etc.) for concise iteration and construction.
  - Use built-ins like `any()`, `all()`, `sum()`, `enumerate()`, `zip()`, and `sorted()` instead of manual loops.-
  - Use `with` statements for all resource management (e.g., file I/O, locks).
  - Use the walrus operator (`:=`) where it improves readability (Python 3.8+).
  - Use structural pattern matching (`match-case`) for multi-branch logic (Python 3.10+).
  - Prefer `enum.Enum` for named constants.
  - Use tuple/list unpacking and starred expressions for clean assignments.
  - Use `collections` and `itertools` where appropriate:
    - e.g., `defaultdict`, `Counter`, `namedtuple`, `groupby`, `chain`, etc.
  - Avoid mutable default arguments — use `None` and assign inside the function.

- Never use `print()` for logging or operational output — always use the project logger.
- Do not add shebang lines unless there is a documented, project-specific reason.
- All code must be autoformatted with a tool like `black` or `ruff` after generation.
- All functions and classes must have clear, concise docstrings. For test functions, add docstrings only when they clarify complex scenarios or edge cases; for simple, self-explanatory tests, docstrings are optional.
- Add comments for any non-obvious logic or edge cases.
- All resource creation/update functions must be idempotent.

# Logging & Error Handling

- Use structured logging - Never use `print()` for operational output.
- Log unexpected conditions to aid debugging.
- Handle exceptions gracefully and avoid silent failures.
- Catch specific exceptions, not bare `except:` blocks.
- Use `contextlib.suppress()` when ignoring known exceptions is intentional.

# Retry Logic & Resilience

- **Always use the `backoff` library for retry logic** — do not implement custom retry loops.
- Use `@backoff.on_exception()` decorator for handling transient errors (network failures, rate limits, timeouts).
- Configure appropriate `giveup` conditions for non-retryable errors (e.g., 404, validation errors).
- Use exponential backoff (`backoff.expo`) as the default strategy.
- Always specify `max_tries` to prevent infinite loops.
- Log retry attempts at appropriate levels for debugging.
- Example pattern:
  ```python
  import backoff
  
  @backoff.on_exception(
      backoff.expo,
      (NetworkError, TimeoutError),
      max_tries=3,
      giveup=lambda e: isinstance(e, ValueError)  # Don't retry validation errors
  )
  def fetch_data(...):
      # Your code here
  ```

# Testing Best Practices

- When testing state changes or error conditions, always use the public API or documented workflow (e.g., call delete() instead of directly setting internal flags). Avoid manipulating internal state unless testing for very specific, documented edge cases.
- All generated tests must maximize branch and condition coverage, include edge cases and error conditions, and be ready for immediate use in CI and code review with no further manual improvement needed.
- Only add tests for edge cases and error conditions if they validate custom logic or error handling in your code. Avoid tests that merely verify standard library behavior unless your code customizes or wraps it.
- Use `pytest` with idiomatic patterns:
  - Use `pyproject.toml` ([tool.pytest.ini_options]) for pytest configuration — do not use `pytest.ini`.
  - Prefer function-based tests unless setup/teardown is needed.
  - Use `@pytest.mark.parametrize` to reduce duplication.
  - Use `pytest-mock` and `monkeypatch` instead of `unittest.mock`.
- Place all unit tests in `tests/unit_tests/`.
- All test files must be named `test_*.py`.
- All test functions must be named `test_*`.
- Use descriptive fixture names (e.g., `valid_message`, `empty_message`).
- Mock external systems only when necessary, patching at the import path used in the code under test.
- Ensure all tests are isolated from global state and environment variables.
- Write meaningful assertions and cover edge cases in all tests.
- Avoid multiple asserts unless comparing dictionaries or using parameterization.
- Validate both output and side effects.
- Avoid test smells:
  - Redundant assertions
  - Overuse of mocks
  - Tests that depend on execution order
  - Redundant assertions
  - Overuse of mocks
  - Tests that depend on execution order
  - Tests that do not increase branch or condition coverage, or do not validate custom logic or error handling in your code. Tests should not simply verify mock configuration or standard library behavior.
- Use dictionary comparison for structured output validation.
- Avoid asserting internal implementation unless necessary.
- Ensure tests integrate well with existing ones.

## Mocking Guidelines: ##
- When mocking a method, only assert the interaction (e.g., `assert_called()`, `assert_called_with()`) unless your code transforms or processes the return value.
- Avoid asserting the return value of a mock unless it validates custom logic in your code, not just the mock configuration.

# YAML Generation

- Include comments for required and optional fields.
- Use environment variable placeholders in sample YAML.

# AI Usage Notes

- Use Copilot Chat for code explanations, refactoring, or troubleshooting.
- These rules apply across all AI-assisted workflows, including PRD generation, task breakdowns, and automated test scaffolding.
- When generating new code or tests, ensure they follow modern, idiomatic, and maintainable Python practices.
- For full test philosophy and advanced practices, see: [python-unit-test-guidelines.md](./prompts/python-unit-test-guidelines.mdc)
