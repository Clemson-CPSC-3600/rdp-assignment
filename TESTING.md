# Testing Guide for [Assignment Name]

## Important: Project Directory Structure

**Your working directory should be the project root folder** (not the `src/` directory). All commands assume you're running from the root:

```
project/                    ← You should be here
├── src/                    ← Your implementation files
│   └── [your_module.py]
├── tests/                  ← Test files
├── template/               ← Original starter files
└── run_tests.py           ← Test runner
```

**Tests automatically look for your code in the `src/` directory**, so you don't need to change directories or modify imports.

## Quick Start

### Run Tests with Grading Script
```bash
# From project root directory
# See your current grade
python run_tests.py

# See detailed results
python run_tests.py -v

# Test specific bundle
python run_tests.py --bundle 1
python run_tests.py --bundle 2
python run_tests.py --bundle 3
```

### Run Tests with pytest
```bash
# From project root directory
# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_[module].py -v

# Run tests matching a pattern
python -m pytest tests/ -k "[pattern]" -v
```

---

## VS Code Testing Integration

### Setting Up VS Code

1. **Install VS Code** and open the project folder
2. **Install recommended extensions** when prompted (or search for @recommended in Extensions)
3. **Select Python interpreter**: Press `Ctrl+Shift+P` → "Python: Select Interpreter" → Choose your venv

### Using the Test Explorer

#### Visual Test Runner
1. Click the **Testing** icon in the Activity Bar (flask icon on left sidebar)
2. All tests appear in a tree view organized by file and function
3. Click the ▶ button next to any test to run it
4. Results show immediately: ✅ = passed, ❌ = failed
5. Click on a failed test to jump to the failure location

#### Running Tests from VS Code

**Option 1: Test Explorer (Visual)**
- Click play buttons next to tests/folders in Testing sidebar
- Run individual tests, test files, or all tests
- See live results with colored indicators

**Option 2: Command Palette** (`Ctrl+Shift+P`)
- "Python: Run All Tests"
- "Python: Run Test Method"
- "Python: Debug Test Method"

**Option 3: Keyboard Shortcuts**
- `F5` - Debug current test
- `Ctrl+F5` - Run without debugging
- `Shift+F5` - Stop debugging

### Debugging Tests in VS Code

#### Setting Breakpoints
1. Click in the gutter (left of line numbers) to set a red breakpoint
2. Open a test file or your implementation
3. Set breakpoints where you want to investigate

#### Debug Configurations
Press `F5` or use Run and Debug sidebar:
- **Python: Current File** - Debug the open file
- **Python: Run Tests (All)** - Debug all tests
- **Python: Run Tests (Current File)** - Debug tests in current file
- **Python: Debug Tests (Current Test)** - Debug specific test

#### Debug Controls
- `F5` - Continue execution
- `F10` - Step over (execute current line)
- `F11` - Step into (enter function calls)
- `Shift+F11` - Step out (exit current function)
- `F9` - Toggle breakpoint

#### Debug Panel Features
- **Variables**: See all local and global variables
- **Watch**: Monitor specific expressions
- **Call Stack**: Trace execution path
- **Breakpoints**: Manage all breakpoints

### VS Code Productivity Tips

#### Essential Shortcuts
- `` Ctrl+` `` - Toggle terminal
- `Ctrl+Shift+P` - Command palette
- `Ctrl+P` - Quick file open
- `F12` - Go to definition
- `Shift+F12` - Find all references
- `F2` - Rename symbol

#### Test-Specific Features
- **Inline Test Results**: See pass/fail directly in code
- **Test Output**: View detailed output in OUTPUT panel
- **Problem Matcher**: Errors appear in PROBLEMS panel
- **CodeLens**: Run/debug buttons above each test

---

## Test Categories and Structure

### Bundle C: Core Functionality ([X] tests)

#### [Category 1: Basic Tests]
```bash
# Test [functionality 1]
python -m pytest tests/ -k "test_[pattern1]" -v

# Test [functionality 2]
python -m pytest tests/ -k "test_[pattern2]" -v
```

#### [Category 2: Essential Operations]
```bash
# Test [functionality 3]
python -m pytest tests/ -k "test_[pattern3]" -v

# Test [functionality 4]
python -m pytest tests/ -k "test_[pattern4]" -v
```

### Bundle B: Advanced Features ([Y] tests)

#### [Category 3: Error Handling]
```bash
# Test [error scenario 1]
python -m pytest tests/ -k "test_[error_pattern1]" -v

# Test [error scenario 2]
python -m pytest tests/ -k "test_[error_pattern2]" -v
```

#### [Category 4: Complex Operations]
```bash
# Test [complex feature 1]
python -m pytest tests/ -k "test_[complex_pattern1]" -v

# Test [complex feature 2]
python -m pytest tests/ -k "test_[complex_pattern2]" -v
```

### Bundle A: Production Quality ([Z] tests)

#### [Category 5: Performance]
```bash
# Test [performance aspect 1]
python -m pytest tests/ -k "test_[perf_pattern1]" -v

# Test [performance aspect 2]
python -m pytest tests/ -k "test_[perf_pattern2]" -v
```

#### [Category 6: Robustness]
```bash
# Test [robustness aspect 1]
python -m pytest tests/ -k "test_[robust_pattern1]" -v

# Test [robustness aspect 2]
python -m pytest tests/ -k "test_[robust_pattern2]" -v
```

---

## Manual Testing

### Starting Your Program
```bash
# [Instructions for running your program]
python [your_program.py] [arguments]
# Should output: [Expected initial output]
```

### Testing Commands
```bash
# [Example command 1]
python [your_program.py] [command1] [args]

# [Example command 2]
python [your_program.py] [command2] [args]

# [Example command 3]
python [your_program.py] [command3] [args]
```

### Interactive Testing with Python
```python
# Start Python REPL
python

>>> from [your_module] import *
>>> 
>>> # Test [functionality 1]
>>> result = your_function(args)
>>> print(result)
>>> 
>>> # Test [functionality 2]
>>> obj = YourClass()
>>> obj.method()
```

---

## Debugging Failed Tests

### Understanding Test Output

#### pytest Output Format
```
tests/test_[module].py::test_[function] FAILED

================================= FAILURES =================================
______________________________ test_[function] ______________________________

    def test_[function]():
        expected = [expected_value]
>       assert your_function() == expected
E       AssertionError: assert [actual] == [expected]
E         Expected: [expected_value]
E         Got: [actual_value]
```

#### Reading Error Messages
- **Test name**: Shows which test failed
- **Expected vs Got**: Shows what the test expected and what your code produced
- **Line number**: Click to jump to the failing assertion
- **Traceback**: Shows the call stack leading to the error

### Common Test Failures and Solutions

#### [Category 1] Tests Failing

**Issue**: "[Common error message 1]"
```python
# Problem: [Explanation of what's wrong]
# Example of incorrect code

# Solution: [How to fix it]
# Example of correct code
```

**Issue**: "[Common error message 2]"
```python
# Problem: [Explanation]
# Solution: [Fix]
```

#### [Category 2] Tests Failing

**Issue**: "[Common error message 3]"
```python
# Problem: [Explanation]
# Solution: [Fix]
```

### Debug Helpers

#### Add to Your Code for Debugging
```python
import logging
logging.basicConfig(level=logging.DEBUG)

def debug_value(label, value):
    """Print value in readable format."""
    logging.debug(f"{label}: {value}")
    logging.debug(f"  Type: {type(value)}")
    logging.debug(f"  Length: {len(value) if hasattr(value, '__len__') else 'N/A'}")

def debug_function_call(func_name, args, kwargs):
    """Log function calls for debugging."""
    logging.debug(f"Calling {func_name}")
    logging.debug(f"  Args: {args}")
    logging.debug(f"  Kwargs: {kwargs}")

# Example usage in your code:
def your_function(arg1, arg2):
    debug_function_call("your_function", (arg1, arg2), {})
    # Your implementation here
    result = process(arg1, arg2)
    debug_value("Result", result)
    return result
```

---

## Test Coverage

### Running with Coverage
```bash
# Generate coverage report
python -m pytest tests/ --cov=src --cov-report=term-missing

# Generate HTML coverage report
python -m pytest tests/ --cov=src --cov-report=html
# Open htmlcov/index.html in browser
```

### Understanding Coverage Output
```
Name                 Stmts   Miss  Cover   Missing
----------------------------------------------------
src/module1.py          50      5    90%   45-50
src/module2.py          75     10    87%   120-125, 200-205
src/module3.py          30      2    93%   55-56
----------------------------------------------------
TOTAL                  155     17    89%
```

- **Stmts**: Total statements in file
- **Miss**: Statements not executed by tests
- **Cover**: Percentage of code covered
- **Missing**: Line numbers not covered

### Improving Coverage
1. Look at "Missing" line numbers
2. Write tests that exercise those code paths
3. Focus on error handling and edge cases
4. Aim for >90% coverage for production code

---

## Performance Testing

### Running Performance Tests
```bash
# Show slowest tests
python -m pytest tests/ --durations=10

# Run with timeout
python -m pytest tests/ --timeout=60

# Profile specific functionality
python -m cProfile -s cumtime [your_program.py] [args]
```

### Stress Testing
```python
# Test with large inputs
# [Example of stress test for your assignment]

# Test rapid operations
# [Example of rapid operation test]
```

---

## Continuous Testing

### Watch Mode (Auto-run on File Changes)
```bash
# Install pytest-watch
pip install pytest-watch

# Run tests automatically on file save
ptw tests/ -- -v
```

### Git Pre-commit Hook
```bash
# Create .git/hooks/pre-commit
#!/bin/bash
python -m pytest tests/ -q
if [ $? -ne 0 ]; then
    echo "Tests failed. Commit aborted."
    exit 1
fi
```

---

## Test Organization Best Practices

### Writing Your Own Tests
```python
# tests/test_my_features.py
import pytest
from src.[your_module] import *

class TestMyFeatures:
    """Group related tests together."""
    
    def test_feature_one(self):
        """Test names should be descriptive."""
        # Arrange
        input_data = "test"
        
        # Act
        result = my_function(input_data)
        
        # Assert
        assert result == expected_value
    
    @pytest.mark.skip(reason="Not implemented yet")
    def test_future_feature(self):
        """Mark tests to skip temporarily."""
        pass
    
    @pytest.mark.parametrize("input,expected", [
        ("input1", "output1"),
        ("input2", "output2"),
    ])
    def test_multiple_cases(self, input, expected):
        """Test multiple inputs with one test."""
        assert process(input) == expected
```

### Test Fixtures
```python
@pytest.fixture
def test_data():
    """Create test data for reuse."""
    return {
        "key1": "value1",
        "key2": "value2"
    }

def test_with_fixture(test_data):
    """Use the fixture in a test."""
    result = process_data(test_data)
    assert result["status"] == "success"
```

---

## Troubleshooting

### VS Code Issues

**Tests not showing in Test Explorer?**
1. Select correct Python interpreter: `Ctrl+Shift+P` → "Python: Select Interpreter"
2. Refresh tests: `Ctrl+Shift+P` → "Python: Refresh Tests"
3. Check test discovery settings in `.vscode/settings.json`

**Debugging not working?**
1. Ensure virtual environment is activated
2. Check that pytest is installed: `pip install pytest`
3. Verify launch.json configuration exists

### Common Test Issues

**Import errors?**
```bash
# Add project root to Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

**Tests hanging?**
- Add timeout to tests: `@pytest.mark.timeout(30)`
- Check for infinite loops in your code
- Verify proper resource cleanup

---

## Summary

### Quick Reference

| Task | Command |
|------|---------|
| Check grade | `python run_tests.py` |
| Run all tests | `python -m pytest tests/ -v` |
| Run specific bundle | `python run_tests.py --bundle 1` |
| Debug in VS Code | Set breakpoint → `F5` |
| Test coverage | `python -m pytest tests/ --cov=src` |
| Run one test | `python -m pytest tests/ -k "test_name"` |

### Testing Workflow

1. **Write code** for one feature
2. **Run relevant tests** to check progress
3. **Debug failures** using VS Code debugger
4. **Check coverage** to find untested code
5. **Run full suite** before committing
6. **Check grade** with `run_tests.py`

Remember: Good tests help you write better code. Use them as a guide, not just a grade check!

---

## Instructor Notes (Remove Before Distribution)

When customizing this template:
1. Replace all bracketed placeholders with assignment-specific content
2. Update test patterns to match your test naming conventions
3. Add specific debugging examples from your assignment
4. Include relevant manual testing commands
5. Update module and function names throughout
6. Add assignment-specific troubleshooting tips
7. Include examples of common error messages students will encounter
8. Remove this section before distributing to students
