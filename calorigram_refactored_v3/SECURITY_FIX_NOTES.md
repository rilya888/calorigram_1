# Security Fix Notes (Step 1)
Date: 2025-10-01

**What was done:**
- Removed any `.env` files from the project archive (not tracked anymore).
- Added `.gitignore` that ignores env files and common secrets.
- Created `.env.example` with placeholders for required environment variables.

**Action required from you: rotate/revoke exposed tokens**
1) **Telegram Bot Token**
   - Open chat with **@BotFather**
   - Select your bot → `/revoke` to invalidate the old token
   - Then request a new token (`/token`)
   - Set the new token as `BOT_TOKEN` in your deployment environment variables (Railway/Render/Heroku).

2) **Nebius / Other API Keys**
   - Go to the vendor's console (e.g., Nebius) and **delete/regenerate** the API key that was stored in `.env`.
   - Set the new key in your deployment environment (e.g., `NEBIUS_API_KEY`).

3) **Version control cleanup (important if `.env` was committed before)**
   - Remove the file from git history to prevent leaks in old commits:
     - Using BFG Repo-Cleaner (recommended):  
       `bfg --delete-files .env`
     - Or `git filter-repo` alternative (requires installing `git-filter-repo`):  
       `git filter-repo --path .env --invert-paths`
   - Then force-push to the remote (be careful if this is a shared repo).

**Deployment variables**
- Railway: Project → *Variables* → add `BOT_TOKEN`, `NEBIUS_API_KEY`, etc.
- Render: Service → *Environment* → add variables.
- Heroku: *Settings* → *Config Vars*.
- Docker Compose: use `.env` locally but **never commit** it; keep real secrets outside of VCS.

**Tip:** Never log secrets. Ensure logs don’t print `os.environ` or token values.
