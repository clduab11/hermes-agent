---
name: "Dependency Management"
about: "Track dependency management improvements for HERMES"
title: "[DEPS] Dependency Management Enhancement"
labels: ["dependencies", "security", "technical-debt"]
assignees: ["clduab11"]
---

## Objective

Implement automated dependency management, security scanning, and regular updates to mitigate vulnerabilities and leverage latest features.

## Current State

- Dependencies in `requirements.txt` and `requirements-ci.txt` with some version pinning
- Security scanning exists in CI but is non-blocking (see `.github/workflows/consolidated-ci.yml` lines 83-101)
- No automated dependency update process (no Dependabot)
- Development dependencies commented out in `requirements.txt` (lines 58-67)
- No license compliance checking

## Tasks

### Phase 1: Dependency Organization

- [ ] Separate dependencies into clear categories:
  - `requirements.txt` - Production dependencies only
  - `requirements-dev.txt` - Development tools (NEW)
  - `requirements-test.txt` - Testing dependencies (NEW)
  - `requirements-ci.txt` - CI-specific dependencies

- [ ] Consider migrating to `pyproject.toml` for better management:
  - `[project.dependencies]`
  - `[project.optional-dependencies]`

- [ ] Pin all dependencies with exact versions
- [ ] Document why each major dependency is needed

### Phase 2: Automated Security Scanning

- [ ] Make security scanning blocking in CI
  - Update `.github/workflows/consolidated-ci.yml` (lines 83-101)
  - Block on high/critical vulnerabilities
  - Allow warnings for low/medium

- [ ] Add Dependabot configuration (`.github/dependabot.yml`)
  - Python dependencies (pip)
  - GitHub Actions
  - Docker (when Dockerfile added)

- [ ] Set up continuous vulnerability monitoring
  - Consider Snyk or similar
  - Automated alerts for new CVEs

- [ ] Add SBOM (Software Bill of Materials) generation

### Phase 3: Dependency Update Strategy

- [ ] Establish update cadence
  - Weekly for security updates
  - Monthly for feature updates

- [ ] Create process for reviewing updates
  - Test compatibility
  - Review changelogs
  - Check for breaking changes

- [ ] Set up automated PR creation for updates
- [ ] Document migration paths for breaking changes

### Phase 4: License Compliance

- [ ] Add license scanning to CI
- [ ] Document all dependency licenses
- [ ] Ensure compatibility with MIT license
- [ ] Add license headers to source files (optional)

### Phase 5: Dependency Optimization

- [ ] Audit for unused packages
- [ ] Find lighter alternatives where appropriate
- [ ] Minimize transitive dependencies
- [ ] Consider vendoring critical small dependencies
- [ ] Document dependency tree and rationale

## Acceptance Criteria

- [ ] All dependencies have clear purpose and documentation
- [ ] Security vulnerabilities detected and fixed within 7 days
- [ ] Dependabot PRs automatically created for updates
- [ ] CI fails on high/critical security vulnerabilities
- [ ] License compliance verified in CI
- [ ] Dependency update process documented
- [ ] No unused dependencies in requirements files

## Technical References

- Dependencies: `requirements.txt`, `requirements-ci.txt`
- CI Workflow: `.github/workflows/consolidated-ci.yml`
- Security Workflow: `.github/workflows/security-compliance.yml`

## Dependabot Configuration Example

```yaml
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 5
    labels:
      - "dependencies"
      - "python"
    groups:
      production:
        patterns:
          - "fastapi*"
          - "pydantic*"
      development:
        patterns:
          - "pytest*"
          - "black"
          - "mypy"
```

## Notes

- Security updates should be prioritized
- Major version updates need careful review
- Test all updates before merging
- Document known compatibility issues
