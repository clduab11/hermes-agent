---
name: "Docker Containerization"
about: "Track Docker containerization implementation for HERMES"
title: "[INFRA] Docker Containerization Implementation"
labels: ["infrastructure", "docker", "technical-debt"]
assignees: ["clduab11"]
---

## Objective

Containerize HERMES for development environments and optional self-hosted deployments while maintaining App Engine as primary production target.

## Current State

- No Docker containerization exists
- Deployment is App Engine-only (see `app.yaml`, `deployment/deploy.sh`)
- Anti-Docker checks exist in deployment script (lines 121-126)
- Development environment setup requires manual configuration

## Tasks

### Phase 1: Core Docker Infrastructure

- [ ] Create multi-stage `Dockerfile` with builder and runtime stages
  - Use `python:3.11-slim` base image
  - Implement non-root user execution for security
  - Optimize for production with minimal attack surface
  - Target image size under 500MB

- [ ] Create `Dockerfile.dev` for development
  - Include hot-reload capabilities
  - Add debugging tools (ipython, ipdb, debugpy)
  - Volume mount support for live code reloading

- [ ] Create `.dockerignore` to optimize build context
  - Exclude version control, IDE files, test artifacts
  - Keep image lean and builds fast

### Phase 2: Docker Compose Configuration

- [ ] Create `docker-compose.yml` for production-like local testing
  - Services: hermes-api, redis, postgres
  - Health checks for all services
  - Resource limits and restart policies

- [ ] Create `docker-compose.dev.yml` for development
  - Volume mounts for live reload
  - Debug port exposure (5678 for debugpy)
  - Optional debug services (redis-commander, pgadmin)

### Phase 3: Integration & Documentation

- [ ] Update `deployment/deploy.sh` to support Docker deployment path
  - Remove anti-Docker checks (lines 121-126)
  - Add `--mode [appengine|docker]` argument
  - Support Cloud Run deployment as alternative

- [ ] Add Docker health checks using existing endpoints
  - `/health` - General health check
  - `/ready` - Readiness probe
  - `/live` - Liveness probe
  - Reference: `hermes/main.py`

- [ ] Create Docker-specific environment configuration
  - Document required environment variables
  - Reference `.env.example` for variable list

- [ ] Add documentation for Docker-based development workflow
  - Quick start guide
  - Troubleshooting common issues

### Phase 4: Security & Quality

- [ ] Container passes security scanning (Trivy/Grype)
- [ ] Add Docker image scanning to CI pipeline
- [ ] Document security best practices for Docker deployment

## Acceptance Criteria

- [ ] Developers can run `docker-compose -f docker-compose.dev.yml up` and have full working environment
- [ ] Production Docker image is under 500MB
- [ ] Container passes security scanning with no high/critical vulnerabilities
- [ ] All health checks pass in containerized environment
- [ ] Documentation includes complete Docker setup instructions
- [ ] App Engine remains the primary production deployment method

## Technical References

- Current deployment: `app.yaml`, `deployment/deploy.sh`
- Dependencies: `requirements.txt`
- Environment: `.env.example`
- Health endpoints: `hermes/main.py`

## Notes

- Docker support is for development and optional self-hosted deployments
- App Engine remains the primary production target for SaaS offering
- Self-hosting requires separate licensing consideration
