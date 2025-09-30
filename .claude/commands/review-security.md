Perform a comprehensive security review of the current changes:

1. **Scan for hardcoded secrets** in all modified files
2. **Check data handling** for attorney-client privilege violations
3. **Verify encryption** is used for sensitive data (voice, client info)
4. **Review input validation** for SQL injection, XSS vulnerabilities
5. **Audit logging** - ensure all sensitive operations are logged
6. **API security** - check authentication, authorization, rate limiting
7. **Third-party dependencies** - identify any new dependencies with known CVEs

For each issue found, provide:
- Severity: P0 (Blocker), P1 (Critical), P2 (Important), P3 (Minor)
- Location: File and line number
- Description: What's wrong
- Recommendation: How to fix it
- Reference: Link to relevant security standard (OWASP, HIPAA, etc.)

Focus on HERMES-specific compliance requirements:
- HIPAA BAA compliance
- Attorney-client privilege protection  
- GDPR data handling
- SOC 2 control requirements