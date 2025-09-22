# Email Integration Guide

## Overview
The TGM-Adapter supports multiple email sending methods for maximum flexibility:

1. **Simulation Mode** (default) - For testing
2. **SMTP** - Traditional email servers
3. **SendGrid API** - Professional email service
4. **Mailgun API** - Developer-friendly email service  
5. **Custom Webhook** - Your own email service

## Quick Setup

### 1. Copy Environment Template
```bash
cp .env.example .env
```

### 2. Choose Email Method
Edit `.env` and set `EMAIL_METHOD` to one of:
- `simulate` - Testing mode (default)
- `smtp` - Traditional SMTP
- `sendgrid` - SendGrid API
- `mailgun` - Mailgun API
- `webhook` - Custom webhook

## Configuration Details

### SMTP (Traditional Email)
Best for: Gmail, Outlook, corporate email servers

```bash
EMAIL_METHOD=smtp
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SENDER_EMAIL=your-email@gmail.com
SENDER_PASSWORD=your-app-password
```

**Gmail Setup:**
1. Enable 2-factor authentication
2. Generate an "App Password" 
3. Use the app password, not your regular password

### SendGrid API
Best for: High-volume, reliable delivery

```bash
EMAIL_METHOD=sendgrid
SENDGRID_API_KEY=SG.your-api-key
SENDER_EMAIL=noreply@your-domain.com
```

**Setup:**
1. Create account at https://sendgrid.com
2. Generate API key with "Mail Send" permission
3. Verify your sender domain/email

### Mailgun API
Best for: Developers, easy integration

```bash
EMAIL_METHOD=mailgun
MAILGUN_API_KEY=your-mailgun-api-key
MAILGUN_DOMAIN=your-verified-domain.com
SENDER_EMAIL=noreply@your-verified-domain.com
```

**Setup:**
1. Create account at https://mailgun.com
2. Add and verify your domain
3. Get API key from dashboard

### Custom Webhook
Best for: Integration with existing systems

```bash
EMAIL_METHOD=webhook
EMAIL_WEBHOOK_URL=https://your-service.com/send-email
EMAIL_WEBHOOK_TOKEN=your-auth-token
SENDER_EMAIL=noreply@your-company.com
```

**Webhook Payload:**
```json
{
  "to": "employee@company.com",
  "subject": "Zeiterfassung für Employee Name (2025-09-01 bis 2025-09-03)",
  "html_body": "<html>...</html>",
  "employee_name": "Employee Name",
  "date_from": "2025-09-01",
  "date_to": "2025-09-03",
  "time_entries": [...],
  "token": "your-auth-token"
}
```

**Expected Response:**
- Status 200 for success
- Any other status code will be treated as failure

## Testing

### 1. Start with Simulation
```bash
EMAIL_METHOD=simulate
```
This will log email details without sending.

### 2. Test Real Sending
Set your preferred method and test:
```bash
# Start the application
cd frontend && python app.py

# Send a test email through the web interface
```

## Troubleshooting

### SMTP Issues
- **Gmail**: Use app password, not regular password
- **Corporate**: Check firewall settings for outbound SMTP
- **SSL/TLS**: Verify port (587 for STARTTLS, 465 for SSL)

### API Issues
- **SendGrid**: Verify API key permissions and sender verification
- **Mailgun**: Check domain verification status
- **Rate Limits**: Most services have sending limits

### Webhook Issues
- **URL**: Ensure webhook URL is accessible from server
- **Authentication**: Include proper authorization headers
- **Timeout**: Webhook calls timeout after 30 seconds

## Security Best Practices

1. **Never commit credentials** to version control
2. **Use environment variables** for all sensitive data
3. **Rotate API keys** regularly
4. **Use HTTPS** for webhook endpoints
5. **Validate webhook tokens** in your service

## Example Webhook Service

Here's a simple webhook service example (Node.js):

```javascript
const express = require('express');
const nodemailer = require('nodemailer');
const app = express();

app.use(express.json());

app.post('/send-email', async (req, res) => {
  try {
    const { to, subject, html_body, token } = req.body;
    
    // Verify token
    if (token !== process.env.WEBHOOK_TOKEN) {
      return res.status(401).json({ error: 'Invalid token' });
    }
    
    // Configure your email transport
    const transporter = nodemailer.createTransporter({
      // Your email configuration
    });
    
    // Send email
    await transporter.sendMail({
      from: process.env.SENDER_EMAIL,
      to: to,
      subject: subject,
      html: html_body
    });
    
    res.json({ success: true });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});
```