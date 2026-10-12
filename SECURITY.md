# Security

Do not put API keys, access tokens, passwords, private keys, or private user
data in this repository, generated pages, screenshots, or Git commits.
The published site does not require runtime credentials.

Before publishing changes, stage the intended files and run:

```bash
python3 scripts/audit_publication.py
python3 tests/validate.py
gitleaks git --redact --no-banner .
```

The built-in audit checks the Git index and reports locations without printing
secret values. Gitleaks scans the commit history. Neither tool establishes
redistribution rights for media or guarantees that all secrets are detected.
To enable Gitleaks before local commits, install `pre-commit` and run
`pre-commit install`; the hook configuration is included in the repository.

Report sensitive vulnerabilities through GitHub's private vulnerability
reporting on this repository's Security tab. Do not include credentials or
private data in public issues. Revoke exposed credentials immediately;
removing them from the current files does not remove them from Git history.
