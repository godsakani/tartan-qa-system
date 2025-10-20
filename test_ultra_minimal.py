#!/usr/bin/env python3
"""
Test script for the ultra-minimal version
"""

def test_imports():
    """Test if all imports work"""
    try:
        from main_ultra_minimal import app
        print("✅ main_ultra_minimal imports successfully")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_dependencies():
    """Test if all required packages are available"""
    required_packages = [
        "fastapi",
        "pydantic", 
        "requests",
        "python-dotenv"
    ]
    
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
            print(f"✅ {package} available")
        except ImportError:
            print(f"❌ {package} missing")
            return False
    
    return True

if __name__ == "__main__":
    print("Testing Ultra-Minimal Version...")
    print("=" * 40)
    
    deps_ok = test_dependencies()
    imports_ok = test_imports()
    
    if deps_ok and imports_ok:
        print("\n🎉 Ultra-minimal version is ready!")
        print("Run: uvicorn main_ultra_minimal:app --reload")
    else:
        print("\n❌ Issues found. Check the errors above.")