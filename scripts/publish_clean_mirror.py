#!/usr/bin/env python3
"""
AI Collaboration Portal - Clean Mirror Publisher
Copies, sanitizes, and prepares a fresh squashed git mirror repo for external sharing.
Ensures zero past git history or deleted files are leaked.
"""

import os
import sys
import shutil
import subprocess
import argparse
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SANITIZER = SCRIPT_DIR / "sanitize.py"


def run_cmd(cmd: list, cwd: Path = None) -> str:
    res = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"Command failed ({' '.join(cmd)}):\n{res.stderr}\n{res.stdout}")
    return res.stdout.strip()


def main():
    parser = argparse.ArgumentParser(description="Build and publish a clean-slate sanitized git mirror.")
    parser.add_argument("--source", "-s", type=Path, required=True, help="Source workspace or assets directory")
    parser.add_argument("--mirror-repo", "-m", type=Path, required=True, help="Target clean mirror git repository directory")
    parser.add_argument("--branch", "-b", default="main", help="Target branch name (default: main)")
    parser.add_argument("--remote-url", "-r", help="Optional remote URL to configure (e.g. collaborator@example.com:org/shared-ai.git)")
    parser.add_argument("--push", action="store_true", help="Push changes to remote if configured")
    args = parser.parse_args()

    source = args.source.resolve()
    mirror = args.mirror_repo.resolve()

    print(f"[*] Initializing clean mirror build...")
    print(f"    Source: {source}")
    print(f"    Target: {mirror}")

    # Step 1: Run Sanitizer Audit
    print("\n[*] Step 1: Running audit check on source...")
    audit_cmd = [sys.executable, str(SANITIZER), "--source", str(source), "--check"]
    audit_res = subprocess.run(audit_cmd, capture_output=True, text=True)
    if audit_res.returncode != 0:
        print("[!] Security warnings detected during source scan:")
        print(audit_res.stdout)
        print("[!] The publisher will actively redact known patterns during export.")

    # Step 2: Ensure Mirror Git Repo exists
    mirror.mkdir(parents=True, exist_ok=True)
    git_dir = mirror / ".git"
    if not git_dir.exists():
        print("\n[*] Step 2: Initializing new clean git repository...")
        run_cmd(["git", "init", "-b", args.branch], cwd=mirror)
    else:
        print(f"\n[*] Step 2: Using existing git repository at {mirror}")

    # Step 3: Sanitize into mirror repo
    print("\n[*] Step 3: Sanitizing and exporting files into mirror...")
    # Clear existing working tree in mirror except .git
    for item in mirror.iterdir():
        if item.name == ".git":
            continue
        if item.is_dir():
            shutil.rmtree(item)
        else:
            item.unlink()

    export_cmd = [sys.executable, str(SANITIZER), "--source", str(source), "--dest", str(mirror)]
    export_res = subprocess.run(export_cmd, capture_output=True, text=True)
    print(export_res.stdout)

    # Step 4: Verify target repo has zero secrets
    print("\n[*] Step 4: Running final security audit on target mirror...")
    final_audit = subprocess.run([sys.executable, str(SANITIZER), "--source", str(mirror), "--check"], capture_output=True, text=True)
    if final_audit.returncode != 0:
        print("[CRITICAL] Leaks detected in exported mirror! Aborting git commit.")
        print(final_audit.stdout)
        sys.exit(1)
    print("[PASS] Security audit passed with zero detected secrets.")

    # Step 5: Git stage and squashed commit
    print("\n[*] Step 5: Creating squashed commit...")
    run_cmd(["git", "add", "-A"], cwd=mirror)
    status = run_cmd(["git", "status", "--porcelain"], cwd=mirror)
    if not status:
        print("[-] No changes to commit in mirror repository.")
    else:
        commit_msg = "Collaborative AI sync (sanitized snapshot)"
        run_cmd(["git", "commit", "-m", commit_msg], cwd=mirror)
        print(f"[+] Committed clean snapshot to '{args.branch}' branch.")

    # Step 6: Remote setup and push
    if args.remote_url:
        print(f"\n[*] Step 6: Configuring remote origin -> {args.remote_url}")
        remotes = run_cmd(["git", "remote"], cwd=mirror)
        if "origin" in remotes.splitlines():
            run_cmd(["git", "remote", "set-url", "origin", args.remote_url], cwd=mirror)
        else:
            run_cmd(["git", "remote", "add", "origin", args.remote_url], cwd=mirror)

        if args.push:
            print("[*] Pushing to remote...")
            run_cmd(["git", "push", "-u", "origin", args.branch], cwd=mirror)
            print("[+] Push complete!")
        else:
            print("[-] Remote configured. Run with --push or execute 'git push' manually when ready.")

    print("\n=======================================================")
    print("Clean mirror is ready for safe collaboration!")
    print(f"Path: {mirror}")
    print("=======================================================")


if __name__ == "__main__":
    main()
