# Security Configuration Guide

## ⚠️ IMPORTANT: Never Commit Secrets to Git!

This project has been configured to use environment variables for all sensitive data.

## 🔒 Required Environment Variables

### 1. McTime API Configuration
```bash
MCTIME_API_KEY=your-actual-api-key-here
```

### 2. Email/SMTP Configuration
```bash
EMAIL_METHOD=smtp
SMTP_SERVER=email-smtp.eu-west-1.amazonaws.com
SMTP_PORT=587
SMTP_USERNAME=your-actual-smtp-username
SMTP_PASSWORD=your-actual-smtp-password
SENDER_EMAIL=noreply@mctime.com
USE_TLS=true
```

## 📝 Setup Instructions

1. **Copy the example file:**
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` with your actual credentials:**
   ```bash
   nano .env  # or use your preferred editor
   ```

3. **NEVER commit `.env` to git:**
   - The `.gitignore` file is configured to exclude `.env`
   - Only commit `.env.example` with placeholder values

## 🔐 Best Practices

### For Production:
- Use **AWS Secrets Manager** or **Azure Key Vault**
- Use **app-specific passwords** instead of main account passwords
- For Gmail: Generate app password at https://myaccount.google.com/apppasswords
- For AWS SES: Use IAM credentials with minimum required permissions
- Rotate credentials regularly
- Never log passwords or API keys

### For Development:
- Use local `.env` file (already in `.gitignore`)
- Don't share `.env` file via email, chat, or screenshots
- Use different credentials for dev/staging/production

## 🚨 If Credentials Were Exposed

If you accidentally committed credentials to git:

1. **Immediately revoke/rotate the exposed credentials:**
   - AWS SES: Delete the IAM user or regenerate credentials
   - McTime API: Regenerate the API key
   - Email: Change password and regenerate app password

2. **Remove from git history:**
   ```bash
   git filter-branch --force --index-filter \
     "git rm --cached --ignore-unmatch .env" \
     --prune-empty --tag-name-filter cat -- --all
   
   git push origin --force --all
   ```

3. **Add to .gitignore and verify:**
   ```bash
   echo ".env" >> .gitignore
   git add .gitignore
   git commit -m "Add .env to .gitignore"
   git push
   ```

## 📚 Additional Resources

- [OWASP Secrets Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_CheatSheet.html)
- [12-Factor App: Config](https://12factor.net/config)
- [AWS Secrets Manager](https://aws.amazon.com/secrets-manager/)
