# Security policy

## Supported versions

Until Loop reaches 1.0, security fixes are applied to the latest release only.

## Reporting a vulnerability

Please report vulnerabilities privately through the repository's GitHub
security-advisory form. Do not open a public issue for an unpatched security
problem. Include the affected version, reproduction steps, impact, and any
suggested mitigation.

## Execution model

Loop executes configured child processes with the operating-system permissions
of the parent process. Review `loop.toml` before running it, especially command
arrays supplied by third parties. Loop does not elevate permissions, approve
external effects, or provide a security boundary around child agents.
