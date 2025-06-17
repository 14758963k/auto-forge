#!/usr/bin/env python3
"""
auto_forge.py - Automated Software Project Generator

This script uses Mistral AI to generate project blueprints, creates the folder structure,
and automates GitHub Copilot to write the actual code using pyautogui.
"""

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Any

import requests
import pyautogui

# Configuration
MISTRAL_API_KEY = "Input-your-mistral-api-key"  # Replace with actual API key
MISTRAL_API_URL = "https://api.mistral.ai/v1/chat/completions"


class MistralPlanner:
    """Handles communication with Mistral AI to generate project blueprints."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        # Fallback blueprint for when API fails
        self.fallback_structure = {
            "folders": ["src", "tests", "docs"],
            "files": [
                {
                    "path": "src/main.py",
                    "description": "Main application entry point",
                    "copilot_prompt": "Create a Python main.py file that serves as the entry point for the application"
                },
                {
                    "path": "tests/test_main.py", 
                    "description": "Unit tests for main module",
                    "copilot_prompt": "Create pytest unit tests for the main.py module"
                },
                {
                    "path": "README.md",
                    "description": "Project documentation",
                    "copilot_prompt": "Create a comprehensive README.md file for this project"
                }
            ],
            "interactions": "Basic project structure with main application file, tests, and documentation.",
            "test_command": "pytest tests"
        }
    
    def build_prompt(self, topic: str) -> str:
        """Build the prompt for Mistral to generate project structure."""
        return f"""You are a professional AI software architect and project planner. Your job is to produce a detailed, JSON-formatted blueprint for a software project.

Topic: "{topic}"

Please respond with **only valid JSON** containing the following keys:
1. **folders** - An array of folder paths (relative to the project root) to be created.
2. **files** - An array of objects, each with:
   • **path**: the file path relative to project root (e.g., `src/main.py`)
   • **description**: a one-sentence summary of what that file does
   • **copilot_prompt**: a concise, clear prompt that, when sent to GitHub Copilot, will generate the full contents of this file
3. **interactions** - A free-form text field explaining how the files and folders work together
4. **test_command** (optional) - A shell command to run the project's test suite

Respond with only the JSON, no additional text."""

    def ask(self, topic: str) -> str:
        """Send request to Mistral API and return the response."""
        prompt = self.build_prompt(topic)
        
        payload = {
            "model": "mistral-large-latest",
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": 2000,
            "temperature": 0.3
        }
        
        # Try multiple times with increasing timeouts
        timeouts = [30, 60, 90]
        
        for attempt, timeout in enumerate(timeouts, 1):
            try:
                print(f"Attempting API call {attempt}/{len(timeouts)} (timeout: {timeout}s)...")
                response = requests.post(MISTRAL_API_URL, headers=self.headers, json=payload, timeout=timeout)
                response.raise_for_status()
                
                data = response.json()
                return data["choices"][0]["message"]["content"].strip()
            
            except requests.exceptions.Timeout as e:
                print(f"Timeout on attempt {attempt}: {e}")
                if attempt == len(timeouts):
                    print("All API attempts failed. Using fallback structure...")
                    return self._get_fallback_structure(topic)
                time.sleep(2)  # Wait before retry
                
            except requests.exceptions.RequestException as e:
                print(f"API Error on attempt {attempt}: {e}")
                if attempt == len(timeouts):
                    print("All API attempts failed. Using fallback structure...")
                    return self._get_fallback_structure(topic)
                time.sleep(2)
                
            except (KeyError, IndexError) as e:
                print(f"Error parsing Mistral response: {e}")
                if attempt == len(timeouts):
                    return self._get_fallback_structure(topic)
                time.sleep(2)
    
    def _get_fallback_structure(self, topic: str) -> str:
        """Generate a fallback structure based on the topic."""
        # Customize fallback based on topic keywords
        topic_lower = topic.lower()
        
        if any(word in topic_lower for word in ['web', 'website', 'html', 'css', 'js']):
            structure = {
                "folders": ["src", "assets", "css", "js", "tests"],
                "files": [
                    {
                        "path": "src/index.html",
                        "description": f"Main HTML file for {topic}",
                        "copilot_prompt": f"Create a complete HTML5 webpage for {topic} with modern structure and semantic elements"
                    },
                    {
                        "path": "css/style.css",
                        "description": "Main stylesheet",
                        "copilot_prompt": f"Create modern, responsive CSS styles for {topic} webpage with animations and good typography"
                    },
                    {
                        "path": "js/main.js",
                        "description": "Main JavaScript functionality",
                        "copilot_prompt": f"Create JavaScript code for {topic} with interactive features and modern ES6+ syntax"
                    }
                ],
                "interactions": f"A web project for {topic} with HTML structure, CSS styling, and JavaScript functionality working together to create an interactive website.",
                "test_command": ""
            }
        elif any(word in topic_lower for word in ['api', 'server', 'backend']):
            structure = {
                "folders": ["src", "tests", "config"],
                "files": [
                    {
                        "path": "src/app.py",
                        "description": f"Main application server for {topic}",
                        "copilot_prompt": f"Create a FastAPI or Flask server application for {topic} with RESTful endpoints"
                    },
                    {
                        "path": "src/models.py",
                        "description": "Data models",
                        "copilot_prompt": f"Create Pydantic or SQLAlchemy models for {topic} application"
                    },
                    {
                        "path": "tests/test_app.py",
                        "description": "API tests",
                        "copilot_prompt": f"Create comprehensive pytest tests for {topic} API endpoints"
                    }
                ],
                "interactions": f"A backend API for {topic} with models, endpoints, and tests working together.",
                "test_command": "pytest tests"
            }
        else:
            # Generic Python project
            structure = self.fallback_structure.copy()
            structure["interactions"] = f"A Python project for {topic} with main application, tests, and documentation."
            
            # Customize the main file prompt based on topic
            for file_obj in structure["files"]:
                if file_obj["path"] == "src/main.py":
                    file_obj["copilot_prompt"] = f"Create a Python application for {topic} with proper structure and functionality"
        
        return json.dumps(structure, indent=2)
    
    def parse_structure(self, json_string: str) -> Dict[str, Any]:
        """Parse and validate the JSON structure from Mistral."""
        try:
            # Clean the response in case there's markdown formatting
            json_string = json_string.strip()
            if json_string.startswith('```json'):
                json_string = json_string[7:]
            if json_string.endswith('```'):
                json_string = json_string[:-3]
            
            structure = json.loads(json_string)
            
            # Validate required fields
            if "folders" not in structure:
                structure["folders"] = []
            if "files" not in structure:
                structure["files"] = []
            if "interactions" not in structure:
                structure["interactions"] = ""
            
            # Validate file objects
            for file_obj in structure["files"]:
                if not all(key in file_obj for key in ["path", "description", "copilot_prompt"]):
                    raise ValueError(f"Invalid file object: {file_obj}")
            
            return structure
        
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON: {e}")
            print(f"Raw response: {json_string}")
            raise
        except ValueError as e:
            print(f"Validation error: {e}")
            raise


class StructureCreator:
    """Creates the project folder structure and files based on the blueprint."""
    
    def __init__(self, desktop_path: Optional[str] = None):
        if desktop_path is None:
            self.desktop_path = Path.home() / "Desktop"
        else:
            self.desktop_path = Path(desktop_path)
    
    def create_structure(self, topic: str, structure: Dict[str, Any]) -> Path:
        """Create the complete project structure on desktop."""
        # Create project folder
        project_name = self._sanitize_name(topic)
        project_path = self.desktop_path / project_name
        
        # Remove existing project if it exists
        if project_path.exists():
            import shutil
            shutil.rmtree(project_path)
        
        project_path.mkdir(parents=True, exist_ok=True)
        print(f"Created project folder: {project_path}")
        
        # Create folders
        for folder in structure["folders"]:
            folder_path = project_path / folder
            folder_path.mkdir(parents=True, exist_ok=True)
            print(f"Created folder: {folder}")
        
        # Create files
        for file_obj in structure["files"]:
            file_path = project_path / file_obj["path"]
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write file with description and copilot prompt as comments
            content = f"""# Description: {file_obj['description']}
# Copilot Prompt: {file_obj['copilot_prompt']}

"""
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"Created file: {file_obj['path']}")
        
        # Create README.md with interactions
        readme_path = project_path / "README.md"
        readme_content = f"""# {topic}

## Project Structure

{structure['interactions']}

## Getting Started

This project was generated automatically. Each file contains a Copilot prompt that describes its intended functionality.

"""
        if structure.get("test_command"):
            readme_content += f"""## Testing

Run tests with: `{structure['test_command']}`

"""
        
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        
        print("Created README.md")
        return project_path
    
    def _sanitize_name(self, name: str) -> str:
        """Sanitize the project name for use as a folder name."""
        # Remove or replace invalid characters
        import re
        sanitized = re.sub(r'[<>:"/\\|?*]', '_', name)
        sanitized = sanitized.strip('. ')
        return sanitized[:50]  # Limit length


class CopilotAutomator:
    """Automates VS Code and GitHub Copilot using pyautogui."""
    
    def __init__(self):
        # Configure pyautogui
        pyautogui.PAUSE = 0.8
        pyautogui.FAILSAFE = True
    
    def launch_vscode(self, project_path: Path) -> bool:
        """Launch VS Code with the project folder."""
        commands = ["code", "code.cmd"]
        
        for cmd in commands:
            try:
                subprocess.run([cmd, str(project_path)], check=True, capture_output=True)
                print(f"Launched VS Code with: {cmd}")
                time.sleep(5)  # Wait for VS Code to open
                return True
            except (subprocess.CalledProcessError, FileNotFoundError):
                continue
        
        # Fallback: open in file explorer
        try:
            if os.name == 'nt':  # Windows
                os.startfile(project_path)
            elif os.name == 'posix':  # macOS/Linux
                subprocess.run(['open' if sys.platform == 'darwin' else 'xdg-open', str(project_path)])
            print("Opened project folder in file explorer")
            return False
        except Exception as e:
            print(f"Failed to open project: {e}")
            return False
    
    def automate_copilot(self, structure: Dict[str, Any]) -> None:
        """Automate Copilot for each file in the project."""
        print("Starting Copilot automation...")
        time.sleep(2)
        
        # First, open README.md for context
        self._open_file("README.md")
        time.sleep(2)
        
        # Process each file
        for file_obj in structure["files"]:
            print(f"Processing file: {file_obj['path']}")
            self._process_file(file_obj)
            time.sleep(2)
    
    def _open_file(self, filename: str) -> None:
        """Open a file using VS Code quick open."""
        # Use Ctrl+P for quick open
        pyautogui.hotkey('ctrl', 'p')
        time.sleep(1)
        
        # Type filename
        pyautogui.write(filename)
        time.sleep(1)
        
        # Press Enter
        pyautogui.press('enter')
        time.sleep(2)
    
    def _process_file(self, file_obj: Dict[str, str]) -> None:
        """Process a single file with Copilot."""
        # Open the file
        self._open_file(Path(file_obj["path"]).name)
        
        # Move to end of file (after the comments)
        pyautogui.hotkey('ctrl', 'end')
        time.sleep(0.5)
        
        # Trigger Copilot inline chat with Ctrl+I
        pyautogui.hotkey('ctrl', 'i')
        time.sleep(2)  # Wait for Copilot chat to appear
        
        # Type the prompt into Copilot's chat interface
        pyautogui.write(file_obj['copilot_prompt'])
        time.sleep(1)
        
        # Press Enter to send the prompt to Copilot
        pyautogui.press('enter')
        time.sleep(3)  # Wait for Copilot to generate code
        
        # Accept the suggestion (usually Tab or Ctrl+Enter)
        pyautogui.press('tab')
        time.sleep(1)
        
        # Alternative: If Tab doesn't work, try Ctrl+Enter
        # pyautogui.hotkey('ctrl', 'enter')
        
        # Save file
        pyautogui.hotkey('ctrl', 's')
        time.sleep(1)
        
        print(f"✓ Processed {file_obj['path']}")


class TestRunner:
    """Handles test execution and error fixing."""
    
    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.copilot_automator = CopilotAutomator()
    
    def run_tests(self, test_command: str, max_attempts: int = 3) -> bool:
        """Run tests and fix errors using Copilot."""
        if not test_command:
            print("No test command specified")
            return True
        
        # Check if npm test requires package.json
        if "npm" in test_command.lower():
            package_json = self.project_path / "package.json"
            if not package_json.exists():
                print("npm test specified but no package.json found")
                return True
        
        print(f"Running tests with command: {test_command}")
        
        for attempt in range(max_attempts):
            print(f"Test attempt {attempt + 1}/{max_attempts}")
            
            try:
                result = subprocess.run(
                    test_command.split(),
                    cwd=self.project_path,
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                
                if result.returncode == 0:
                    print("Tests passed!")
                    return True
                else:
                    print(f"Tests failed with return code: {result.returncode}")
                    print(f"STDOUT: {result.stdout}")
                    print(f"STDERR: {result.stderr}")
                    
                    # Create error fix file
                    self._create_error_fix_file(result.stderr, result.stdout)
                    
                    # Attempt to fix with Copilot
                    self._fix_with_copilot()
                    
                    time.sleep(2)  # Wait before next attempt
            
            except subprocess.TimeoutExpired:
                print("Test command timed out")
                return False
            except Exception as e:
                print(f"Error running tests: {e}")
                return False
        
        print("Failed to fix tests after maximum attempts")
        return False
    
    def _create_error_fix_file(self, stderr: str, stdout: str) -> None:
        """Create a file with error information for Copilot to fix."""
        error_file = self.project_path / "copilot_error_fix.txt"
        
        content = f"""# Fix Prompt: The following errors occurred during testing. Please analyze and fix the issues:

## STDERR:
{stderr}

## STDOUT:
{stdout}

## Instructions:
Please identify the root cause of these errors and provide fixes for the relevant files.
Focus on syntax errors, missing imports, incorrect function signatures, and logical issues.
"""
        
        with open(error_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("Created copilot_error_fix.txt")
    
    def _fix_with_copilot(self) -> None:
        """Use Copilot to fix the errors."""
        print("Attempting to fix errors with Copilot...")
        
        # Open the error fix file
        self.copilot_automator._open_file("copilot_error_fix.txt")
        time.sleep(2)
        
        # Trigger Copilot to analyze the errors
        pyautogui.hotkey('ctrl', 'i')
        time.sleep(2)
        
        pyautogui.write("Analyze these test errors and suggest fixes for the project files")
        time.sleep(1)
        
        pyautogui.press('enter')
        time.sleep(5)  # Wait for analysis
        
        pyautogui.press('tab')  # Accept suggestions
        time.sleep(1)


def main():
    """Main orchestration function."""
    print("=== Auto Forge - Automated Software Project Generator ===")
    
    # Get topic from user
    topic = input("Enter your project topic/description: ").strip()
    if not topic:
        print("No topic provided. Exiting.")
        return
    
    try:
        # Step 1: Generate blueprint with Mistral
        print("\n1. Generating project blueprint with Mistral AI...")
        print("⚠️  Note: If API fails, will use intelligent fallback structure")
        planner = MistralPlanner(MISTRAL_API_KEY)
        json_response = planner.ask(topic)
        structure = planner.parse_structure(json_response)
        print("✓ Blueprint generated successfully")
        
        # Show what was generated
        print(f"  - {len(structure['folders'])} folders")
        print(f"  - {len(structure['files'])} files")
        if structure.get('test_command'):
            print(f"  - Test command: {structure['test_command']}")
        
        # Step 2: Create project structure
        print("\n2. Creating project structure...")
        creator = StructureCreator()
        project_path = creator.create_structure(topic, structure)
        print(f"✓ Project created at: {project_path}")
        
        # Step 3: Automate Copilot
        print("\n3. Launching VS Code and automating Copilot...")
        automator = CopilotAutomator()
        vscode_launched = automator.launch_vscode(project_path)
        
        if vscode_launched:
            print("\n🤖 IMPORTANT: Make sure GitHub Copilot is enabled in VS Code!")
            print("💡 TIP: The automation will use Ctrl+I to trigger Copilot's inline chat")
            input("Press Enter when VS Code is ready and you're ready to start Copilot automation...")
            automator.automate_copilot(structure)
            print("✓ Copilot automation completed")
        else:
            print("⚠ VS Code not launched automatically. Please open the project manually.")
        
        # Step 4: Run tests if specified
        if structure.get("test_command"):
            print("\n4. Running tests...")
            test_runner = TestRunner(project_path)
            success = test_runner.run_tests(structure["test_command"])
            
            if success:
                print("✓ Tests passed or no test failures")
            else:
                print("⚠ Tests failed after multiple attempts")
        else:
            print("\n4. No test command specified, skipping tests")
        
        print(f"\n🎉 Project '{topic}' has been successfully forged!")
        print(f"📁 Location: {project_path}")
        
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
