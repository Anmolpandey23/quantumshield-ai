# GitHub Setup (Group Leader): Private Repo, Team Access, Safe Workflow

Follow in order. Total time: about 30 minutes.

## 1. One-time prerequisites
1. Create a GitHub account and **turn on two-factor authentication** (Settings, Password and authentication).
2. Install Git (git-scm.com; on Windows this also gives you Git Bash).
3. Tell Git who you are:
```bash
git config --global user.name "Your Name"
git config --global user.email "the-email-on-your-github-account"
git config --global init.defaultBranch main
```
Check: `git --version` prints a version.

## 2. Where should the repo live?
- **Simplest:** under the leader's personal account (`github.com/<you>/quantumshield-stage2`), private, with teammates added as collaborators.
- If your team keeps one repo for all four stages, put this folder inside it as `stage2_quantum_cryptography/`. Then move `.github/workflows/ci.yml` to the root of that repo and add `working-directory: stage2_quantum_cryptography` to its steps.

## 3. Create the private repository
1. github.com, click **+**, **New repository**.
2. Name: `quantumshield-stage2`. Visibility: **Private**.
3. **Do not** tick README, .gitignore or license. This project already has files; an empty repo avoids merge trouble.
4. Click **Create repository**.

## 4. Push this project (pick ONE way)

**Way A: GitHub CLI (shortest).** Install `gh` (cli.github.com), then from the project folder:
```bash
gh auth login
git init -b main
git add .
git commit -m "Stage 2: QRNG, BB84, ML-KEM, ML-DSA, tests and results"
gh repo create quantumshield-stage2 --private --source=. --remote=origin --push
```

**Way B: plain Git + token.**
```bash
git init -b main
git add .
git commit -m "Stage 2: QRNG, BB84, ML-KEM, ML-DSA, tests and results"
git remote add origin https://github.com/<you>/quantumshield-stage2.git
git push -u origin main
```
GitHub does not accept your password. When asked for a password, paste a **Personal Access Token**: Settings, Developer settings, Personal access tokens, Tokens (classic), Generate new token, tick `repo`, copy it at once.

Check: refresh the repo page. You see the files, and a green tick appears next to the commit once CI finishes (Actions tab).

## 5. Add your three teammates
Repo, **Settings**, **Collaborators**, **Add people**. Send each their username. They must **accept the invitation** (email or the bell icon). Check: each can open the private repo URL.

Each teammate then runs:
```bash
git clone https://github.com/<you>/quantumshield-stage2.git
cd quantumshield-stage2
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt && python -m pytest -q
```

## 6. Protect `main` (important plan limit)
In **Settings, Branches** you can require a pull request and one approval before merging. **On a private repo this needs a paid plan**: GitHub Pro on a personal account, or GitHub Team for an organization. On the free plan GitHub shows an "upgrade" message and enforces nothing. Students can get GitHub Pro free through the GitHub Student Developer Pack (apply with your college email; approval can take a few days).

If you cannot enable it, use a **team rule instead**: nobody pushes to `main`. Everyone works on a branch and merges through a pull request that another member approves. CI (Actions) still runs on every pull request on the free plan.

## 7. Daily workflow for every teammate
```bash
git checkout main && git pull                 # start from the latest code
git checkout -b stage2-fix-bb84-docs          # one branch per task
# ... edit ...
python -m pytest -q                           # never push red tests
git add . && git commit -m "Explain QBER threshold in README"
git push -u origin stage2-fix-bb84-docs
```
Then on GitHub: **Compare and pull request**, add a reviewer, wait for CI to go green, get one approval, **Merge**, delete the branch. Back locally: `git checkout main && git pull`.

## 8. Rules that prevent disasters
- **Never commit secrets** (tokens, `.env`, private keys). `.gitignore` covers common names, but check `git status` before `git add .`.
- Commit small and often, with messages that say what changed.
- Pull before you start work and before you push.
- Don't edit the same file as a teammate at the same time. If you do, see the conflict fix below.
- Tag finished milestones: `git tag v0.1-stage2 && git push --tags`.

## 9. Common errors and fixes
| Message | Fix |
|---|---|
| `Authentication failed` | Use a Personal Access Token (or `gh auth login`), not your password. |
| `remote: Repository not found` | Wrong URL, or the invite was not accepted. Check the exact URL and invitation. |
| `failed to push some refs` | Someone pushed first. Run `git pull --rebase`, then push again. |
| `refusing to merge unrelated histories` | You created the repo with a README. Run `git pull origin main --allow-unrelated-histories`. |
| Conflict markers `<<<<<<<` | Open the file, keep the right lines, delete the marker lines, then `git add .`, `git commit`. |
| `ModuleNotFoundError: stage2` | Run commands from the repo root, with the venv active. |
| CI red on GitHub, green locally | Versions differ. Use `requirements.txt` exactly and Python 3.11 or 3.12. |
