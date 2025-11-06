#!/usr/bin/env python3
"""
MCP Server Setup Script

This script sets up a new MCP server by:
1. Prompting for service name and tool name
2. Creating the project directory structure
3. Configuring pyproject.toml with the service name
4. Creating tool file from template
5. Updating __init__.py to import the tool
6. Initializing git repository
"""

import os
import re
import shutil
import sys
from pathlib import Path


def get_input(prompt: str, validator=None) -> str:
    """Get user input with optional validation."""
    while True:
        value = input(prompt).strip()
        if not value:
            print("  Error: Input cannot be empty. Please try again.")
            continue
        if validator and not validator(value):
            continue
        return value


def validate_service_name(name: str) -> bool:
    """Validate service name format."""
    # Allow alphanumeric and hyphens, must start with letter
    if not re.match(r"^[a-z][a-z0-9-]*$", name):
        print(
            "  Error: Service name must start with a letter and contain only lowercase letters, numbers, and hyphens."
        )
        return False
    return True


def validate_tool_name(name: str) -> bool:
    """Validate tool name format."""
    # Allow alphanumeric and underscores, must start with letter
    if not re.match(r"^[a-z][a-z0-9_]*$", name):
        print(
            "  Error: Tool name must start with a letter and contain only lowercase letters, numbers, and underscores."
        )
        return False
    return True


def to_pascal_case(name: str) -> str:
    """Convert snake_case or kebab-case to PascalCase."""
    parts = re.split(r"[_-]", name)
    return "".join(word.capitalize() for word in parts)


def setup_service():
    """Main setup function."""
    print("=" * 70)
    print("MCP Server Setup")
    print("=" * 70)
    print()

    # Get service name
    print("Step 1: Service Configuration")
    print("-" * 70)
    service_name = get_input(
        "Enter service name (e.g., 'document-processor'): ", validate_service_name
    )
    folder_name = f"mcp-{service_name}"
    description = f"MCP {service_name.replace('-', ' ').title()} Server"

    print(f"\n  → Service folder: {folder_name}")
    print(f"  → Description: {description}")
    print()

    # Get tool name
    print("Step 2: Tool Configuration")
    print("-" * 70)
    tool_name = get_input(
        "Enter tool name (e.g., 'document_processor'): ", validate_tool_name
    )
    tool_file = f"{tool_name}.py"

    print(f"\n  → Tool file: app/tools/{tool_file}")
    print()

    # Confirm setup
    print("Step 3: Confirmation")
    print("-" * 70)
    print(f"Service Name:  {folder_name}")
    print(f"Description:   {description}")
    print(f"Tool Name:     {tool_name}")
    print()

    confirm = input("Proceed with setup? (y/n): ").strip().lower()
    if confirm != "y":
        print("\nSetup cancelled.")
        return

    print()
    print("Step 4: Creating Project")
    print("-" * 70)

    # Get script directory (scaffold template location)
    script_dir = Path(__file__).parent
    target_dir = Path.cwd() / folder_name

    # Check if target directory already exists
    if target_dir.exists():
        print(f"\n❌ Error: Directory '{folder_name}' already exists!")
        return

    try:
        # Create target directory
        print(f"Creating directory: {folder_name}")
        target_dir.mkdir(parents=True, exist_ok=True)

        # Copy all files and directories except setup.py, install.py, and tool_template.py
        print("Copying template files...")
        for item in script_dir.iterdir():
            if item.name in [
                "setup.py",
                "install.py",
                ".git",
                "__pycache__",
                ".DS_Store",
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

        # Initialize git repository
        print("Initializing git repository...")
        os.chdir(target_dir)
        os.system("git init")
        os.system("git add .")
        os.system(
            f'git commit -m "Initial commit: {folder_name} from oxsci-mcp-scaffold"'
        )

        # Create .gitignore if not exists
        gitignore_path = target_dir / ".gitignore"
        if not gitignore_path.exists():
            gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
venv/
env/
ENV/
.venv/

# Poetry
poetry.lock

# IDEs
.vscode/
.idea/
*.swp
*.swo
*~

# Testing
.pytest_cache/
.coverage
htmlcov/

# OS
.DS_Store
Thumbs.db

# Environment
.env
.env.local
"""
            gitignore_path.write_text(gitignore_content)
            os.system("git add .gitignore")
            os.system('git commit -m "Add .gitignore"')

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
        print(f"  5. poetry run uvicorn app.core.main:app --reload --port 8060")
        print()
        print("For more information, see README.md")
        print()

    except Exception as e:
        print(f"\n❌ Error during setup: {e}")
        import traceback

        traceback.print_exc()
        if target_dir.exists():
            print(f"\nCleaning up {folder_name}...")
            shutil.rmtree(target_dir)
        return


if __name__ == "__main__":
    try:
        setup_service()
    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user.")
        sys.exit(1)
