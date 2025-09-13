# GitHub Issue: Refactor - Clean Up Project Root and Update README

**Title:** Refactor: Clean Up Project Root and Update README

**Body:**

## Description

The project root has become cluttered with various config files, scripts, and temporary assets. The goal is to improve the developer experience and reduce technical debt by organizing the project structure. Currently, the root directory contains scattered configuration files, standalone utility scripts, and temporary analysis files that make navigation difficult and reduce code maintainability.

## Tasks

- [ ] Create a `/scripts` directory and move all standalone utility scripts into it
- [ ] Consolidate all configuration files (e.g., .dotfiles, *.config.js) into a new `/config` directory where possible  
- [ ] Review and delete any unused or temporary files from the root
- [ ] Update the README.md to reflect the new project structure in the "Getting Started" and "Project Layout" sections
- [ ] Ensure the cleanup does not break the CI/CD pipeline or local development environment

## Acceptance Criteria

- The project root is clean and contains only essential directories and files
- The README.md accurately documents the project structure
- All linting and test commands run successfully after the refactor

---

*This issue should be created in the clduab11/hermes-agent repository using the GitHub web interface or GitHub CLI.*