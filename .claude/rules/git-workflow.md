# Git Workflow Rules

## Commit Messages

### Format
```
<type>(<scope>): <subject>

[body]

[footer]
```

### Types
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Formatting (no code change)
- `refactor`: Code restructuring
- `test`: Adding tests
- `chore`: Maintenance

### Examples
```
feat(auth): add password reset functionality

fix(cart): resolve quantity update race condition

docs(api): update authentication endpoint docs
```

## Branch Naming

### Format
```
<type>/<ticket>-<description>
```

### Examples
```
feature/ABC-123-user-authentication
fix/ABC-456-cart-total-calculation
chore/ABC-789-update-dependencies
```

## Pull Request Process

1. Create feature branch from `main`
2. Make atomic commits
3. Write clear PR description
4. Request review
5. Address feedback
6. Squash and merge

### PR Description Template
```markdown
## Summary
[Brief description of changes]

## Changes
- [Change 1]
- [Change 2]

## Testing
- [ ] Unit tests added
- [ ] Integration tests added
- [ ] Manual testing done

## Screenshots
[If UI changes]
```

## Forbidden

- Force push to `main`/`master`
- Commits without meaningful messages
- Large PRs (> 500 lines)
- Merging without review
- Committing secrets

## Required

- Atomic commits
- PR review before merge
- Tests pass before merge
- Up-to-date with base branch
