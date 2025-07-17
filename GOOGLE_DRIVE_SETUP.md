# 🔗 Google Drive Integration Setup

This guide explains how to set up local Google Drive integration for the Video Trimmer tool.

## 📋 Prerequisites

1. **Google Cloud Console Access**: You need a Google account
2. **Python Dependencies**: Install requirements with `pip install -r requirements.txt`

## 🚀 Step-by-Step Setup

### 1. Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Navigate to "APIs & Services" → "Library"
4. Search for "Google Drive API" and enable it

### 2. Create OAuth2 Credentials

1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "OAuth client ID"
3. Choose "Desktop application" as the application type
4. Give it a name (e.g., "Video Trimmer Local")
5. Click "Create"

### 3. Download Credentials

1. After creating the OAuth client, click the download button (⬇️)
2. Save the downloaded JSON file as `oauth_credentials.json` in the same directory as `app.py`

### 4. First-Time Authentication

1. Run the app: `python app.py`
2. Go to the "☁️ Google Drive" tab
3. Click "🔄 Refresh Drive List"
4. Your web browser will open for authentication
5. Sign in with your Google account
6. Grant permissions to access your Google Drive
7. The app will create an `oauth_token.pickle` file for future use

## 📁 File Structure

After setup, your directory should look like:
```
video-process/
├── app.py
├── trim-convert.sh
├── requirements.txt
├── oauth_credentials.json  ← Your downloaded credentials
├── oauth_token.pickle      ← Auto-generated after first auth
└── ...
```

## 🔒 Security Notes

- **Local Only**: These credentials work only on your local machine
- **Not Shared**: Your `oauth_credentials.json` and `oauth_token.pickle` files are personal
- **Gitignored**: These files are automatically excluded from git commits
- **No Cloud Risk**: This approach avoids the shared credential security issues

## 🎯 Usage

1. **Local Upload Tab**: Upload files directly from your computer
2. **Google Drive Tab**: 
   - Click "🔄 Refresh Drive List" to see your videos
   - Select a video from the dropdown
   - Click "📥 Load Selected Video"
   - Use the trim controls as normal

## 🔧 Troubleshooting

### "Google Drive credentials not found"
- Make sure `oauth_credentials.json` exists in the same directory as `app.py`
- Check that the file is valid JSON

### "No videos found in your Google Drive"
- The app only shows video files (MP4, MOV, AVI, etc.)
- Check that you have video files in your Google Drive

### Authentication expires
- Delete `oauth_token.pickle` and re-authenticate
- The app will automatically prompt for re-authentication when needed

## 🎉 Benefits

- **Private**: Only you can access your Drive files
- **Secure**: No shared credentials or API keys
- **Convenient**: Browse and trim videos directly from Drive
- **Fast**: Downloads only the video you want to trim

---

**Note**: This setup is for local development only. For production deployment, you would need different OAuth configuration.