#!/usr/bin/env python3
"""
MCP Server Installer

Quick install:
    curl -sSL https://raw.githubusercontent.com/OxSci-AI/oxsci-mcp-scaffold/main/install.py | python3 -

This script:
1. Downloads the MCP scaffold template from GitHub
2. Prompts for service name and tool name
3. Creates a new MCP server project
4. Initializes git repository

Dependencies:
    - Python 3.11+ (only uses Python standard library, no external packages)
    - Git (required for repository initialization)
    - Network connectivity to GitHub (required for downloading template)
    - AWS CLI (checked but not required - needed later for CodeArtifact access)
"""

import argparse
import os
import platform
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path
from typing import Optional, Tuple


GITHUB_REPO = "OxSci-AI/oxsci-mcp-scaffold"
GITHUB_BRANCH = "main"
GITHUB_ZIP_URL = (
    f"https://github.com/{GITHUB_REPO}/archive/refs/heads/{GITHUB_BRANCH}.zip"
)


def detect_platform() -> str:
    """Detect the operating system platform."""
    system = platform.system().lower()
    if system == "linux":
        # Try to detect Linux distribution
        try:
            with open("/etc/os-release", "r") as f:
                content = f.read().lower()
                if "ubuntu" in content:
                    return "ubuntu"
                elif "debian" in content:
                    return "debian"
                elif "centos" in content or "rhel" in content:
                    return "centos"
                elif "arch" in content:
                    return "arch"
                else:
                    return "linux"
        except (OSError, IOError):
            return "linux"
    elif system == "darwin":
        return "macos"
    elif system == "windows":
        return "windows"
    else:
        return "unknown"


def check_python_version() -> Tuple[bool, Optional[str]]:
    """Check if Python 3.11+ is installed."""
    try:
        version = sys.version_info
        if version.major >= 3 and version.minor >= 11:
            return True, f"{version.major}.{version.minor}.{version.micro}"
        else:
            return False, f"{version.major}.{version.minor}.{version.micro}"
    except Exception:
        return False, None


def check_git() -> Tuple[bool, Optional[str]]:
    """Check if Git is installed."""
    try:
        result = subprocess.run(
            ["git", "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            version = result.stdout.strip().split()[2]
            return True, version
        return False, None
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False, None
    except Exception:
        return False, None


def check_network_connectivity() -> bool:
    """Check if network connectivity is available."""
    try:
        # Try to connect to GitHub
        socket.create_connection(("github.com", 443), timeout=5)
        return True
    except (OSError, socket.timeout):
        return False


def check_aws_cli() -> Tuple[bool, Optional[str]]:
    """Check if AWS CLI is installed."""
    try:
        result = subprocess.run(
            ["aws", "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            # AWS CLI output format: "aws-cli/2.x.x Python/3.x.x ..."
            version_line = result.stdout.strip().split("\n")[0]
            # Extract version part (e.g., "aws-cli/2.x.x")
            version = version_line.split()[0] if version_line else "installed"
            return True, version
        return False, None
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False, None
    except Exception:
        return False, None


def check_environment() -> bool:
    """Check all required environment prerequisites."""
    print("=" * 70)
    print("Environment Check")
    print("=" * 70)
    print()

    # Detect platform
    detected_platform = detect_platform()
    print(f"  Platform: {detected_platform}")
    if detected_platform == "unknown":
        print("  ⚠️  Warning: Unknown platform detected")
    print()

    # Check Python version
    python_ok, python_version = check_python_version()
    if python_ok:
        print(f"  ✅ Python: {python_version} (required: 3.11+)")
    else:
        print(f"  ❌ Python: {python_version if python_version else 'Not found'}")
        print("     Required: Python 3.11 or higher")
        print()
        print("     Installation instructions:")
        if detected_platform == "ubuntu":
            print(
                "       sudo apt-get update && sudo apt-get install -y python3.11 python3.11-venv"
            )
        elif detected_platform == "macos":
            print("       brew install python@3.11")
        elif detected_platform == "windows":
            print("       Download from: https://www.python.org/downloads/")
        else:
            print("       Please install Python 3.11+ for your platform")
        return False
    print()

    # Check Git
    git_ok, git_version = check_git()
    if git_ok:
        print(f"  ✅ Git: {git_version}")
    else:
        print("  ❌ Git: Not found")
        print("     Git is required for repository initialization")
        print()
        print("     Installation instructions:")
        if detected_platform == "ubuntu":
            print("       sudo apt-get update && sudo apt-get install -y git")
        elif detected_platform == "macos":
            print("       brew install git")
        elif detected_platform == "windows":
            print("       Download from: https://git-scm.com/download/win")
        else:
            print("       Please install Git for your platform")
        return False
    print()

    # Check network connectivity
    network_ok = check_network_connectivity()
    if network_ok:
        print("  ✅ Network: Connected")
    else:
        print("  ❌ Network: No connection to GitHub")
        print("     Please check your internet connection")
        return False
    print()

    # Check write permissions for current directory
    try:
        test_file = Path.cwd() / ".install_test"
        test_file.touch()
        test_file.unlink()
        print("  ✅ Write permissions: OK")
    except (OSError, IOError):
        print("  ❌ Write permissions: Cannot write to current directory")
        print(f"     Current directory: {Path.cwd()}")
        print(
            "     Please run the script from a directory where you have write permissions"
        )
        return False
    print()

    # Check AWS CLI (warning only, not required for installation)
    aws_ok, aws_version = check_aws_cli()
    if aws_ok:
        print(f"  ✅ AWS CLI: {aws_version}")
        print(
            "     Note: AWS CLI is required for CodeArtifact access after installation"
        )
    else:
        print("  ⚠️  AWS CLI: Not found")
        print("     Warning: AWS CLI is required for CodeArtifact access")
        print("     You can install it later to configure dependency access")
        print()
        print("     Installation instructions:")
        if detected_platform == "ubuntu":
            print("       sudo apt-get update && sudo apt-get install -y awscli")
        elif detected_platform == "macos":
            print("       brew install awscli")
        elif detected_platform == "windows":
            print("       Download from: https://aws.amazon.com/cli/")
        else:
            print("       Please install AWS CLI for your platform")
    print()

    print("=" * 70)
    print("✅ All environment checks passed!")
    print("=" * 70)
    print()

    return True


def is_interactive() -> bool:
    """Check if stdin is available for interactive input."""
    return sys.stdin.isatty()


def get_input(prompt: str, validator=None) -> str:
    """Get user input with optional validation."""
    if not is_interactive():
        raise EOFError(
            "Cannot read input from stdin. Please use command-line arguments:\n"
            "  python3 install.py --service-name <name> --tool-name <name>\n"
            "Or download the script first and run it interactively:\n"
            "  curl -sSL https://raw.githubusercontent.com/OxSci-AI/oxsci-mcp-scaffold/main/install.py > install.py\n"
            "  python3 install.py"
        )
    while True:
        value = input(prompt).strip()
        if not value:
            print("  Error: Input cannot be empty. Please try again.")
            continue
        if validator and not validator(value):
            continue
        return value


def normalize_service_name(name: str) -> str:
    """Normalize service name: lowercase, convert spaces/special chars to hyphens."""
    # Convert to lowercase
    normalized = name.lower().strip()
    # Replace spaces and other non-alphanumeric characters (except hyphens) with hyphens
    normalized = re.sub(r"[^a-z0-9-]+", "-", normalized)
    # Remove leading/trailing hyphens and multiple consecutive hyphens
    normalized = re.sub(r"-+", "-", normalized).strip("-")
    # Ensure it starts with a letter
    if normalized and not normalized[0].isalpha():
        # Find first letter and take from there
        match = re.search(r"[a-z]", normalized)
        if match:
            normalized = normalized[match.start() :]
        else:
            normalized = "service-" + normalized
    return normalized or "service"


def normalize_tool_name(name: str) -> str:
    """Normalize tool name: lowercase, convert spaces/hyphens/special chars to underscores."""
    # Convert to lowercase
    normalized = name.lower().strip()
    # Replace spaces, hyphens, and other non-alphanumeric characters with underscores
    normalized = re.sub(r"[^a-z0-9_]+", "_", normalized)
    # Remove leading/trailing underscores and multiple consecutive underscores
    normalized = re.sub(r"_+", "_", normalized).strip("_")
    # Ensure it starts with a letter
    if normalized and not normalized[0].isalpha():
        # Find first letter and take from there
        match = re.search(r"[a-z]", normalized)
        if match:
            normalized = normalized[match.start() :]
        else:
            normalized = "tool_" + normalized
    return normalized or "tool"


def validate_service_name(name: str) -> bool:
    """Validate service name format (after normalization)."""
    if not name or not re.match(r"^[a-z][a-z0-9-]*$", name):
        print(
            "  Error: Service name must start with a letter and contain only lowercase letters, numbers, and hyphens."
        )
        return False
    return True


def validate_tool_name(name: str) -> bool:
    """Validate tool name format (after normalization)."""
    if not name or not re.match(r"^[a-z][a-z0-9_]*$", name):
        print(
            "  Error: Tool name must start with a letter and contain only lowercase letters, numbers, and underscores."
        )
        return False
    return True


def to_pascal_case(name: str) -> str:
    """Convert snake_case or kebab-case to PascalCase."""
    parts = re.split(r"[_-]", name)
    return "".join(word.capitalize() for word in parts)


def download_and_extract_scaffold(temp_dir: Path) -> Path:
    """Download and extract scaffold from GitHub."""
    print("Downloading scaffold from GitHub...")

    zip_path = temp_dir / "scaffold.zip"

    try:
        # Download zip file
        with urllib.request.urlopen(GITHUB_ZIP_URL) as response:
            with open(zip_path, "wb") as out_file:
                out_file.write(response.read())

        print("Extracting files...")

        # Extract zip file
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(temp_dir)

        # Find extracted directory (should be oxsci-mcp-scaffold-main or similar)
        extracted_dirs = [
            d
            for d in temp_dir.iterdir()
            if d.is_dir() and d.name.startswith("oxsci-mcp-scaffold")
        ]

        if not extracted_dirs:
            raise Exception("Could not find extracted scaffold directory")

        return extracted_dirs[0]

    except Exception as e:
        print(f"❌ Failed to download scaffold: {e}")
        print("\nAlternative installation method:")
        print("1. Clone the repository:")
        print(f"   git clone https://github.com/{GITHUB_REPO}.git")
        print("2. Run setup.py:")
        print("   cd oxsci-mcp-scaffold && python setup.py")
        sys.exit(1)


def setup_service(
    service_name: Optional[str] = None,
    tool_name: Optional[str] = None,
    skip_confirm: bool = False,
    skip_env_check: bool = False,
):
    """Main setup function.

    Note: This script should be run from the parent directory where you want to create
    the service. For example, if you want to create the service at /git/mcp-service-name/,
    run this script from /git/ directory. The script will create mcp-{service-name}/
    in the current working directory.
    """
    print("=" * 70)
    print("MCP Server Installer")
    print("=" * 70)
    print()

    # Show current directory for clarity
    current_dir = Path.cwd()
    print(f"Current directory: {current_dir}")
    print("Note: The service will be created in a subdirectory of this location.")
    print()

    # Perform environment checks (unless skipped)
    if not skip_env_check:
        if not check_environment():
            print(
                "\n❌ Environment check failed. Please fix the issues above and try again."
            )
            print(
                "   You can skip this check with --skip-env-check flag (not recommended)"
            )
            sys.exit(1)

    # Get service name
    print("Step 1: Service Configuration")
    print("-" * 70)
    if service_name is None:
        raw_service_name = get_input(
            "Enter service name (e.g., 'document-processor'): "
        )
        service_name = normalize_service_name(raw_service_name)
        if not validate_service_name(service_name):
            sys.exit(1)
        if raw_service_name != service_name:
            print(f"  → Normalized to: {service_name}")
    else:
        original_service_name = service_name
        service_name = normalize_service_name(service_name)
        if not validate_service_name(service_name):
            sys.exit(1)
        if original_service_name != service_name:
            print(
                f"Service name: {original_service_name} → normalized to: {service_name}"
            )
        else:
            print(f"Service name: {service_name}")

    folder_name = f"mcp-{service_name}"
    description = f"MCP {service_name.replace('-', ' ').title()} Server"

    print(f"\n  → Service folder: {folder_name}")
    print(f"  → Description: {description}")
    print()

    # Get tool name
    print("Step 2: Tool Configuration")
    print("-" * 70)
    if tool_name is None:
        raw_tool_name = get_input("Enter tool name (e.g., 'document_processor'): ")
        tool_name = normalize_tool_name(raw_tool_name)
        if not validate_tool_name(tool_name):
            sys.exit(1)
        if raw_tool_name != tool_name:
            print(f"  → Normalized to: {tool_name}")
    else:
        original_tool_name = tool_name
        tool_name = normalize_tool_name(tool_name)
        if not validate_tool_name(tool_name):
            sys.exit(1)
        if original_tool_name != tool_name:
            print(f"Tool name: {original_tool_name} → normalized to: {tool_name}")
        else:
            print(f"Tool name: {tool_name}")

    tool_file = f"{tool_name}.py"

    print(f"\n  → Tool file: app/tools/{tool_file}")
    print()

    # Confirm setup
    if not skip_confirm:
        print("Step 3: Confirmation")
        print("-" * 70)
        print(f"Service Name:  {folder_name}")
        print(f"Description:   {description}")
        print(f"Tool Name:     {tool_name}")
        print()

        if is_interactive():
            confirm = input("Proceed with setup? (y/n): ").strip().lower()
            if confirm != "y":
                print("\nSetup cancelled.")
                return
        else:
            print("Note: Non-interactive mode detected. Proceeding with setup...")
            print()

    print()
    print("Step 4: Creating Project")
    print("-" * 70)

    target_dir = Path.cwd() / folder_name

    # Check if target directory already exists
    if target_dir.exists():
        print(f"\n❌ Error: Directory '{folder_name}' already exists!")
        return

    # Create temporary directory for download
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        try:
            # Download scaffold
            scaffold_dir = download_and_extract_scaffold(temp_path)

            # Create target directory
            print(f"Creating directory: {folder_name}")
            target_dir.mkdir(parents=True, exist_ok=True)

            # Copy all files and directories except setup.py, install.py, and tool_template.py
            print("Copying template files...")
            for item in scaffold_dir.iterdir():
                if item.name in [
                    "setup.py",
                    "install.py",
                    ".git",
                    "__pycache__",
                    ".DS_Store",
                    "README.md",
                ]:
                    continue

                dest = target_dir / item.name
                if item.is_file():
                    shutil.copy2(item, dest)
                elif item.is_dir():
                    shutil.copytree(item, dest)

            # Update pyproject.toml
            print("Configuring pyproject.toml...")
            pyproject_path = target_dir / "pyproject.toml"
            content = pyproject_path.read_text()
            content = content.replace(
                'name = "mcp-server-template"', f'name = "{folder_name}"'
            )
            content = content.replace(
                'description = "MCP Server Template built with oxsci-oma-mcp"',
                f'description = "{description}"',
            )
            pyproject_path.write_text(content)

            # Create tool file from template
            print(f"Creating tool file: app/tools/{tool_file}")
            tool_template_path = target_dir / "app" / "tools" / "tool_template.py"
            tool_path = target_dir / "app" / "tools" / tool_file

            # Check if template exists, otherwise use example_tool.py as template
            if not tool_template_path.exists():
                tool_template_path = target_dir / "app" / "tools" / "example_tool.py"

            tool_content = tool_template_path.read_text()
            # Replace template placeholders
            tool_content = tool_content.replace("example_tool", tool_name)
            tool_content = tool_content.replace("ExampleTool", to_pascal_case(tool_name))
            tool_content = tool_content.replace(
                "Example tool that processes text input",
                f"{to_pascal_case(tool_name)} tool",
            )

            tool_path.write_text(tool_content)

            # Remove template file if it exists
            if tool_template_path.name == "tool_template.py":
                tool_template_path.unlink()
            # Remove example_tool.py if we created a different tool
            elif tool_name != "example_tool":
                example_tool = target_dir / "app" / "tools" / "example_tool.py"
                if example_tool.exists():
                    example_tool.unlink()

            # Update __init__.py for tools
            tools_init = target_dir / "app" / "tools" / "__init__.py"
            init_content = f'''"""
MCP Tools Package

Import all your tool modules here to ensure they are registered with @oma_tool.
"""

# Import your tools here
from . import {tool_name}  # noqa: F401
'''
            tools_init.write_text(init_content)

            # Update config.py with service name
            print("Updating config.py...")
            config_path = target_dir / "app" / "core" / "config.py"
            config_content = config_path.read_text()
            # This will use the SERVICE_NAME from BaseConfig, but we should update comments if any
            config_path.write_text(config_content)

            # Create README.md
            readme_content = f"""# {folder_name}

{description}

## Quick Start

### 1. Configure AWS CodeArtifact

```bash
./entrypoint-dev.sh
```

### 2. Install Dependencies

```bash
poetry install
```

### 3. Run Server

```bash
poetry run uvicorn app.core.main:app --reload --port 8060
```

### 4. Test the Tool

```bash
# Discover tools
curl http://localhost:8060/tools/discover

# Execute your tool
curl -X POST http://localhost:8060/tools/{tool_name} \\
  -H "Content-Type: application/json" \\
  -d '{{"arguments": {{}}, "context": {{}}}}'
```

## Documentation

For detailed documentation, see: https://github.com/{GITHUB_REPO}
"""
            readme_path = target_dir / "README.md"
            readme_path.write_text(readme_content)

            # Initialize git repository
            print("Initializing git repository...")
            os.chdir(target_dir)
            os.system("git init")
            os.system("git add .")
            os.system(
                f'git commit -m "Initial commit: {folder_name} from oxsci-mcp-scaffold"'
            )

            print()
            print("=" * 70)
            print("✅ Setup Complete!")
            print("=" * 70)
            print()
            print(f"Your MCP server has been created in: {folder_name}")
            print()
            print("Next steps:")
            print()
            print(f"  1. cd {folder_name}")
            print(f"  2. ./entrypoint-dev.sh          # Configure AWS CodeArtifact")
            print(f"  3. poetry install                # Install dependencies")
            print(f"  4. Edit app/tools/{tool_file}    # Implement your tool logic")
            print(
                f"  5. poetry run uvicorn app.core.main:app --reload --port 8060  # Start server"
            )
            print()
            print(f"For more information, see: https://github.com/{GITHUB_REPO}")
            print()

        except Exception as e:
            print(f"\n❌ Error during setup: {e}")
            import traceback

            traceback.print_exc()
            if target_dir.exists():
                print(f"\nCleaning up {folder_name}...")
                shutil.rmtree(target_dir)
            return


def main():
    """Main entry point with argument parsing."""
    parser = argparse.ArgumentParser(
        description="MCP Server Installer - Creates a new MCP server in the current directory",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode (download and run separately):
  cd /git
  curl -sSL https://raw.githubusercontent.com/OxSci-AI/oxsci-mcp-scaffold/main/install.py > install.py
  python3 install.py

  # Non-interactive mode with arguments:
  cd /git
  curl -sSL https://raw.githubusercontent.com/OxSci-AI/oxsci-mcp-scaffold/main/install.py | python3 - --service-name document-processor --tool-name document_processor --yes

  # Non-interactive mode with auto-confirm:
  cd /git
  python3 install.py --service-name my-service --tool-name my_tool --yes

Note:
  - Run this script from the parent directory where you want to create the service
  - Example: To create /git/mcp-my-service/, run the script from /git/ directory
  - The script will create mcp-{service-name}/ in the current working directory
        """,
    )
    parser.add_argument(
        "--service-name",
        type=str,
        help="Service name (e.g., 'document-processor'). Must start with a letter and contain only lowercase letters, numbers, and hyphens.",
    )
    parser.add_argument(
        "--tool-name",
        type=str,
        help="Tool name (e.g., 'document_processor'). Must start with a letter and contain only lowercase letters, numbers, and underscores.",
    )
    parser.add_argument(
        "--yes",
        "-y",
        action="store_true",
        help="Skip confirmation prompt (useful for non-interactive mode)",
    )
    parser.add_argument(
        "--skip-env-check",
        action="store_true",
        help="Skip environment prerequisites check (not recommended)",
    )

    args = parser.parse_args()

    # If stdin is not a TTY and no arguments provided, show error
    if not is_interactive() and (args.service_name is None or args.tool_name is None):
        parser.error(
            "Cannot read input from stdin. Please provide --service-name and --tool-name arguments.\n"
            "Example: python3 install.py --service-name document-processor --tool-name document_processor\n"
            "Or download the script first and run it interactively:\n"
            "  curl -sSL https://raw.githubusercontent.com/OxSci-AI/oxsci-mcp-scaffold/main/install.py > install.py\n"
            "  python3 install.py"
        )

    try:
        setup_service(
            service_name=args.service_name,
            tool_name=args.tool_name,
            skip_confirm=args.yes,
            skip_env_check=args.skip_env_check,
        )
    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user.")
        sys.exit(1)
    except EOFError as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
