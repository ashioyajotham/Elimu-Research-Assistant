# INSTALL.md - Elimu Research Assistant Setup Guide

## Installation Guide for Educators

### Quick Start for Kenyan Educators

Elimu Research Assistant helps you create localized educational content using AI. This guide will get you started quickly.

#### Prerequisites

- A computer with internet connection
- Python 3.9 or higher (we'll help you install this)
- Google Gemini API key (free tier available)
- Serper.dev search API key (free tier available)

#### Step 1: Install Python

If you don't have Python installed:

**Windows:**

1. Visit [https://python.org/downloads](https://python.org/downloads)
2. Download Python 3.9 or higher
3. Run installer and check "Add Python to PATH"

**Mac:**

```bash
# Using Homebrew (recommended)
brew install python3
```

**Ubuntu/Linux:**

```bash
sudo apt update
sudo apt install python3 python3-pip
```

#### Step 2: Get API Keys

**Google Gemini API (Free):**

1. Visit [https://makersuite.google.com/app/apikey](https://makersuite.google.com/app/apikey)
2. Sign in with Google account
3. Click "Create API Key"
4. Copy and save the key securely

**Serper.dev API (Free):**

1. Visit [https://serper.dev/](https://serper.dev/)
2. Sign up for free account
3. Get your API key from dashboard
4. Copy and save the key securely

#### Step 3: Install Elimu Research Assistant

```bash
# Clone or download the project
git clone https://github.com/ashioyajotham/elimu_research_assistant.git
cd elimu_research_assistant

# Install dependencies
pip install -r requirements.txt

# Set up the tool
pip install -e .
```

#### Step 5: Test Your Installation

Open a **new terminal** and run:

```bash
elimu --version
```

This should display the installed version number.

#### Troubleshooting: 'elimu' is not recognized

If you see an error like `'elimu' is not recognized...` or a `WARNING` during installation about a script not being on `PATH`, you need to add Python's script directory to your system's PATH.

1. During the `pip install` command, copy the path from the warning message. It will look like `C:\Users\YourUsername\AppData\Roaming\Python\Python313\Scripts`.
2. Press the **Windows key**, type `env`, and select **"Edit the system environment variables"**.
3. Click the **"Environment Variables..."** button.
4. In the "User variables" section, select the **`Path`** variable and click **"Edit..."**.
5. Click **"New"** and paste the path you copied.
6. Click **OK** on all windows to save.
7. **Close and reopen your terminal** and try `elimu --version` again.

---

**Contact for Educational Support:**

- Email: [victorashioya960@gmail.com](mailto:victorashioya960@gmail.com)
- Project: Elimu Research Assistant
- Focus: Empowering Kenyan Education Through AI

*Let's make education relevant, accessible, and proudly Kenyan.*
