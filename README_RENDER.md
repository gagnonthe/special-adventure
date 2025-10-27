Deploying this project to Render
================================

This document explains how to push the local project to your GitHub repo and deploy it to Render as a Web Service.

Prerequisites
- You have a GitHub repository (for example: https://github.com/gagnonthe/special-adventure) and push access.
- Git installed locally and configured (name/email); authenticated to GitHub (SSH key or HTTPS + PAT).
- You already have these files in the repository:
  - `app.py` (Flask app)
  - `requirements.txt` (Python dependencies)
  - `Procfile` (commands for Render)
  - `runtime.txt` (optional Python runtime hint)

1) Push local project to GitHub (PowerShell)

Replace <remote-url> with `https://github.com/gagnonthe/special-adventure.git` or your repo URL.

```powershell
# initialize repo (if not already a git repo)
git init
git add --all
git commit -m "Initial commit: playscore PWA + backend"

# add remote and push
git remote add origin <remote-url>
# If the remote is empty and you want to push the current branch as main:
git branch -M main
git push -u origin main
```

Notes about authentication:
- If using HTTPS, Git may prompt for your GitHub username and a Personal Access Token (PAT) as the password. Create a PAT with `repo` scope.
- If using SSH, ensure your public key is added to GitHub.

2) Deploy on Render (web service)

- Sign in to https://render.com and create a new Web Service.
- Choose "Connect a repository" and pick the GitHub account/repo (you may need to authorize Render).
- Select the `main` branch (or the branch you pushed).
- For the environment/runtime settings:
  - Runtime: Render will read `runtime.txt` (you have `python-3.8.10`).
  - Build Command: leave empty (Render will use default), or set: `pip install -r requirements.txt`
  - Start Command: leave empty if you have a `Procfile`. Otherwise set: `gunicorn app:app --bind 0.0.0.0:$PORT`

- Environment variables (optional):
  - `FLASK_DEBUG` = 0 (recommended)

- Click Deploy.

3) Post-deploy notes
- Your app will be reachable at `https://<your-app>.onrender.com`.
- Upload size limits: Render has platform limits; `app.py` already sets `MAX_CONTENT_LENGTH = 100MB`.
- If you hit runtime or memory limits (music21 can be memory-heavy for large files), consider increasing instance size on Render.

Troubleshooting
- If the deploy fails with missing dependency errors, check `requirements.txt` and include exact pinned versions if needed.
- For long conversions you may see request timeouts; consider implementing async jobs (Render Background Worker) or increase request timeout.

Want me to push the local workspace to your GitHub repo?
- I can provide the exact commands above. I can't push to your GitHub for you without credentials. Run the `git` commands locally, then tell me when the repo is pushed and I'll walk you through connecting Render and completing deployment.

-- end
