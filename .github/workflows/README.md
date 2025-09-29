# HERMES GitHub Actions Workflows

This directory contains the streamlined and optimized GitHub Actions workflows for the HERMES Legal AI Platform. The workflows have been consolidated from 7 redundant files into 3 focused, efficient workflows.

## 📋 Workflow Overview

### 🏛️ HERMES Consolidated CI/CD (`consolidated-ci.yml`)
**Primary workflow for continuous integration and deployment**

**Triggers:**
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop` branches
- Manual dispatch with environment selection

**Key Features:**
- **Quality Assurance**: Python testing, linting (Black, Flake8, isort), security scanning
- **Frontend Build**: Node.js build, linting, security auditing
- **Security Integration**: Bandit analysis, dependency vulnerability scanning, secret detection
- **Legal Compliance**: HIPAA/GDPR pattern validation, legal disclaimer checks
- **Deployment**: Automated deployment to both GCP App Engine and GitHub Pages
- **Performance Monitoring**: Lighthouse CI, accessibility validation
- **E2E Testing**: Conditional end-to-end testing with Redis services

**Jobs:**
1. `quality-assurance` - Python testing, linting, security scanning
2. `frontend-build` - Frontend compilation and quality checks
3. `e2e-tests` - End-to-end integration testing (conditional)
4. `deploy-production` - GCP App Engine deployment
5. `deploy-pages` - GitHub Pages deployment
6. `performance-audit` - Lighthouse and accessibility testing
7. `deployment-summary` - Comprehensive status reporting

### 🔒 HERMES Security & Legal Compliance (`security-compliance.yml`)
**Specialized workflow for security auditing and legal compliance**

**Triggers:**
- Weekly schedule (Monday 2 AM and 6 AM UTC)
- Push to `main` branch (documentation changes)
- Manual dispatch with scan type selection

**Key Features:**
- **Advanced Security Auditing**: Bandit, Safety, pip-audit, npm audit
- **Secret Scanning**: Pattern detection for sensitive data and API keys
- **OWASP Security Analysis**: Comprehensive security pattern validation
- **Legal Compliance Validation**: HIPAA, GDPR, attorney-client privilege checks
- **Documentation Generation**: OpenAPI schema and API documentation
- **Compliance Reporting**: Detailed security and legal compliance reports

**Jobs:**
1. `security-audit` - Comprehensive security scanning and analysis
2. `legal-compliance` - Legal industry compliance validation
3. `documentation-generation` - API documentation and legal compliance docs
4. `security-compliance-summary` - Consolidated reporting and alerting

### 📊 HERMES Site Monitoring & Professional Readiness (`monitoring.yml`)
**Continuous monitoring for professional presentation readiness**

**Triggers:**
- Every 30 minutes (continuous uptime monitoring)
- Business hours check (9 AM weekdays)
- After CI/CD workflow completion
- Manual dispatch with monitoring type selection

**Key Features:**
- **Uptime Monitoring**: Multi-point availability checking with detailed metrics
- **Performance Analysis**: Response time, page size, download speed analysis
- **Content Validation**: React app structure, HERMES branding, legal positioning
- **Professional Readiness Assessment**: Suitability for legal industry presentations
- **Legal Industry Positioning**: Compliance messaging and professional language validation
- **Business Hours Alerts**: Professional presentation readiness reports

**Jobs:**
1. `site-monitoring` - Comprehensive uptime and content validation
2. `performance-analysis` - Detailed performance metrics and optimization recommendations
3. `legal-compliance-monitoring` - Legal industry positioning validation
4. `professional-readiness-alert` - Business hours professional readiness assessment
5. `monitoring-summary` - Comprehensive monitoring reports and critical issue alerting

## 🚀 Migration Benefits

### Before: 7 Redundant Workflows
- `ci.yml` - Comprehensive CI with duplicated security scans
- `deploy-production.yml` - GCP deployment with redundant testing
- `docs-compliance.yml` - Legal documentation with duplicated checks
- `main.yml` - Enterprise CI/CD with overlapping functionality
- `pages-validation.yml` - GitHub Pages validation with duplicated monitoring
- `security-monitor.yml` - Security monitoring with overlapping compliance checks
- `site-monitoring.yml` - Site monitoring with redundant validation

### After: 3 Optimized Workflows
- **75% reduction** in workflow files (7 → 3)
- **Eliminated duplicate functionality** across security scanning, testing, and monitoring
- **Improved resource efficiency** through better caching and job dependencies
- **Enhanced maintainability** with centralized configuration and consistent patterns
- **Better error handling** and comprehensive reporting

## 🔧 Configuration

### Environment Variables
```yaml
PYTHON_VERSION: "3.11"
NODE_VERSION: "20"
GCP_PROJECT_ID: hermes-legal-ai
GCP_REGION: us-central1
```

### Required Secrets
- `GCP_SA_KEY` - Google Cloud service account key for deployment
- `OPENAI_API_KEY` - OpenAI API key for testing and E2E tests
- Additional GCP secrets managed through Secret Manager

### Caching Strategy
- **Python dependencies**: `~/.cache/pip`
- **Node.js modules**: `frontend/node_modules`
- **Multi-layered cache keys** for optimal cache hit rates

## 📊 Performance Improvements

### Workflow Execution Time
- **Reduced redundant operations** by consolidating duplicate security scans
- **Optimized job dependencies** to run operations in parallel where possible
- **Improved caching** reduces dependency installation time
- **Conditional execution** prevents unnecessary operations

### Resource Utilization
- **Shared artifacts** between jobs reduce upload/download overhead
- **Consolidated reporting** reduces GitHub Actions compute usage
- **Strategic job dependencies** optimize runner utilization

### Maintenance Overhead
- **Single source of truth** for CI/CD configuration
- **Consistent patterns** across all workflows
- **Centralized error handling** and alerting
- **Unified documentation** and troubleshooting

## 🎯 Professional Readiness Features

The consolidated workflows are specifically optimized for professional legal industry demonstrations:

### Legal Industry Compliance
- **Attorney-client privilege** protection validation
- **HIPAA/GDPR compliance** pattern detection
- **Legal disclaimer** verification and enforcement
- **Professional presentation** language validation

### Business Readiness Monitoring
- **Professional readiness scores** for presentation suitability
- **Business hours alerts** for demonstration preparation
- **Performance benchmarks** suitable for legal industry expectations
- **Comprehensive reporting** for stakeholder communication

### Quality Assurance
- **Enterprise-grade security** scanning and validation
- **Legal tech specific** compliance checks
- **Professional presentation** optimization
- **Comprehensive monitoring** and alerting

## 🔍 Troubleshooting

### Common Issues
1. **Dependency Installation Failures**: Check requirements.txt and package.json for conflicts
2. **Security Scan False Positives**: Review bandit configuration in pyproject.toml
3. **Deployment Failures**: Verify GCP secrets and project configuration
4. **Performance Issues**: Review Lighthouse CI configuration in .lighthouserc.json

### Debugging Tips
- Monitor workflow run logs for detailed error information
- Check artifact uploads for security and compliance reports
- Review job dependencies and conditional execution logic
- Validate YAML syntax before committing workflow changes

## 📚 Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Google Cloud App Engine Deployment](https://cloud.google.com/appengine/docs/standard/python3/deploying-your-app)
- [Lighthouse CI Configuration](https://github.com/GoogleChrome/lighthouse-ci)
- [Legal Technology Compliance Best Practices](https://www.americanbar.org/groups/departments_offices/legal_technology_resources/)

---

*This consolidated workflow structure supports HERMES as a professional legal technology platform ready for enterprise legal industry demonstrations and client presentations.*