"""
Test url_exists() method
"""

import os
import sys
from dotenv import load_dotenv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from adapters.vector.vector_manager import get_vector_adapter

load_dotenv()

vectorizer = get_vector_adapter()

# Test with a known URL
test_url = "https://support.yotpo.com/docs/loyalty-emails-setup-guide-for-klaviyo"
test_esp = "klaviyo"

print("="*80)
print("TESTING url_exists()")
print("="*80)
print(f"\nURL: {test_url}")
print(f"ESP: {test_esp}\n")

result = vectorizer.url_exists(test_url, test_esp)

print(f"\n{'✅' if result else '❌'} Result: {result}")

if not result:
    print("\n⚠️  This is why admin panel shows 'UNDEFINED'!")
    print("   The url_exists() method is not working correctly.")

print("\n" + "="*80)
