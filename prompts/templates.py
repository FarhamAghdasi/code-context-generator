# prompts/templates.py
"""Prompt templates for various use cases."""

PROMPT_TEMPLATES = {
    "code_review": {
        "name": "Code Review & Improvement",
        "template": """Please carefully review this project and perform the following tasks:

1. **Analyze the complete structure** - Understand the architecture, patterns, and organization
2. **Identify issues** - Find bugs, code smells, security vulnerabilities, and performance bottlenecks
3. **Suggest improvements** - Provide specific recommendations for:
   - Code quality and readability
   - Performance optimizations
   - Security enhancements
   - Better design patterns
   - Missing error handling
4. **Prioritize changes** - Rank suggestions by impact and effort

Project Structure and Files:
---"""
    },
    "documentation": {
        "name": "Documentation Generation",
        "template": """Please generate comprehensive documentation for this project:

1. **Overview** - Project purpose, key features, and architecture
2. **Setup Instructions** - Installation, configuration, and dependencies
3. **API Documentation** - All public functions, classes, and methods with parameters and return values
4. **Usage Examples** - Common use cases with code snippets
5. **Contributing Guidelines** - How to contribute, coding standards, and PR process
6. **Troubleshooting** - Common issues and solutions

Project Structure and Files:
---"""
    },
    "commit_messages": {
        "name": "Generate Commit Messages",
        "template": """For each change you suggest or make, provide a commit message following the Conventional Commits standard:

Format: <type>(<scope>): <description>

Types: feat, fix, docs, style, refactor, perf, test, chore
Example: "feat(auth): add JWT token validation"

Include:
- Clear, concise description (50 chars max for subject)
- Detailed body explaining what and why (if needed)
- Breaking changes notation if applicable

Project Structure and Files:
---"""
    }
}