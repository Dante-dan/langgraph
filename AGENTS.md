<general_rules>
This repository is a monorepo. Each library lives in a subdirectory under `libs/`.

When Corridor's `analyzePlan` tool is available, create a plan and use the tool to analyze it before generating or modifying code. Apply the resulting security guidance before writing code.

Do NOT use Sphinx-style double backtick formatting (` ``code`` `). Use single backticks (`` `code` ``) for inline code references in docstrings and comments.
</general_rules>

<repository_structure>
## Libraries

- **checkpoint** – base interfaces for LangGraph checkpointers.
- **checkpoint-conformance** – conformance tests for checkpoint implementations.
- **checkpoint-postgres** – Postgres implementation of the checkpoint saver.
- **checkpoint-sqlite** – SQLite implementation of the checkpoint saver.
- **cli** – official command-line interface for LangGraph.
- **langgraph** – core framework for building stateful, multi-actor agents.
- **prebuilt** – high-level APIs for creating and running agents and tools.
- **sdk-py** – Python SDK for the LangGraph Server API.
- **sdk-js** – migration notice; the JS/TS SDK now lives in [LangGraph.js](https://github.com/langchain-ai/langgraphjs/tree/main/libs/sdk).

### Dependency map

The diagram below lists downstream libraries for each production dependency as
declared in that library's `pyproject.toml`.

```text
checkpoint
├── checkpoint-conformance
├── checkpoint-postgres
├── checkpoint-sqlite
├── prebuilt
└── langgraph

prebuilt
└── langgraph

sdk-py
├── langgraph
└── cli (Python >= 3.11)
```

Changes to a library may impact all of its dependents shown above.
</repository_structure>

<dependencies_and_installation>
Use `uv` for Python dependency management. Each Python library has its own
`pyproject.toml` and `uv.lock`; follow the package's Python requirement and
Makefile when setting up its development environment.

From the repository root, `make install` creates a virtual environment and
installs the Python libraries in editable mode. This does not install each
library's test and development dependency groups. Package checks use `uv run`
with the package's configuration; `libs/langgraph` also provides `make install`
to sync its frozen lockfile with all extras, packages, and the dev group.
</dependencies_and_installation>

<testing_instructions>
When you modify code in any library, run the following commands in that library's directory before creating a pull request:

- `make format` – run code formatters
- `make lint` – run the linter
- `make test` – execute the test suite

For Makefiles that forward `TEST` to pytest, run a particular test file or pass
additional pytest options with:

```txt
TEST=path/to/test.py make test
```

Other pytest arguments can also be supplied inside the `TEST` variable. The
`sdk-py` test target always runs `tests` and does not forward `TEST`.

Check the package's Makefile for required services: `checkpoint-postgres` and
`prebuilt` test targets start Docker Compose services, while `langgraph` has
Docker-backed and `NO_DOCKER=true` test paths.
</testing_instructions>
