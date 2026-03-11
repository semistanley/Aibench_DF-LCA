"""Check if all required dependencies and files are installed/present."""
import sys
from pathlib import Path

REQUIRED_PACKAGES = [
    "streamlit",
    "fastapi",
    "uvicorn",
    "sqlalchemy",
    "pandas",
    "matplotlib",
    "prometheus_client",
    "docker",
    "yaml",
    "plotly",
    "datasets",
    "pydantic",
    "click",
    "psutil",
    "jose",
]

REQUIRED_FILES = [
    "app.py",
    "api.py",
    "evaluator.py",
    "config.yaml",
    "requirements.txt",
    "README.md",
]

REQUIRED_DIRS = [
    "api",
    "core",
    "adapters",
    "tasks",
    "cli",
    "utils",
]


def check_packages():
    """Check if all required packages are installed."""
    print("Checking required packages...")
    missing = []
    for package in REQUIRED_PACKAGES:
        try:
            if package == "jose":
                __import__("jose")
            elif package == "yaml":
                __import__("yaml")
            else:
                __import__(package)
            print(f"  [OK] {package}")
        except ImportError:
            print(f"  [MISSING] {package}")
            missing.append(package)

    if missing:
        print(f"\n[WARNING] Missing packages: {', '.join(missing)}")
        print("Install with: pip install -r requirements.txt")
        return False
    else:
        print("\n[SUCCESS] All required packages are installed!")
        return True


def check_files():
    """Check if all required files exist."""
    print("\nChecking required files...")
    project_root = Path(__file__).parent
    missing = []
    for file in REQUIRED_FILES:
        path = project_root / file
        if path.exists():
            print(f"  [OK] {file}")
        else:
            print(f"  [MISSING] {file}")
            missing.append(file)

    if missing:
        print(f"\n[WARNING] Missing files: {', '.join(missing)}")
        return False
    else:
        print("\n[SUCCESS] All required files are present!")
        return True


def check_directories():
    """Check if all required directories exist."""
    print("\nChecking required directories...")
    project_root = Path(__file__).parent
    missing = []
    for dir_name in REQUIRED_DIRS:
        path = project_root / dir_name
        if path.exists() and path.is_dir():
            print(f"  [OK] {dir_name}/")
        else:
            print(f"  [MISSING] {dir_name}/")
            missing.append(dir_name)

    if missing:
        print(f"\n[WARNING] Missing directories: {', '.join(missing)}")
        return False
    else:
        print("\n[SUCCESS] All required directories are present!")
        return True


def main():
    """Run all checks."""
    print("=" * 60)
    print("DF-LCA Benchmark Platform - Setup Verification")
    print("=" * 60)

    packages_ok = check_packages()
    files_ok = check_files()
    dirs_ok = check_directories()

    print("\n" + "=" * 60)
    if packages_ok and files_ok and dirs_ok:
        print("[SUCCESS] Setup is complete! All requirements are met.")
        return 0
    else:
        print("[WARNING] Setup is incomplete. Please install missing dependencies/files.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
