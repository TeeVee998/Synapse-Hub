---
trigger: always_on
description: Standard Clean Git Push Protocol for target projects and agent-skills Hub, eliminating legacy dual-remote and smart-push dependencies.
---

# CLEAN GIT PUSH PROTOCOL (TARGET PROJECTS & AGENT-SKILLS HUB)

> **Context & Decoupled Architecture:**  
> `agent-skills` is now an **independent, standalone repository** (`https://github.com/TeeVee998/Synapse-Hub.git`).  
> Target projects (Spokes) mount `agent-skills` (Hub) as an external multi-root workspace folder or secondary directory.  
> **Legacy Discontinuation:** The previous "Dual-Remote / Smart Push" mechanism (`smart_push.ps1`, `scm-clean` branch switching, git commit-tree rewriting) is **OFFICIALLY DISCONTINUED**.

---

## 1. Zero-Leakage Guarantee by Architecture

Because `agent-skills` lives in a separate repository completely outside the target project's file tree:
1. **Target Project Repositories are Clean by Default:** Target project git commits only ever contain target source code (Test Cases, Page Objects, Specs, Configs, Fixtures). No `.agents/`, skills, or swarm prompts exist in the target project git index.
2. **No Dual-Remote Needed:** Target projects only need their standard single remote (e.g., `origin` pointing to Company GitLab, GitHub, Bitbucket, or Azure DevOps).
3. **No Branch Stripping Needed:** No need for synthetic `scm-clean` branches or tree filtering.

---

## 2. Standard Push Protocol for Target Projects

When the user commands:  
- *"push"*, *"push code"*, *"push git"*, *"push up"*...

AI Agents execute the clean standard Git workflow within the target project:

### Step 1: Pre-Push Verification (DoD Gate)
Run the project's quality verification gate or test suite before committing:
```bash
# Example: 9 Quality Gates verification or project test runner
python tools/verify_all.py  # or npm test / npx playwright test
```
*Never push unverified code or broken tests.*

### Step 2: Stage Project Changes
Stage changed project files within the target project workspace:
```bash
git add <changed-files>
# or git add -A (within target project directory)
```
Ensure no temporary artifacts (e.g., screenshots, video recordings, local cache) are staged.

### Step 3: Conventional Commit
Create a structured semantic commit message following conventional standards:
```bash
git commit -m "<type>(<scope>): <summary>"
# Examples:
# git commit -m "feat(billing): add Clean POM for Invoice Reconciliation"
# git commit -m "test(auth): add automated login boundary test cases"
# git commit -m "fix(locators): heal stale table row selector in OrderSummaryPage"
```

### Step 4: Direct Push to Project Remote
Push directly to the current tracking branch on the project's remote:
```bash
git push origin <current-branch>
```

### Step 5: Post-Analysis Artifact Push (Post-Audit Auto-Sync)
Whenever the user requests project audit/analysis or runs `tools/analyze_project.py` ("analyze project", "audit project"), after generating/updating the report files:
1. AI Agent must immediately stage the updated intelligence files inside the target project:
   ```bash
   git add PROJECT_HEALTH_REPORT.md repo_map.txt
   ```
2. Commit with conventional semantic message:
   ```bash
   git commit -m "docs(audit): update project health report and AST repo map"
   ```
3. Push to the target project's remote repository:
   ```bash
   git push origin <current-branch>
   ```
*(Ensures the entire team and all AI agents consistently share the latest method map and health metrics).*

---

## 3. Target Project Privacy & File Hygiene

| File / Asset | Location | Recommendation for Target Projects |
| :--- | :--- | :--- |
| **`PROJECT_HEALTH_REPORT.md` & `repo_map.txt`** | Target Project Root | **Commit & push:** Synchronize to git for shared team and AI access. |
| **Test Code / Page Classes** | Target Project Repo | Commit & push to company SCM normally. |
| **`PROJECT_AI_GUIDE.md`** | Target Project Root | **Shared mode:** Commit if team shares AI instructions.<br/>**Strict Privacy mode:** Add to `.gitignore` if company policy disallows AI markdown. |
| **`.agents/` & Skills Hub** | `agent-skills` Repo | **Decoupled:** Exists solely in `agent-skills` repo; never copied into target project. |
| **Temporary Dumps / Logs** | Target Project Root | Ensure added to target `.gitignore` (`Reports/`, `Screenshots/`, `*.log`). |

---

## 4. Push Protocol for `agent-skills` Hub

When authoring or updating universal skills, rules, or tools inside the `agent-skills` repository itself:
```bash
git add -A
git commit -m "feat(skills): update <skill-name> with new capabilities"
git push origin <branch>
```
All skills and rules reside natively in the `agent-skills` repository.
