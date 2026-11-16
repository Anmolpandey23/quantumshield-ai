# Team Repo, Secure Push/Pull and Stage Integration Guide (VS Code)

**Who this is for:** the group leader (Parts A to C) and every teammate (Parts C to E).
**What it adds on top of the Stage 2 guide:** (1) ONE common private GitHub repo for all four stages, (2) secure push and pull, (3) how Stage 1, Stage 2, Stage 3 and the dashboard plug into each other. Everything here was run and tested on a clean install.

## Contents
- Part A: What the Stage 2 guide did and did not cover
- Part B: Create the ONE common repo (leader, about 40 minutes)
- Part C: Every teammate joins (15 minutes each)
- Part D: Secure push and pull
- Part E: Integration: how the stages plug together
- Part F: Weekly team routine
- Part G: Problems and fixes, final checklist

---

# PART A: What the Stage 2 guide did and did not cover

| Topic | Stage 2 guide | This guide |
|---|---|---|
| Stage 2 development (QRNG, BB84, ML-KEM, ML-DSA, tests, results) | Complete | Included as `stage2_quantum_cryptography/` |
| GitHub for Stage 2 only | Basic (separate repo, token login) | Replaced by ONE repo for all stages |
| One common repo for all 4 stages | Only a short note | Part B and C |
| Secure push and pull (SSH keys, signed commits, secret blocking, no direct push to `main`) | Not covered | Part D |
| Integration with Stage 1, Stage 3, dashboard | Only the output format | Part E, with working code and tests |

**If you already pushed `quantumshield-stage2` as its own repo:** that is fine. You do not delete anything. The common repo contains the same Stage 2 code. Once the common repo works, archive the old one (repo Settings → Archive this repository) so nobody pushes to it by mistake.

---

# PART B: Create the ONE common repo (leader)

## B1. What you received
`quantumshield-ai-monorepo.zip`. Unzip it. It contains:
```text
quantumshield-ai/
├── README.md                         team rules and quick start
├── .gitignore                        blocks secrets, datasets, model files
├── .github/
│   ├── workflows/ci.yml              runs tests on every push and pull request
│   ├── CODEOWNERS                    who reviews which folder
│   └── PULL_REQUEST_TEMPLATE.md      checklist for every pull request
├── contracts/                        JSON Schemas: the agreed interface between stages
├── integration/                      glue that runs the whole loop (works today)
├── scripts/
│   ├── bootstrap.sh                  turns on the safety hooks
│   └── hooks/pre-commit, pre-push    block secrets and direct pushes to main
├── stage1_ai_threat_prediction/      Member 1 (README and contract; empty for now)
├── stage2_quantum_cryptography/      finished Stage 2 (25 tests)
├── stage3_self_healing/              Member 2 (README and contract; empty for now)
└── backend_dashboard/                Member 4 (README and contract; empty for now)
```

## B2. Open it in VS Code and check it runs
```bash
cd quantumshield-ai
code .
```
In the VS Code terminal (Ctrl + backtick key):
```bash
python3 -m venv venv                       # Windows: python -m venv venv
source venv/bin/activate                   # Windows PowerShell: .\venv\Scripts\Activate.ps1
pip install -r requirements-integration.txt
python -m pytest -q
python -m integration.demo
```
**Expected** (7 integration tests pass):
```text
integration/tests/test_integration.py::test_attack_goes_through_all_stages_and_command_is_verified PASSED [ 14%]
integration/tests/test_integration.py::test_benign_traffic_never_triggers_stage2 PASSED [ 28%]
integration/tests/test_integration.py::test_eavesdropper_means_no_command_is_issued PASSED [ 42%]
integration/tests/test_integration.py::test_replayed_command_is_rejected PASSED [ 57%]
integration/tests/test_integration.py::test_broken_stage1_output_is_caught_by_the_contract PASSED [ 71%]
integration/tests/test_integration.py::test_example_files_match_their_contract[stage1_attack.json] PASSED [ 85%]
integration/tests/test_integration.py::test_example_files_match_their_contract[stage1_benign.json] PASSED [100%]
============================== 7 passed ===============================
```
**Expected demo** (the whole loop, with stand-ins for Stage 1 and Stage 3):
```text
1. Benign traffic                  decision=no_action            stage2=None  command=None  verified=None
2. Attack detected                 decision=command_issued       stage2=secure_channel_established  command=isolate  verified=True
3. Attack + eavesdropper on line   decision=aborted_no_command   stage2=aborted_eavesdrop_detected  command=None  verified=None
4. Replay of a genuine command    -> (False, 'replay_detected')
```
Read the four lines: (1) benign traffic triggers nothing; (2) an attack goes through Stage 2 and a signed `isolate` command is verified; (3) with an eavesdropper on the line, Stage 2 aborts and **no command is issued**; (4) replaying a genuine command is rejected.

## B3. Fill in your team's names
1. Open `.github/CODEOWNERS` and replace each `@memberN-github-username` with the real GitHub username.
2. Open `README.md` and put real names in the owner column.

## B4. Turn on the safety hooks and make the first commit
```bash
git init -b main
git config core.hooksPath scripts/hooks
git add .
git update-index --chmod=+x scripts/hooks/pre-commit scripts/hooks/pre-push scripts/bootstrap.sh
git status
```
**Check `git status` carefully.** You must NOT see `venv/`, `.env`, `.pem`, `.key`, or any dataset. Then:
```bash
git commit -m "Initial common repo: 4 stage folders, contracts, integration, Stage 2 complete"
```
Why `update-index --chmod=+x`: on Windows, files lose the "executable" flag, and a teammate on Mac or Linux would then get hooks that silently do nothing. This command stores the flag in Git.

## B5. Create the private repo on GitHub
1. github.com → **+** → **New repository**.
2. Name: `quantumshield-ai`. Visibility: **Private**.
3. Leave README, .gitignore and license **unticked** (your folder already has them).
4. **Create repository.**

## B6. Set up SSH authentication first (see Part D1 for details), then push
```bash
git remote add origin git@github.com:YOUR-USERNAME/quantumshield-ai.git
ALLOW_MAIN_PUSH=1 git push -u origin main
```
Windows PowerShell version of the last line:
```powershell
$env:ALLOW_MAIN_PUSH="1"; git push -u origin main; Remove-Item Env:ALLOW_MAIN_PUSH
```
The pre-push hook blocks pushes to `main` for everyone. This flag is for the **leader's very first push only**.

**Check:** refresh the repo page; you see all folders. Open the **Actions** tab; both jobs (`stage2`, `integration`) turn green after a minute or two.

## B7. Add your teammates
Repo → **Settings → Collaborators → Add people** → give each person **Write** access (not Admin). They must accept the email invitation.

## B8. GitHub settings to check (2 minutes)
1. **Actions** tab works (CI ran).
2. Settings → **Branches** (or **Rules → Rulesets**): "Require a pull request before merging" and "Require approvals". **On a private repo this needs a paid plan** (GitHub Pro on a personal account, or GitHub Team on an organization). Students can get Pro free via the GitHub Student Developer Pack. If it is not available, the pre-push hook and the team rule ("nobody pushes to `main`") are your protection, as described in Part D.
3. Settings → **Code security**: switch on whatever scanning your plan offers (secret scanning, Dependabot alerts). Availability on private repos depends on your plan; the local pre-commit hook works on every plan.

## B9. Tag the starting point
```bash
git tag v0.1-baseline
git push --tags
```

---

# PART C: Every teammate joins

## C1. One-time setup per laptop
Do Part D1 (SSH key) first. Then:
```bash
git clone git@github.com:LEADER-USERNAME/quantumshield-ai.git
cd quantumshield-ai
bash scripts/bootstrap.sh              # Windows PowerShell: git config core.hooksPath scripts/hooks
python3 -m venv venv && source venv/bin/activate      # Windows: python -m venv venv ; .\venv\Scripts\Activate.ps1
pip install -r requirements-integration.txt
python -m pytest -q                    # 7 passed
cd stage2_quantum_cryptography && python -m pytest -q && cd ..    # 25 passed
```
**Check the hooks are on:** `git config core.hooksPath` must print `scripts/hooks`.

In VS Code: **File → Open Folder** → the `quantumshield-ai` folder; `Ctrl+Shift+P` → **Python: Select Interpreter** → the `venv` one.

## C2. Who edits what
| Folder | Owner | Everyone else |
|---|---|---|
| `stage1_ai_threat_prediction/` | Member 1 | read only |
| `stage3_self_healing/` | Member 2 | read only |
| `stage2_quantum_cryptography/` | Member 3 | read only |
| `backend_dashboard/` and `integration/` | Member 4 (+ leader) | read only |
| `contracts/` | all four must approve changes | read only |

"Read only" is a team rule. If you need a change in someone else's folder, ask them or open a pull request they review.

## C3. Daily workflow (copy this)
```bash
git checkout main
git pull --rebase                              # get the latest first
git checkout -b stage1-cpc-encoder             # branch name: stageN-what-you-do
# ... work in VS Code ...
python -m pytest -q                            # root: integration tests
git add <the files you changed>                # prefer this over "git add ." 
git status                                     # read it: nothing secret, nothing huge
git commit -m "Add CPC encoder and unit test"
git push -u origin stage1-cpc-encoder
```
Then on GitHub: **Compare & pull request** → fill the template → add a reviewer (a teammate) → wait for CI to turn green → get **one approval** → **Merge** → delete the branch. Back locally: `git checkout main && git pull --rebase`.

**In VS Code:** the Source Control panel (Ctrl+Shift+G) shows changed files; **+** stages, the tick commits, **Publish Branch** pushes. The hooks run there too. Always create your branch first; **Sync Changes on `main` is blocked on purpose**.

## C4. Large files: datasets and models
CICIDS2017 and trained model files are far too big for Git. They are in `.gitignore`, and the pre-commit hook refuses files over 10 MB. Share them through a shared Drive folder and write the expected path (for example `stage1_ai_threat_prediction/data/raw/`) in your stage README. Each person downloads once.

---

# PART D: Secure push and pull

## D1. Log in with an SSH key (better than passwords or long-lived tokens)
**1. Create the key** (press Enter to accept the default file; set a passphrase):
```bash
ssh-keygen -t ed25519 -C "your-github-email@example.com"
```
**2. Load it into the agent.**
```bash
# Mac / Linux / Git Bash
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519
```
```powershell
# Windows PowerShell (run once as Administrator: enable the agent)
Get-Service ssh-agent | Set-Service -StartupType Manual
Start-Service ssh-agent
ssh-add $env:USERPROFILE\.ssh\id_ed25519
```
**3. Copy the PUBLIC key** (the file ending in `.pub`; **never share the one without `.pub`**):
```bash
cat ~/.ssh/id_ed25519.pub                                   # Mac / Linux / Git Bash
Get-Content $env:USERPROFILE\.ssh\id_ed25519.pub            # Windows PowerShell
```
**4.** GitHub → your profile photo → **Settings → SSH and GPG keys → New SSH key** → Key type **Authentication Key** → paste → **Add**.

**5. Test:**
```bash
ssh -T git@github.com
```
The first time it asks whether to trust the host. Compare the fingerprint with the one in GitHub's documentation ("GitHub's SSH key fingerprints") before typing `yes`. **Expected:** `Hi <your-username>! You've successfully authenticated, but GitHub does not provide shell access.`

**6.** Make sure your repo uses the SSH address:
```bash
git remote -v          # must show git@github.com:...  (not https://)
git remote set-url origin git@github.com:LEADER-USERNAME/quantumshield-ai.git
```

**Alternative if SSH is blocked on your network:** HTTPS with a **fine-grained** Personal Access Token: GitHub → Settings → Developer settings → Personal access tokens → **Fine-grained tokens** → Repository access: **Only select repositories** (this one) → Permissions: **Contents: Read and write** → expiry 30 days. Let the Git Credential Manager (installed with Git for Windows) store it. Never paste a token into a file, a chat or a screenshot.

## D2. Account security (every member)
- Two-factor authentication ON (GitHub → Settings → Password and authentication).
- Use a different password for GitHub than for anything else.
- Never share your SSH private key or token, even with teammates. Each person has their own.

## D3. Signed commits (optional, shows a "Verified" badge)
```bash
git config --global gpg.format ssh
git config --global user.signingkey ~/.ssh/id_ed25519.pub
git config --global commit.gpgsign true
```
Then on GitHub add the **same public key again** as **Key type: Signing Key** (Settings → SSH and GPG keys → New SSH key). Your next commits show "Verified" on GitHub. If Git cannot find the key on Windows, give the full path like `C:/Users/YOURNAME/.ssh/id_ed25519.pub`.

## D4. What the two safety hooks do for you
| Hook | Runs when | Blocks |
|---|---|---|
| `pre-commit` | `git commit` | `.env`, `.pem`, `.key` and similar files; files over 10 MB; GitHub tokens, AWS key IDs, Slack tokens and private-key blocks in the lines you added |
| `pre-push` | `git push` | any push straight to `main` |

They are local helpers, not a guarantee: anyone can switch them off with `--no-verify`. So the team rule is: **never use `--no-verify`**, and keep the hooks on (`git config core.hooksPath` shows `scripts/hooks`).

## D5. Rules for secure pushing
1. Push only to your own branch; merge through a reviewed pull request.
2. Run `git status` and `git diff --staged` before every commit. Read what you are about to publish.
3. Stage specific files (`git add path/to/file`) instead of `git add .` when you have been experimenting.
4. Never commit secrets, datasets, model weights or your `venv/`.
5. Never force-push (`git push --force`) to a shared branch.
6. Keep the repo private. Don't add anyone who is not on the team.

## D6. Rules for secure pulling
1. Check where you pull from: `git remote -v` must show the team repo, nothing else.
2. Use `git pull --rebase` on your own branch. It keeps history tidy and avoids surprise merge commits.
3. Read what arrived: `git log --oneline -10` and, for a teammate's pull request, the **Files changed** tab before approving.
4. Don't run code from a pull request you have not reviewed, especially on a machine that holds tokens or keys.
5. Install packages only from the pinned `requirements.txt` files. Optional check for known vulnerabilities:
```bash
pip install pip-audit
pip-audit -r stage2_quantum_cryptography/requirements.txt
```
6. Teammate left the project? Remove them under Settings → Collaborators. Everyone else keeps working.

## D7. If a secret was committed or pushed by mistake
Treat it as **leaked**, even in a private repo.
1. **Revoke it first.** Delete the token on GitHub, remove the SSH key from GitHub, change the password or API key.
2. Tell the leader.
3. Remove it from the files and then from history (the leader runs `git filter-repo`, or BFG Repo-Cleaner). This rewrites history, so everyone must re-clone afterwards.
4. Do not stop at step 3. Revoking in step 1 is what actually protects you; deleting history alone does not.

## D8. Backups
Every teammate's clone is a full backup. The leader also tags milestones (`git tag v0.2-integration && git push --tags`) so you can always return to a known-good version.

---

# PART E: Integration: how the stages plug together

## E1. The four contracts
The `contracts/` folder holds one JSON Schema per hand-off. A stage that breaks its contract fails the tests immediately instead of failing silently in the demo.

| Contract | Made by | Used by | Key fields |
|---|---|---|---|
| `stage1_output` | Stage 1 | Stage 2, orchestrator | `node_id`, `threat_label`, `confidence`, `anomaly_score`, `risk_score_node`, `explanation` |
| `stage2_output` | Stage 2 `secure_channel()` | Stage 3, orchestrator | `status`, `qber`, `eavesdrop_detected`, `key_gen_time_ms`, `shared_key_id` |
| `stage3_command` | Stage 3 + Stage 2 signing | nodes, orchestrator | `payload{node_id, action, issued_at, nonce}`, `signature` |
| `pipeline_event` | orchestrator | Stage 4 dashboard | `decision`, `stage1`, `stage2`, `stage3_command`, `command_verified` |

## E2. The flow, in one paragraph
Stage 1 scores a node. If the label is not `BENIGN` and the confidence or anomaly score is at least 0.6, Stage 2 runs (QRNG, BB84, ML-KEM, hybrid AES key, ML-DSA). If Stage 2 reports anything other than `secure_channel_established`, **no command is issued**. Otherwise Stage 3 chooses `isolate`, `monitor` or `reconnect`; Stage 2's `CommandSigner` signs it; the node-side `CommandVerifier` checks the signature, the allowlist, freshness and replay. The orchestrator wraps everything in a `pipeline_event` for the dashboard. All of this is in `integration/orchestrator.py` (about 50 lines); read it first.

## E3. Plugging in your stage (replace a stub)

**Stage 1 owner (Member 1).** Create `stage1_ai_threat_prediction/__init__.py` (empty) and `stage1_ai_threat_prediction/predict.py`:
```python
def predict_node(node_id: str, flow_window) -> dict:
    # ... run TabDDPM-trained classifier, CPC Transformer, DyGNN, anomaly detector ...
    return {"contract_version": "1.0", "node_id": node_id, "threat_label": "DDoS",
            "confidence": 0.94, "anomaly_score": 0.87, "risk_score_node": 0.91,
            "explanation": ["unusual packet rate"]}
```
Test it with the contract (put in `stage1_ai_threat_prediction/tests/`):
```python
from integration.validate import validate
def test_output_matches_contract():
    validate(predict_node("10.0.0.1", window), "stage1_output")
```

**Stage 3 owner (Member 2).** Your agent only chooses the action. It never signs; Stage 2 does that.
```python
# stage3_self_healing/decide.py
def decide(stage1: dict, stage2: dict) -> str:
    return "isolate"      # or "monitor" / "reconnect", chosen by the PPO agent + guardrails
```
Use it: `Orchestrator(policy=decide)`. Guardrails (allowed actions, human approval for drastic ones) live in your code; the verifier already rejects any action outside `isolate / monitor / reconnect`.

**Stage 4 owner (Member 4).** Your backend calls `Orchestrator().handle(stage1_output)` for each node and pushes the returned `pipeline_event` to the dashboard (WebSocket or polling). The dashboard reads exactly the fields in `pipeline_event.schema.json`.

**When your module is ready**, do these three things in one pull request:
1. Add your folder name to `STAGE_DIRS` in `integration/__init__.py` (only needed if other stages import yours by short name).
2. Swap the stub for your real function where the orchestrator is created.
3. Add a CI job for your stage in `.github/workflows/ci.yml` (copy the `stage2` job and change the folder name).

## E4. Changing a contract
1. Talk first. All four members must agree.
2. One pull request edits the schema **and** the example files and bumps `contract_version`.
3. All four approve (CODEOWNERS asks them automatically).
4. Merge the producer and consumer changes together, so `main` never goes red.

## E5. What tests protect you
`python -m pytest -q` at the repo root runs the integration tests: attack goes through all stages, benign never triggers Stage 2, an eavesdropper blocks every command, a replayed command is rejected, a Stage 1 output that breaks the contract is caught with a clear message, and the example files stay valid. Run it before every pull request.

---

# PART F: Weekly team routine

| When | What |
|---|---|
| Monday | Each member writes the week's goal for their stage in the stage README. |
| Daily | Branch, commit small, push, pull request. Never leave work only on your laptop. |
| Friday | Everyone merges working code to `main`. The leader runs `python -m integration.demo` and `python -m pytest -q` on a fresh pull and tags the week (`v0.2-week2`). |
| Whenever | Anyone who finds a broken contract tells the whole team the same day. |

---

# PART G: Problems and fixes, final checklist

| Problem | Fix |
|---|---|
| `Permission denied (publickey)` | Your SSH key is not loaded or not on GitHub. Redo D1 steps 2 to 5. |
| `git push` says BLOCKED: do not push directly to main | Correct behavior. Make a branch (`git checkout -b stage2-something`) and open a pull request. |
| Hook does nothing on Mac or Linux | The executable flag is missing: `chmod +x scripts/hooks/*`, and make sure `git config core.hooksPath` prints `scripts/hooks`. |
| `ModuleNotFoundError: stage2` at the repo root | Run through `python -m integration.demo` or `python -m pytest` from the repo root; `integration/__init__.py` adds the stage folders to the path. |
| `ModuleNotFoundError: jsonschema` | `pip install -r requirements-integration.txt` inside the active venv. |
| `ContractError: stage1_output contract broken -> confidence: ...` | Your Stage 1 output does not match `contracts/stage1_output.schema.json`. Fix the output, not the schema (unless the team agreed to change it). |
| CI is red on GitHub, green on your laptop | Use Python 3.11 or 3.12 and the pinned `requirements*.txt`. |
| `failed to push some refs` | `git pull --rebase`, then push again. |
| Merge conflict markers `<<<<<<<` | Open the file, keep the right lines, delete the marker lines, then `git add <file>` and `git rebase --continue` (or `git commit` after a merge). |
| The pre-commit hook blocks a legitimate large file | It should not be in Git. Share it through Drive instead. |

## Final checklist
- [ ] ONE private repo `quantumshield-ai` exists; all four members cloned it.
- [ ] Everyone logs in with SSH (or a fine-grained token), has 2FA on, and `ssh -T git@github.com` works.
- [ ] `git config core.hooksPath` prints `scripts/hooks` on every laptop.
- [ ] Nobody pushes to `main`; every change is a reviewed pull request.
- [ ] `.github/CODEOWNERS` has real usernames.
- [ ] CI is green for `stage2` and `integration`.
- [ ] `python -m pytest -q` (root) shows 7 passed; Stage 2 shows 25 passed.
- [ ] Each owner knows their contract and has a plan to replace their stub.
- [ ] Datasets and model files are shared outside Git.
- [ ] The leader tagged `v0.1-baseline`.
