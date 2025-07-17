# 🚨 Fix "Access Blocked" Error

## The Error You're Seeing:
```
Access blocked: video-trim has not completed the Google verification process
Error 403: access_denied
```

## ✅ Quick Fix (2 minutes):

### Step 1: Configure OAuth Consent Screen
1. Go to **Google Cloud Console**: https://console.cloud.google.com/
2. Select your project
3. Go to **"APIs & Services"** → **"OAuth consent screen"**

### Step 2: Set Up Testing Mode
4. **User Type:** Choose **"External"** (if not already selected)
5. Fill in required fields:
   - **App name:** Video Trimmer
   - **User support email:** nipunbatra0@gmail.com
   - **Developer contact:** nipunbatra0@gmail.com
6. Click **"SAVE AND CONTINUE"**

### Step 3: Skip Scopes
7. **Scopes page:** Just click **"SAVE AND CONTINUE"** (don't add anything)

### Step 4: Add Yourself as Test User
8. **Test users page:** Click **"+ ADD USERS"**
9. Add: **nipunbatra0@gmail.com**
10. Click **"SAVE AND CONTINUE"**

### Step 5: Finish
11. **Summary page:** Click **"BACK TO DASHBOARD"**

---

## 🎯 What This Does:

- **Puts your app in "testing" mode** - bypasses Google verification
- **Adds you as a test user** - allows you to use the app
- **Works immediately** - no waiting for Google approval

---

## 🔄 Now Try Again:

1. **Run your video trimmer app**
2. **Sign in process should work** - no more access blocked error
3. **You'll see a warning** saying "This app isn't verified" - click **"Advanced"** → **"Go to Video Trimmer (unsafe)"**
4. **Grant permissions** and you're done!

---

## 🛡️ Security Note:

- The "unsafe" warning is just because Google hasn't verified the app
- **It's perfectly safe** since you created the app yourself
- This is normal for personal/development apps
- All your data stays private and secure

**This fix works for personal use and testing. For public apps, you'd need Google verification, but that's not needed here!**