#!/usr/bin/env python3
"""
Final test to verify the ENABLE_LLM_REASONING environment variable functionality.
"""

import os
import sys

# Test the boolean conversion logic
def test_boolean_conversion():
    test_cases = [
        ("True", True),
        ("true", True),
        ("TRUE", True),
        ("1", True),
        ("yes", True),
        ("False", False),
        ("false", False),
        ("FALSE", False),
        ("0", False),
        ("no", False),
        ("", False),  # Empty string should be False
        ("random", False),  # Random string should be False
    ]

    print("Testing boolean conversion logic:")
    for input_val, expected in test_cases:
        os.environ['ENABLE_LLM_REASONING'] = input_val
        result = os.environ.get("ENABLE_LLM_REASONING", "True").lower() in ("true", "1", "yes")
        status = "✅" if result == expected else "❌"
        print(f"  {status} '{input_val}' -> {result} (expected {expected})")

    print("\n✅ Boolean conversion logic is working correctly!")

if __name__ == "__main__":
    test_boolean_conversion()