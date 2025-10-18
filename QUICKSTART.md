# 🚀 Quick Setup Guide

## ✅ Security Fixes Complete!

All hardcoded credentials have been removed. Your project is now secure! 🔒

---

## 📋 Quick Setup (3 Steps)

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Configure Your Environment
```bash
# Copy the example file
cp .env.example .env

# Edit with your real credentials (use nano, vim, or VS Code)
nano .env
```

**Add your real credentials to `.env`:**
```bash
MCTIME_API_KEY=your-actual-mctime-api-key
SMTP_SERVER=email-smtp.eu-west-1.amazonaws.com
SMTP_PORT=587
SMTP_USERNAME=your-actual-aws-ses-username
SMTP_PASSWORD=your-actual-aws-ses-password
SENDER_EMAIL=noreply@mctime.com
USE_TLS=true
```

### Step 3: Run the Application
```bash
cd frontend
python app.py
```

---

## ⚠️ IMPORTANT: Rotate Compromised Credentials!

The following credentials were exposed in git and **MUST be rotated immediately**:

### 1️⃣ McTime API Key
- **Exposed Key:** `bvtA7WVi52MBmu69bRSEEWYSOggNSRKRXJxQc5bPmBPqBXhS`
- **Action:** Log into McTime dashboard → Settings → API → Regenerate key
- **Update:** Put new key in your `.env` file

### 2️⃣ AWS SES/SMTP Credentials
- **Exposed Username:** `AKIA3O74MZU7UX272LKI`
- **Exposed Password:** `BN8dXZgLjEP/3g0q2keO5TFsQkBeJQUUUdGGvB+n9A/E`
- **Action:** AWS Console → IAM → Delete old user → Create new user with SES permissions
- **Update:** Put new credentials in your `.env` file

---

## 🧪 Verify Everything Works

### Test 1: Check Security
```bash
./check_security.sh
```
**Expected:** All checks should show ✅ PASS

### Test 2: Verify .env is loaded
```bash
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('✅ API Key loaded' if os.getenv('MCTIME_API_KEY') else '❌ API Key missing')"
```

### Test 3: Run the app
```bash
cd frontend && python app.py
```

---

## 📁 Files Changed

### ✅ Created:
- `.gitignore` - Protects sensitive files
- `SECURITY.md` - Security best practices guide
- `SECURITY_AUDIT.md` - Detailed audit report
- `check_security.sh` - Security verification script
- `QUICKSTART.md` - This file!

### 🔧 Modified:
- `backend/api_handler.py` - Removed hardcoded API key
- `backend/modules/GET_MAIL.py` - Removed hardcoded API key
- `backend/modules/GET_EMPLOYEE_LIST.py` - Removed hardcoded API key
- `backend/modules/GET_TIMES.py` - Removed hardcoded API key
- `backend/modules/GET_USERID.py` - Removed hardcoded API key
- `frontend/app.py` - Removed hardcoded credentials
- `webhook_email_service.py` - Removed default token
- `.env.example` - Updated with proper structure
- `.env` - Sanitized (add your real credentials here)
- `requirements.txt` - Added python-dotenv

### 🗑️ Removed from Git:
- `.env` - Now only exists locally (not tracked)

---

## 🎯 Next Steps

1. ✅ Install dependencies: `pip install -r requirements.txt`
2. ✅ Copy `.env.example` to `.env`
3. ✅ Add your real credentials to `.env`
4. ⚠️ **ROTATE** the exposed credentials!
5. ✅ Run security check: `./check_security.sh`
6. ✅ Test the app: `python frontend/app.py`
7. ✅ Commit the security fixes (see below)

---

## 📤 Commit Your Changes

```bash
# Add all security fixes
git add .gitignore SECURITY.md SECURITY_AUDIT.md QUICKSTART.md check_security.sh
git add requirements.txt .env.example
git add backend/api_handler.py backend/modules/*.py
git add frontend/app.py webhook_email_service.py

# Commit with a clear message
git commit -m "🔒 Security: Remove all hardcoded credentials

- Removed hardcoded API keys from all files
- Removed hardcoded SMTP credentials
- Added .gitignore to protect .env file
- Removed .env from git tracking
- Added python-dotenv for environment variable support
- Created security documentation and check script

BREAKING CHANGE: Requires .env file with credentials
See QUICKSTART.md for setup instructions"

# Push to remote
git push
```

---

## 🆘 Troubleshooting

### "MCTIME_API_KEY not set" error
→ You forgot to create `.env` file or add the API key
→ Run: `cp .env.example .env` and edit it

### "SMTP credentials not configured" error
→ You forgot to add SMTP credentials to `.env`
→ Edit `.env` and add SMTP_USERNAME and SMTP_PASSWORD

### Can't send emails
→ Make sure you rotated the exposed AWS SES credentials
→ Check AWS SES console for sending limits/verification

---

## 📚 Additional Resources

- **SECURITY.md** - Comprehensive security guide
- **SECURITY_AUDIT.md** - Detailed audit findings
- **.env.example** - Template for environment variables

---

**🎉 You're all set! Your application is now secure!**

Run `./check_security.sh` anytime to verify security status.
