
import os
import subprocess
import sys

# The path to the other repository
REPO_PATH = "/Users/lvc/AI Scripts/2025_10 Afore JSON cleanup"
FILE_TO_COMMIT = "consar_siefores_with_usd.json"

def run_git_cmd(args, cwd):
    print(f"Running: git {' '.join(args)} in {cwd}")
    result = subprocess.run(
        ["git"] + args, 
        cwd=cwd, 
        capture_output=True, 
        text=True
    )
    if result.returncode == 0:
        print(f"✅ Success: {result.stdout.strip()}")
        return True
    else:
        print(f"❌ Error: {result.stderr.strip()}")
        return False

if not os.path.exists(REPO_PATH):
    print(f"❌ Repo path not found: {REPO_PATH}")
    sys.exit(1)

print(f"📂 Switch to: {REPO_PATH}")

# 1. Check status
run_git_cmd(["status"], REPO_PATH)

# 2. Add file
print("➕ Adding file (forcing)...")
if not run_git_cmd(["add", "-f", FILE_TO_COMMIT], REPO_PATH):
    sys.exit(1)

# 3. Commit
print("💾 Committing...")
# Check if there are changes to commit first to avoid empty commit error
status_res = subprocess.run(["git", "status", "--porcelain"], cwd=REPO_PATH, capture_output=True, text=True)
if FILE_TO_COMMIT in status_res.stdout:
    if not run_git_cmd(["commit", "-m", "feat: Update Siefore data for November 2025"], REPO_PATH):
        sys.exit(1)
else:
    print("ℹ️  No changes to commit (already committed?)")

# 4. Push
print("⬆️  Pushing...")
if not run_git_cmd(["push"], REPO_PATH):
    print("❌ Push failed. Please check your git credentials or remote settings.")
    sys.exit(1)

print("\n✅ Successfully updated remote repo.")
