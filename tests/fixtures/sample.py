# This is a sample Python file
# with multiple comments that should be translated.

def add(a: int, b: int) -> int:
    """Add two numbers together and return the result."""
    return a + b

# This function calculates the factorial
def factorial(n: int) -> int:
    """Compute the factorial of a non-negative integer."""
    if n <= 1:
        return 1
    return n * factorial(n - 1)
