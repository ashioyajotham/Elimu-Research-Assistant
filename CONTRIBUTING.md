# Contributing to Elimu Research Assistant

First off, thank you for considering contributing to Elimu Research Assistant! It's people like you that make this tool better for everyone.

## Getting Started

### Prerequisites

- Python 3.9 or higher
- Git
- A Gemini API key
- A Serper API key for web searches

### Setup for Development

1. Fork the repository on GitHub
2. Clone your fork:
   ```bash
   git clone https://github.com/YOUR-USERNAME/elimu_research_assistant.git
   cd elimu_research_assistant
   ```

3. Set up a virtual environment:
   ```bash
   python -m venv venv
   # On Windows
   venv\Scripts\activate
   # On macOS/Linux
   source venv/bin/activate
   ```

4. Install the package in development mode:
   ```bash
   pip install -e .
   ```

5. Create a `.env` file in the root directory with your API keys:
   ```
   GEMINI_API_KEY=your_gemini_api_key_here
   SERPER_API_KEY=your_serper_key_here
   ```

## Contributing

We welcome contributions from educators, developers, and anyone passionate about improving education in Kenya.

### For Educators
- Provide [feedback on generated content quality and relevance](https://github.com/ashioyajotham/elimu_research_assistant/issues)
- Suggest common use cases and classroom scenarios
- Share successful classroom implementations and best practices
- Report content gaps, inaccuracies, or cultural sensitivity issues
- Test new features with real students and provide feedback

### For Developers
- Enhance localization algorithms for Kenyan context
- Improve educational content formatting and structure
- Add new source integration capabilities
- Optimize for low-bandwidth environments common in Kenyan schools
- Develop mobile-friendly interfaces

### For Education Researchers
- Validate pedagogical effectiveness of generated content
- Study impact on student engagement and learning outcomes
- Research cultural context integration effectiveness
- Analyze curriculum alignment accuracy

## Development Workflow

1. Create a branch for your feature or bugfix:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes, adding tests if applicable.

3. Run the tests to ensure your changes don't break existing functionality.

4. Commit your changes:
   ```bash
   git commit -m "Add your meaningful commit message here"
   ```

5. Push to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

6. Submit a pull request from your forked repo to the main repository.

## Code Style Guidelines

- Follow [PEP 8](https://peps.python.org/pep-0008/) for Python code style.
- Use meaningful variable and function names.
- Include docstrings for all functions, classes, and modules.
- Keep line length to a maximum of 100 characters.
- Use type hints where possible.

Example function with proper documentation and type hints:
```python
def process_query(query: str, max_results: int = 5) -> Dict[str, Any]:
    """
    Process a search query and return the results.
    
    Args:
        query: The search query to process
        max_results: Maximum number of results to return
        
    Returns:
        A dictionary containing search results and metadata
    """
    # Implementation here
    return results
```

## Testing

- Write tests for new functionality using pytest.
- Ensure all tests pass before submitting a pull request.
- Run tests with: `pytest`

## Pull Request Process

1. Update the README.md with details of changes if applicable.
2. Update the CHANGELOG.md to describe your changes.
3. The PR should work on the main branch.
4. Include a description of what your changes do and why they should be included.
5. Reference any related issues in your PR description.

## Reporting Issues

- Use the GitHub issue tracker to report bugs.
- Check existing issues before opening a new one.
- Include detailed steps to reproduce the bug.
- Include information about your environment (Python version, OS, etc.).

## Feature Requests

We welcome feature requests! Please provide:
- A clear description of the feature
- Why it would be valuable
- Any implementation ideas you have

## Code of Conduct

- Be respectful and inclusive.
- Focus on the issue, not the person.
- Welcome newcomers and help them learn.
- Ensure your contributions align with the project's goals.

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.

## Questions?

Feel free to reach out if you have any questions about contributing!

Thank you for making Elimu Research Assistant better!
