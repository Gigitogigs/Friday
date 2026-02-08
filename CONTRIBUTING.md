# Contributing to Friday

Thank you for your interest in contributing to Friday! This document provides guidelines and instructions for contributing.

## Table of Contents
- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Process](#development-process)
- [Pull Request Process](#pull-request-process)
- [Coding Standards](#coding-standards)
- [Testing](#testing)

---

## Code of Conduct

### Our Pledge
We are committed to providing a welcoming and inclusive environment for all contributors, regardless of experience level, background, or identity.

### Expected Behavior
- Be respectful and considerate
- Use inclusive language
- Accept constructive criticism gracefully
- Focus on what's best for the community
- Show empathy towards others

### Unacceptable Behavior
- Harassment, discrimination, or offensive comments
- Trolling or insulting remarks
- Publishing others' private information
- Any conduct that would be inappropriate in a professional setting

---

## Getting Started

### Prerequisites
- Python 3.11 or higher
- Git
- Ollama installed locally
- Basic understanding of Python and async programming

### Setting Up Your Development Environment

1. **Fork and Clone**
   ```bash
   git clone https://github.com/YOUR_USERNAME/Friday.git
   cd Friday
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # Linux/Mac
   source venv/bin/activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Verify Setup**
   ```bash
   # Run tests
   python -m pytest tests/ -v
   
   # Check Friday status
   python friday.py status
   ```

---

## Development Process

### Finding Issues to Work On
- Check the [Issues](../../issues) page for open tasks
- Look for issues labeled `good first issue` or `help wanted`
- Comment on an issue to let others know you're working on it

### Creating a Feature Branch
```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/bug-description
```

### Branch Naming Convention
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation updates
- `test/` - Test additions/improvements
- `refactor/` - Code refactoring

---

## Pull Request Process

1. **Update Your Branch**
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Run Tests**
   ```bash
   python -m pytest tests/ -v
   ```

3. **Commit Your Changes**
   ```bash
   git add .
   git commit -m "feat: add new feature description"
   ```

4. **Push to Your Fork**
   ```bash
   git push origin feature/your-feature-name
   ```

5. **Create Pull Request**
   - Go to the original repository
   - Click "New Pull Request"
   - Select your fork and branch
   - Fill out the PR template with:
     - Description of changes
     - Related issue numbers
     - Testing performed
     - Screenshots (if UI changes)

### PR Review Process
- Maintainers will review your PR within 3-5 days
- Address any requested changes
- Once approved, your PR will be merged

---

## Coding Standards

### Python Style Guide
- Follow [PEP 8](https://pep8.org/)
- Use type hints where appropriate
- Maximum line length: 100 characters
- Use meaningful variable and function names

### Code Example
```python
from typing import Optional, List

def process_action(
    action_type: str,
    target: Optional[str] = None,
    dry_run: bool = False
) -> ActionResult:
    """
    Process an action request.
    
    Args:
        action_type: Type of action to perform
        target: Optional target path or command
        dry_run: If True, only preview the action
        
    Returns:
        ActionResult with success status and message
    """
    # Implementation here
    pass
```

### Documentation
- Add docstrings to all public functions and classes
- Use Google-style docstrings
- Update README.md for user-facing changes
- Add inline comments for complex logic

### Security Principles
- **Never** compromise the privacy-first architecture
- All network operations must be opt-in
- Validate and sanitize all user inputs
- Use the Permission Manager for destructive operations
- Log all security-relevant actions

---

## Testing

### Writing Tests
- Add tests for all new features
- Maintain or improve code coverage
- Use descriptive test names
- Test both success and failure cases

### Test Structure
```python
def test_feature_name_success():
    """Test that feature works correctly."""
    # Arrange
    input_data = create_test_data()
    
    # Act
    result = feature_function(input_data)
    
    # Assert
    assert result.success
    assert result.data == expected_value
```

### Running Tests
```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_permission_manager.py -v

# Run with coverage
python -m pytest tests/ --cov=core --cov-report=html
```

---

## Module Development (Days 2-24)

If you're implementing one of the planned modules:

1. **Review the Plan**
   - Check `docs/plans/XX_module_name.md` for specifications
   - Understand the module's purpose and requirements

2. **Create Module Structure**
   ```
   modules/
   └── module_name/
       ├── __init__.py
       ├── core.py
       └── utils.py
   ```

3. **Implement with Security**
   - Use `PermissionManager` for all operations
   - Log actions with `AuditLogger`
   - Follow the dry-run pattern

4. **Add Tests**
   ```
   tests/
   └── test_module_name.py
   ```

5. **Update Documentation**
   - Update README.md
   - Add usage examples
   - Document configuration options

---

## Questions?

- Open a [Discussion](../../discussions) for general questions
- Create an [Issue](../../issues) for bugs or feature requests
- Check existing issues and discussions first

---

## Recognition

Contributors will be:
- Listed in the project's contributors page
- Mentioned in release notes for significant contributions
- Credited in the README.md

---

**Thank you for helping make Friday better! 🎉**
