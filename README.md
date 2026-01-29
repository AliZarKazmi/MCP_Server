# Gmail MCP Server (Claude Desktop)

An MCP (Model Context Protocol) server that lets an AI assistant:
1) Read unread emails from a Gmail inbox
2) Create correctly-threaded draft replies in Gmail

This project is designed to be run locally and connected to Claude Desktop.

---

## Features

- **Tool: `get_unread_emails`**
  - Returns unread inbox emails with:
    - sender, subject, snippet, message id, thread id, date
  - Supports a `max_results` parameter (defaults to `MAX_UNREAD`)

- **Tool: `create_draft_reply`**
  - Creates a Gmail **draft reply** to a given email `message_id`
  - Ensures correct threading by setting:
    - `threadId`
    - `In-Reply-To`
    - `References`
    - `Subject` (`Re:` handling)

---

## Tech Stack

- Python 3.11+
- MCP Python SDK
- Google Gmail API (OAuth 2.0)
- Claude Desktop (local MCP connection)

---

## Prerequisites

- Windows 10/11
- Python 3.11+ installed
- A Gmail account
- Claude Desktop installed
- A Google Cloud project with:
  - Gmail API enabled
  - OAuth consent screen configured
  - OAuth Client ID created (**Desktop app**)

---

## Project Structure

MCP_Server/
server.py
gmail_client.py
requirements.txt
.env.example
.gitignore
claude_desktop_config.example.json
screenshots/


## Setup (Google Cloud + OAuth)

1) Create a Google Cloud project  
2) Enable the **Gmail API**  
3) Configure the **OAuth consent screen**
   - If in *Testing*, add your Gmail address under **Test users**
4) Create OAuth credentials:
   - Type: **Desktop app**
5) Download the OAuth client JSON and save it as: **credentials.json**

---

## Local Installation

### 1. Create and activate a virtual environment

Open PowerShell in the project folder:

powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1


### 2. Install dependencies
 
python -m pip install -r requirements.txt

### 3. Create .env

Update .env to use absolute paths

Run the Server Locally

### 4. Start the MCP server

D:\MCP_Server\.venv\Scripts\python.exe D:\MCP_Server\server.py

The process will stay running and wait for Claude Desktop to connect.

### 5. Connect Claude Desktop

Claude Desktop reads MCP server config from: %APPDATA%\Claude\claude_desktop_config.json

After updating the config:

Fully quit Claude Desktop (tray icon → Quit)

### 6. Reopen Claude Desktop

A copy of this config is included in the repo as:
claude_desktop_config.example.json

### 7. Screenshots (Demo Evidence)

Screenshots are included in screenshots/:

01-tools.png — Claude shows MCP tools

02-unread_emails.png — Claude reads unread emails via tool call

03-reply_mail.png — Claude generates reply text

04-gmail_draftCreated.png — Gmail UI showing the created draft

### 7. Security Notes

This server only reads emails (gmail.readonly) and creates drafts (gmail.compose).


### 8. Troubleshooting

OAuth 403 access_denied

Ensure OAuth consent screen is configured

If status is Testing, add your Gmail address under Test users

Confirm OAuth client type is Desktop app

Claude says credentials are missing

Use absolute paths in .env

Confirm credentials.json exists in the configured location