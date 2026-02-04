# Security Rules

## Mandatory Checks

### Secrets & Credentials
- NEVER hardcode secrets, API keys, or credentials
- Use environment variables for all sensitive data
- Check for accidental commits of `.env` files
- Scan for common secret patterns before commit

### Input Validation
- Validate ALL user inputs
- Sanitize data before database operations
- Use parameterized queries (prevent SQL injection)
- Escape output for XSS prevention

### Authentication & Authorization
- Implement proper session management
- Use secure password hashing (bcrypt, argon2)
- Check authorization on every protected endpoint
- Implement rate limiting on auth endpoints

### Dependencies
- Keep dependencies updated
- Run `npm audit` regularly
- Review new dependencies before adding
- Pin dependency versions

### Data Protection
- Encrypt sensitive data at rest
- Use HTTPS for all communications
- Implement proper CORS policies
- Set secure cookie flags

## Forbidden Patterns

```javascript
// NEVER DO THIS
const apiKey = "sk-12345...";  // Hardcoded secret
eval(userInput);                // Code injection
`SELECT * FROM users WHERE id = ${id}`;  // SQL injection
element.innerHTML = userInput;  // XSS vulnerability
```

## Required Patterns

```javascript
// DO THIS INSTEAD
const apiKey = process.env.API_KEY;
const result = safeParser(userInput);
db.query("SELECT * FROM users WHERE id = ?", [id]);
element.textContent = userInput;
```
