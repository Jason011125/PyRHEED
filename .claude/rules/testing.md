# Testing Rules

## Coverage Requirements

- **Minimum coverage**: 80%
- **Critical paths**: 100%
- **New code**: Must include tests

## Test-Driven Development

### TDD Cycle
1. **RED**: Write failing test first
2. **GREEN**: Minimal code to pass
3. **REFACTOR**: Clean up, keep tests green

### When to Use TDD
- New features
- Bug fixes (write test that reproduces bug first)
- Refactoring (tests as safety net)

## Test Structure

### Naming Convention
```
[unit].[method].[scenario].[expected]
```

### AAA Pattern
```typescript
describe('UserService', () => {
  describe('createUser', () => {
    it('should return user with generated id when valid data provided', () => {
      // Arrange
      const userData = { name: 'John', email: 'john@example.com' };

      // Act
      const result = userService.createUser(userData);

      // Assert
      expect(result.id).toBeDefined();
      expect(result.name).toBe('John');
    });
  });
});
```

## Test Types

### Unit Tests
- Test individual functions/methods
- Mock external dependencies
- Fast execution (< 100ms each)

### Integration Tests
- Test component interactions
- Real database (test instance)
- API endpoint testing

### E2E Tests
- Full user flows
- Browser automation (Playwright)
- Critical paths only

## Forbidden

- Tests without assertions
- Tests that depend on other tests
- Flaky tests (fix immediately)
- Skipped tests without TODO comment
- Testing implementation details

## Required

- Tests for all bug fixes
- Tests for new features
- Meaningful test descriptions
- Clean test data (no shared state)
