"""
Check if all dependencies are installed correctly
"""

import sys
import importlib
import subprocess

def check_python_version():
    """Check Python version"""
    version = sys.version_info
    print(f"🐍 Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8+ required")
        return False
    else:
        print("✅ Python version OK")
        return True

def check_package(package_name, import_name=None):
    """Check if a Python package is installed"""
    if import_name is None:
        import_name = package_name
    
    try:
        importlib.import_module(import_name)
        print(f"✅ {package_name}")
        return True
    except ImportError:
        print(f"❌ {package_name} - run: pip install {package_name}")
        return False

def check_node():
    """Check if Node.js is installed"""
    try:
        result = subprocess.run(['node', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            version = result.stdout.strip()
            print(f"✅ Node.js {version}")
            return True
        else:
            print("❌ Node.js not found")
            return False
    except FileNotFoundError:
        print("❌ Node.js not installed")
        return False

def main():
    print("🔍 Dependency Check")
    print("==================")
    
    checks = []
    
    # Python version
    checks.append(check_python_version())
    
    # Python packages
    packages = [
        "fastapi",
        "uvicorn",
        "pydantic", 
        "requests",
        "python-dotenv",
        ("agno", "agno"),
        ("mcp", "mcp"),
    ]
    
    print("\n📦 Python packages:")
    for pkg in packages:
        if isinstance(pkg, tuple):
            checks.append(check_package(pkg[0], pkg[1]))
        else:
            checks.append(check_package(pkg))
    
    # Node.js
    print("\n🟢 Node.js:")
    checks.append(check_node())
    
    # Summary
    successful = sum(checks)
    total = len(checks)
    
    print(f"\n📋 Summary: {successful}/{total} checks passed")
    
    if successful == total:
        print("✨ All dependencies ready!")
        return True
    else:
        print("⚠️  Some dependencies missing. Install them before proceeding.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)