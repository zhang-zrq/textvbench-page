"""Check the Git index for accidental credentials and local-only files.

Run after `git add`. Findings contain locations and rule names, never secret
values. This focused check complements a full Gitleaks scan and human review.
"""
import json
from pathlib import Path, PurePosixPath
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
LOCAL_PARTS = {'.preview', '__pycache__', '.venv', 'venv', 'node_modules',
               '.aws', '.ssh', '.codex', '.agents', '.idea', '.vscode',
               'test-results', 'playwright-report'}
PRIVATE_SUFFIXES = {'.pem', '.key', '.p12', '.pfx', '.keystore', '.pyc', '.pyo'}
RULES = {
    'private-key': re.compile(rb'-----BEGIN (?:RSA |EC |DSA |OPENSSH |ENCRYPTED )?PRIVATE KEY-----'),
    'github-token': re.compile(rb'\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{50,})\b'),
    'aws-access-key': re.compile(rb'\b(?:AKIA|ASIA)[A-Z0-9]{16}\b'),
    'openai-key': re.compile(rb'\bsk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{40,}\b'),
    'credential-in-url': re.compile(rb'https?://[^\s/<>"\']+:[^\s/<>"\']+@'),
    'absolute-user-path': re.compile(rb'(?:[A-Za-z]:[\\/](?:Users|home)[\\/]|/(?:Users|home)/[A-Za-z0-9_.-]+/)'),
    'private-network-url': re.compile(rb'https?://(?:10\.\d+\.\d+\.\d+|192\.168\.\d+\.\d+|172\.(?:1[6-9]|2\d|3[01])\.\d+\.\d+)(?=[:/\s])'),
    'literal-credential': re.compile(
        rb'''(?i)\b(?:password|passwd|api_key|api-key|access_token|client_secret)\b["']?\s*[:=]\s*["']([^"'\r\n]{8,})["']'''),
}


def main():
    result = subprocess.run(['git', 'ls-files', '--cached', '-z'], cwd=ROOT,
                            check=True, capture_output=True)
    names = [name.decode('utf-8') for name in result.stdout.split(b'\0') if name]
    if not names:
        raise SystemExit('No staged/tracked files. Run git add before auditing.')
    findings = []
    total_bytes = 0
    for name in names:
        path = PurePosixPath(name)
        if (LOCAL_PARTS.intersection(path.parts) or path.suffix.lower() in PRIVATE_SUFFIXES
                or (path.name.startswith('.env') and not path.name.endswith('.example'))
                or path.name in {'credentials.json', '.netrc', '.npmrc', '.pypirc'}
                or path.name.startswith('service-account')):
            findings.append({'path': name, 'rule': 'local-or-sensitive-file'})
        content = subprocess.run(['git', 'show', ':' + name], cwd=ROOT,
                                 check=True, capture_output=True).stdout
        total_bytes += len(content)
        if len(content) > 50 * 1024 * 1024:
            findings.append({'path': name, 'rule': 'oversized-file'})
        for rule, pattern in RULES.items():
            for match in pattern.finditer(content):
                findings.append({'path': name, 'rule': rule,
                                 'line': content.count(b'\n', 0, match.start()) + 1})
    print(json.dumps({'files_checked': len(names), 'bytes_checked': total_bytes,
                      'findings': findings}, ensure_ascii=False, indent=2))
    if findings:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
