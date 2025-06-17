# Auto Forge

**Auto Forge** is a Python-based automation tool that turns your project ideas into structured, working codebases — instantly.

Using the power of **Mistral AI** for smart project planning and **GitHub Copilot** for intelligent code generation, Auto Forge handles everything from scaffolding folders and files to injecting contextual prompts and even automating your Visual Studio Code workflow.

---

## 🚀 What It Does

1. **Input a Project Idea**  
   You simply give it a topic like "chat app", "alarm clock", or "blog website".

2. **AI Blueprinting**  
   Auto Forge sends the topic to Mistral, which returns:
   - A full folder & file structure
   - Descriptions for each file
   - Specific prompts for GitHub Copilot to use
   - A readable explanation of how the components interact

3. **Scaffolding the Project**  
   Auto Forge creates all files, inserts structured Copilot prompts, and sets up the project directory.

4. **Launch & Automate Copilot**  
   It opens VS Code, triggers Copilot suggestions for each file using `Ctrl+I`, and auto-generates code.

5. **Optional Test Loop**  
   If a test command (e.g. `npm test`, `pytest`) is provided, it will attempt to run and fix errors using Copilot.

---

## 📂 Example File Output

```plaintext
project_root/
├── src/
│   └── main.js  # Copilot Prompt: Build the main logic
├── styles/
│   └── app.css  # Copilot Prompt: Add basic styling
├── index.html   # Copilot Prompt: Create homepage structure
└── README.md    # Includes file interactions and purpose
🧠 Why This Was Built
Building entire project structures manually is time-consuming, repetitive, and error-prone. As a developer, I wanted a faster way to go from idea to code.

Auto Forge was built by Kim Kimani to streamline the thinking-to-coding pipeline — with full automation. Whether you’re prototyping, studying, or deploying fast, this tool removes the friction.

⏱️ Time Saved
On average, Auto Forge saves 45 minutes to 2 hours per project by skipping:

Manual folder setup

File boilerplate writing

Context-switching to prompt Copilot

🧩 Graph: Time Comparison
Task	Manual Setup	Auto Forge
Folder Creation	10 mins	0 mins
Writing File Stubs	20 mins	1 min
Copilot Prompt Writing	15 mins	0 mins
VS Code Navigation	10 mins	0 mins
Total	55+ mins	< 2 mins

📦 Installation
bash
Copy
Edit
git clone https://github.com/yourusername/auto-forge.git
cd auto-forge
pip install -r requirements.txt
Requires Python 3.8+, VS Code with Copilot, and pyautogui.

📞 Contact
Have ideas or want to get the code?

Click here to reach me directly:
👉 Message Kim on WhatsApp

🪪 License
Licensed under the MIT License.

