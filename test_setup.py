#!/usr/bin/env python3
"""Quick test to verify setup is complete"""

import os
import sys

def test_setup():
    print("ESP Loyalty Helper - Setup Verification")
    print("=" * 50)

    checks = []

    # Check directories
    checks.append(("Backend directory", os.path.exists("backend")))
    checks.append(("Frontend directory", os.path.exists("frontend")))
    checks.append(("Docs directory", os.path.exists("docs")))
    checks.append(("Klaviyo docs", os.path.exists("docs/klaviyo")))
    checks.append(("DotDigital docs", os.path.exists("docs/dotdigital")))

    # Check files
    checks.append(("Backend app.py", os.path.exists("backend/app.py")))
    checks.append(("Crawler script", os.path.exists("backend/crawler.py")))
    checks.append(("Vectorizer script", os.path.exists("backend/vectorize.py")))
    checks.append(("Frontend index.html", os.path.exists("frontend/index.html")))
    checks.append(("Frontend styles.css", os.path.exists("frontend/styles.css")))
    checks.append(("Frontend app.js", os.path.exists("frontend/app.js")))

    # Check vector database
    checks.append(("Vector database", os.path.exists("backend/chroma_db")))

    # Count documents
    klaviyo_docs = len([f for f in os.listdir("docs/klaviyo") if f.endswith(".txt")]) if os.path.exists("docs/klaviyo") else 0
    dotdigital_docs = len([f for f in os.listdir("docs/dotdigital") if f.endswith(".txt")]) if os.path.exists("docs/dotdigital") else 0

    print("\nSetup Checks:")
    for name, result in checks:
        status = "✓" if result else "✗"
        print(f"  {status} {name}")

    print(f"\nDocumentation:")
    print(f"  Klaviyo: {klaviyo_docs} documents")
    print(f"  DotDigital: {dotdigital_docs} documents")

    # Check Python packages
    print("\nPython Packages:")
    packages = ["flask", "flask_cors", "chromadb", "bs4", "pypdf"]
    for pkg in packages:
        try:
            __import__(pkg)
            print(f"  ✓ {pkg}")
        except ImportError:
            print(f"  ✗ {pkg} (NOT INSTALLED)")

    # Check Gemini package separately
    try:
        import google.generativeai
        print(f"  ✓ google-generativeai")
    except ImportError:
        print(f"  ✗ google-generativeai (NOT INSTALLED)")

    # Check API key
    api_key = os.environ.get("GEMINI_API_KEY")
    if api_key and api_key != "your-key-placeholder":
        print(f"\n  ✓ GEMINI_API_KEY is set")
    else:
        print(f"\n  ⚠️  GEMINI_API_KEY not set (chat won't work)")

    print("\n" + "=" * 50)

    all_passed = all(result for _, result in checks)
    if all_passed and klaviyo_docs > 0 and dotdigital_docs > 0:
        print("✓ Setup complete! Ready to run.")
        print("\nTo start the app:")
        print("  1. Set your API key: export GEMINI_API_KEY='your-key'")
        print("  2. Get free key at: https://makersuite.google.com/app/apikey")
        print("  3. Run: ./start.sh")
        print("  4. Open: http://localhost:8000")
        return 0
    else:
        print("✗ Setup incomplete. Please check the errors above.")
        return 1

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    sys.exit(test_setup())
