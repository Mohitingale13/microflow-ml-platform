# Contributing to MicroFlow

First off, thank you for considering contributing to MicroFlow! It's people like you that make MicroFlow such a great ML operations and observability platform.

## Code of Conduct
By participating in this project, you are expected to uphold our Code of Conduct. Please be respectful, constructive, and inclusive to everyone in the community.

## How Can I Contribute?

### Reporting Bugs
This section guides you through submitting a bug report for MicroFlow. Following these guidelines helps maintainers and the community understand your report, reproduce the behavior, and find related reports.
* Use a clear and descriptive title for the issue to identify the problem.
* Describe the exact steps which reproduce the problem in as many details as possible.
* Provide specific examples to demonstrate the steps.
* Include screenshots or animated GIFs which show you following the described steps.

### Suggesting Enhancements
Enhancement suggestions are tracked as GitHub issues.
* Use a clear and descriptive title for the issue.
* Provide a step-by-step description of the suggested enhancement.
* Explain why this enhancement would be useful to most MicroFlow users.

### Pull Requests
1. **Fork the repo** and create your branch from `main`.
2. **Setup your environment:**
   * Backend: Python 3.11+, install dependencies via `pip install -r backend/requirements.txt`
   * Frontend: Node.js 18+, install dependencies via `cd frontend && npm install`
3. **If you've added code that should be tested, add tests.** (The backend relies heavily on `pytest`).
4. **Ensure the test suite passes:** `docker compose exec backend pytest -v` or `pytest -v` locally.
5. **Format your code.** We prefer clean, readable code with descriptive variable names.
6. **Ensure your UI changes are responsive.** Test on both desktop and mobile viewports.
7. **Issue that PR!**

## Development Guidelines

### Architecture Rules
MicroFlow is built with strict architectural boundaries. Please adhere to them:
- **Routers**: Handle HTTP concerns (request validation, status codes). No business logic.
- **Services**: Handle all business logic. They call repositories.
- **Repositories**: Handle all SQLAlchemy database queries. Services never write raw SQL or SQLAlchemy queries directly.
- **AI Layer (Zero-Hallucination)**: Gemini must *never* be given raw database access. Fetch data via repositories, structure it as context, and pass it to the `AssistantService`.
- **Training Engine**: All training logic must remain HTTP-free. Use the Model Factory pattern for adding new estimators.

### Frontend Styling
- Use Tailwind CSS for styling.
- Avoid hardcoded HEX colors; use CSS variables (e.g., `var(--color-surface)`) to ensure Light/Dark mode compatibility.
- Build components mobile-first.

Thank you for contributing!
