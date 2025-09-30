Generate comprehensive tests for the code in $ARGUMENTS:

1. **Unit Tests** (pytest)
   - Test all public functions
   - Cover happy path and edge cases
   - Include error handling tests
   - Target 80%+ coverage
   
2. **Integration Tests**
   - Test API endpoints
   - Test external integrations (Clio, LawPay)
   - Use mocked external services
   
3. **Test Fixtures**
   - Create realistic test data
   - Include edge cases (empty, null, special chars)
   - Legal-domain specific examples
   
4. **Async Test Patterns**
   - Use @pytest.mark.asyncio
   - Properly await all async calls
   - Clean up resources in fixtures

Generate tests in the appropriate test directory (`tests/unit/`, `tests/integration/`).
Follow HERMES testing standards from CLAUDE.md.
Use descriptive test names that explain what's being tested.