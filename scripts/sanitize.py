#!/usr/bin/env python3
"""
AI Collaboration Portal - Sanitization & Redaction Engine
Scans and redacts credentials, hostnames, PII, and private paths before sharing.
Zero external dependencies (pure standard library).
"""

import os
import sys
import re
import argparse
from pathlib import Path
from typing import List, Tuple, Dict

# High-entropy / Known Secret Patterns
SECRET_PATTERNS = [
    ("OpenAI API Key", re.compile(r"sk-(?:proj-)?[A-Za-z0-9_-]{20,}")),
    ("Anthropic API Key", re.compile(r"sk-ant-[A-Za-z0-9_-]{20,}")),
    ("Google API Key", re.compile(r"AIza[0-9A-Za-z-_]{35}")),
    ("GitHub Personal Token", re.compile(r"(?:ghp_[A-Za-z0-9]{36}|github_pat_[A-Za-z0-9_]{82})")),
    ("HuggingFace Token", re.compile(r"hf_[A-Za-z0-9]{34,}")),
    ("AWS Access Key ID", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("Private Key Block", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----[\s\S]*?-----END (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    ("Generic High-Entropy Bearer", re.compile(r"(?i)bearer\s+[a-zA-Z0-9_\-\.]{32,}")),
    ("Generic Password/Secret assignment", re.compile(r"""(?i)(?:password|secret|token|api_key|auth_token)\s*[:=]\s*["']([^"'\s]{8,})["']""")),
]

# Sensitive Infrastructure & PII Patterns
TOPOLOGY_AND_PII_PATTERNS = [
    ("Local User Path", re.compile(r"/Users/[a-zA-Z0-9_\-]+/"), "~/"),
    ("Homelab Hostnames", re.compile(r"\b(cluster-node|cluster-node|cluster-node|cluster-node|cluster-node)\b", re.IGNORECASE), "cluster-node"),
    ("Private Subnet IPs", re.compile(r"\b(?:192\.168\.\d{1,3}\.\d{1,3}|10\.\d{1,3}\.\d{1,3}\.\d{1,3}|172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3})\b"), "10.0.0.x"),
    ("Tailscale IPs", re.compile(r"\b100\.(?:6[4-9]|[7-9]\d|1[01]\d|12[0-7])\.\d{1,3}\.\d{1,3}\b"), "100.64.0.x"),
    ("Personal Email", re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"), "collaborator@example.com"),
    ("Protected Home Mounts", re.compile(r"~/(?:EServ|OrbStack|Models)\b"), "~/Storage"),
]

# OS metadata files to skip silently
IGNORED_OS_PATTERNS = [
    re.compile(r".*\.DS_Store$"),
    re.compile(r".*\.pyc$"),
    re.compile(r".*__pycache__.*"),
]

# File exclusion blocklist (filenames or patterns that should never be exported)
BLOCKED_FILE_PATTERNS = [
    re.compile(r".*\.env(?:\..*)?$"),
    re.compile(r".*\.(?:pem|key|p12|pfx|pkcs12)$"),
    re.compile(r".*id_rsa.*$"),
    re.compile(r".*credentials.*\.json$"),
    re.compile(r".*chat\.db.*$"),
]


def is_os_ignored(file_path: Path) -> bool:
    name = file_path.name
    rel = str(file_path)
    return any(pattern.match(name) or pattern.match(rel) for pattern in IGNORED_OS_PATTERNS)


def is_file_blocked(file_path: Path) -> bool:
    name = file_path.name
    rel = str(file_path)
    return any(pattern.match(name) or pattern.match(rel) for pattern in BLOCKED_FILE_PATTERNS)


def scan_text(text: str) -> List[Tuple[str, str, int]]:
    """Finds all potential secrets in text. Returns (rule_name, matched_token, line_number)."""
    findings = []
    lines = text.splitlines()
    for line_idx, line in enumerate(lines, 1):
        for rule_name, regex in SECRET_PATTERNS:
            for match in regex.finditer(line):
                token = match.group(0)
                findings.append((rule_name, token, line_idx))
    return findings


def redact_text(text: str) -> Tuple[str, int]:
    """Applies redaction rules for secrets and topology/PII. Returns (sanitized_text, redaction_count)."""
    count = 0
    sanitized = text

    # Redact secrets
    for rule_name, regex in SECRET_PATTERNS:
        matches = list(regex.finditer(sanitized))
        if matches:
            count += len(matches)
            sanitized = regex.sub(f"[REDACTED_{rule_name.upper().replace(' ', '_')}]", sanitized)

    # Redact topology & PII
    for rule_name, regex, replacement in TOPOLOGY_AND_PII_PATTERNS:
        matches = list(regex.finditer(sanitized))
        if matches:
            count += len(matches)
            sanitized = regex.sub(replacement, sanitized)

    return sanitized, count


def process_directory(source_dir: Path, target_dir: Path = None, check_only: bool = False) -> Dict:
    stats = {
        "files_scanned": 0,
        "files_blocked": 0,
        "files_redacted": 0,
        "secrets_found": 0,
        "issues": []
    }

    source_dir = source_dir.resolve()
    if target_dir:
        target_dir = target_dir.resolve()

    for root, dirs, files in os.walk(source_dir):
        # Exclude hidden git dirs
        dirs[:] = [d for d in dirs if d not in {".git", ".system_generated", "node_modules", ".venv"}]

        for file in files:
            src_file = Path(root) / file
            rel_path = src_file.relative_to(source_dir)

            if is_os_ignored(src_file):
                continue

            if is_file_blocked(src_file):
                stats["files_blocked"] += 1
                stats["issues"].append(f"[BLOCKED FILE] {rel_path}")
                continue

            stats["files_scanned"] += 1
            try:
                content = src_file.read_text(encoding="utf-8", errors="ignore")
            except Exception as e:
                stats["issues"].append(f"[READ ERROR] {rel_path}: {e}")
                continue

            findings = scan_text(content)
            if findings:
                stats["secrets_found"] += len(findings)
                for rule_name, token, line_no in findings:
                    preview = token[:6] + "..." + token[-4:] if len(token) > 12 else "[EXACT MATCH]"
                    stats["issues"].append(f"[SECRET DETECTED] {rel_path}:{line_no} ({rule_name}: {preview})")

            if not check_only and target_dir:
                sanitized_content, red_count = redact_text(content)
                dest_file = target_dir / rel_path
                dest_file.parent.mkdir(parents=True, exist_ok=True)
                dest_file.write_text(sanitized_content, encoding="utf-8")
                if red_count > 0:
                    stats["files_redacted"] += 1

    return stats


def main():
    parser = argparse.ArgumentParser(description="Sanitize and redact AI collaboration materials.")
    parser.add_argument("--source", "-s", type=Path, required=True, help="Source directory or file")
    parser.add_argument("--dest", "-d", type=Path, help="Target sanitized output directory")
    parser.add_argument("--check", action="store_true", help="Audit mode: scan and exit with code 1 if issues found")
    args = parser.parse_args()

    if not args.source.exists():
        print(f"Error: Source path '{args.source}' does not exist.")
        sys.exit(1)

    if not args.check and not args.dest:
        print("Error: Must specify --dest when not running with --check.")
        sys.exit(1)

    print(f"=== Scanning {'& Redacting ' if args.dest else ''}{args.source} ===")
    stats = process_directory(args.source, args.dest, check_only=args.check)

    print(f"Files scanned: {stats['files_scanned']}")
    print(f"Files blocked: {stats['files_blocked']}")
    print(f"Files redacted: {stats['files_redacted']}")
    print(f"Secrets detected: {stats['secrets_found']}")

    if stats["issues"]:
        print("\n--- Details / Issues ---")
        for issue in stats["issues"][:30]:
            print("  *", issue)
        if len(stats["issues"]) > 30:
            print(f"  ... and {len(stats['issues']) - 30} more.")

    if args.check and (stats["secrets_found"] > 0 or stats["files_blocked"] > 0):
        print("\n[FAIL] Security check failed: Secrets or blocked files were detected.")
        sys.exit(1)

    print("\n[OK] Sanitization check completed successfully.")


if __name__ == "__main__":
    main()
