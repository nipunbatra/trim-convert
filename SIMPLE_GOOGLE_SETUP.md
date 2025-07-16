# 🚀 Super Simple Google Drive Setup (3 Steps)

## Overview
This is the easiest way to integrate Google Drive - just like signing into any Google app!

---

## Step 1: Create OAuth App (5 minutes, one-time)

### 1.1 Go to Google Cloud Console
- Open: **https://console.cloud.google.com/**
- Sign in with your Google account

### 1.2 Create/Select Project
- Click **"Select a project"** → **"NEW PROJECT"**
- Name: `video-trimmer` → Click **"CREATE"**

### 1.3 Enable Google Drive API
- Go to **"APIs & Services"** → **"Library"**
- Search: **"Google Drive API"** → Click it → **"ENABLE"**

### 1.4 Configure OAuth Consent Screen (Important!)
- Go to **"APIs & Services"** → **"OAuth consent screen"**
- **User Type:** Choose **"External"** → Click **"CREATE"**
- **App name:** Video Trimmer
- **User support email:** Your email (nipunbatra0@gmail.com)
- **Developer contact information:** Your email
- Click **"SAVE AND CONTINUE"**
- **Scopes:** Click **"SAVE AND CONTINUE"** (don't add any)
- **Test users:** Click **"+ ADD USERS"** → Add **nipunbatra0@gmail.com** → **"SAVE AND CONTINUE"**
- **Summary:** Click **"BACK TO DASHBOARD"**

### 1.5 Create OAuth Credentials  
- Go to **"APIs & Services"** → **"Credentials"**
- Click **"+ CREATE CREDENTIALS"** → **"OAuth 2.0 Client IDs"**
- **Application type:** Desktop application
- **Name:** Video Trimmer (or any name)
- Click **"CREATE"**

### 1.6 Download Credentials
- Click **"DOWNLOAD JSON"** button
- **Rename the file to:** `oauth_credentials.json`
- **Move it to this directory** (where video_trimmer_demo.py is)

---

## Step 2: Run the App
```bash
python video_trimmer_demo.py
```

---

## Step 3: Sign In (first time only)
- App will **open your browser automatically**
- **Sign in with your Google account**
- **Click "Allow"** to grant Drive access
- **Done!** Browser will close and app is ready

---

## 🎉 How It Works

### **Loading Videos:**
1. Click **"🔄 Load Videos from Google Drive"**
2. **Browse ALL your Google Drive videos**
3. **Select any video** → Click **"📥 Download & Load Video"**
4. **Video appears automatically** in the player

### **Uploading Results:**
1. **Check "📤 Upload trimmed files to Google Drive"**
2. **Optionally choose a folder** (or use root Drive folder)
3. **Trim your video as normal**
4. **Files automatically upload** to your Google Drive

---

## ✅ Benefits

- **🔐 Use your own Google account** - no complex setup
- **📁 Access ALL your files** - entire Google Drive available
- **📤 Upload anywhere** - choose any folder
- **🔄 Works like Google apps** - familiar OAuth login
- **🛡️ Secure** - standard Google authentication

---

## 🔧 Troubleshooting

### "oauth_credentials.json not found"
- Make sure you downloaded and renamed the file correctly
- Place it in the same folder as `video_trimmer_demo.py`

### Browser doesn't open for login
- Copy the URL from terminal and paste in browser manually
- Make sure you're on the computer where the app is running

### "No videos found"
- Make sure you have video files in your Google Drive
- Check file formats: MP4, MOV, AVI, MKV

---

## 🔒 Security

- **Your credentials stay on your computer**
- **You control what the app can access**
- **Revoke access anytime** in Google Account settings
- **No sharing required** - works with private files

**Total setup time: 5 minutes once, then just sign in and go!**