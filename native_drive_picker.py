"""
Native Google Drive Picker - uses Google's built-in file picker interface
Much simpler than building our own browser
"""

import os
import tempfile
import logging
import webbrowser
from typing import Optional, Dict

try:
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseDownload
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    import io
    GOOGLE_DRIVE_AVAILABLE = True
except ImportError:
    GOOGLE_DRIVE_AVAILABLE = False

logger = logging.getLogger(__name__)

# OAuth scopes
SCOPES = ['https://www.googleapis.com/auth/drive']

class GoogleDrivePickerManager:
    """Simple Google Drive manager with native picker links"""
    
    def __init__(self, credentials_file: str = "oauth_credentials.json", token_file: str = "oauth_token.pickle"):
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.service = None
        self.authenticated = False
        
        if not GOOGLE_DRIVE_AVAILABLE:
            logger.warning("Google Drive API libraries not available")
            return
            
        self._authenticate()
    
    def _authenticate(self) -> bool:
        """Authenticate with Google Drive using OAuth"""
        try:
            import pickle
            
            creds = None
            
            # Load existing token
            if os.path.exists(self.token_file):
                with open(self.token_file, 'rb') as token:
                    creds = pickle.load(token)
            
            # If there are no valid credentials, let user log in
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    try:
                        creds.refresh(Request())
                    except Exception as e:
                        logger.warning(f"Token refresh failed: {e}")
                        creds = None
                
                if not creds:
                    if not os.path.exists(self.credentials_file):
                        logger.error(f"OAuth credentials file not found: {self.credentials_file}")
                        return False
                    
                    flow = InstalledAppFlow.from_client_secrets_file(self.credentials_file, SCOPES)
                    creds = flow.run_local_server(port=0, prompt='consent')
                
                # Save credentials for next time
                with open(self.token_file, 'wb') as token:
                    pickle.dump(creds, token)
            
            self.service = build('drive', 'v3', credentials=creds)
            self.authenticated = True
            logger.info("✅ Google Drive OAuth authentication successful")
            return True
            
        except Exception as e:
            logger.error(f"❌ Google Drive OAuth authentication failed: {e}")
            return False
    
    def is_available(self) -> bool:
        """Check if Google Drive integration is available"""
        return GOOGLE_DRIVE_AVAILABLE and self.authenticated
    
    def get_user_info(self) -> Optional[str]:
        """Get current user's email"""
        if not self.is_available():
            return None
        
        try:
            about = self.service.about().get(fields="user").execute()
            user = about.get('user', {})
            return user.get('emailAddress', 'Unknown user')
        except Exception as e:
            logger.error(f"Error getting user info: {e}")
            return None
    
    def open_drive_picker(self, picker_type: str = "file") -> str:
        """Open Google Drive in browser for file/folder selection"""
        if picker_type == "file":
            # URL to open Google Drive - full access to all files
            drive_url = "https://drive.google.com/drive/my-drive"
            instruction = """
📁 **Google Drive File Picker Instructions:**

1. **Google Drive opens** in your browser
2. **Browse your entire Google Drive** - navigate any folder
3. **Find your video file** (MP4, MOV, AVI, MKV, etc.)
4. **Right-click the file** → **"Share"** → **"Get link"**
5. **Set to "Anyone with the link can view"** → **"Copy link"**
6. **Paste the link** in the field below

The link looks like: `https://drive.google.com/file/d/FILE_ID/view`

**💡 Tip:** You can navigate through all folders, search, and pick any video file!
"""
        else:
            # URL to open Google Drive for folder navigation
            drive_url = "https://drive.google.com/drive/my-drive"
            instruction = """
📂 **Google Drive Folder Picker Instructions:**

1. **Google Drive opens** in your browser
2. **Navigate to your desired upload folder**
   - Browse through your folder structure
   - Or create a new folder: **New** → **Folder**
3. **Right-click the folder** → **"Share"** → **"Get link"**
4. **Set to "Anyone with the link can view"** → **"Copy link"**
5. **Paste the folder link** in the field below
6. **Leave empty** to upload to My Drive root

The link looks like: `https://drive.google.com/drive/folders/FOLDER_ID`

**💡 Tip:** You can create new folders or pick any existing folder!
"""
        
        try:
            webbrowser.open(drive_url)
            logger.info(f"🌐 Opened Google Drive in browser for {picker_type} selection")
        except Exception as e:
            logger.warning(f"Could not open browser: {e}")
            instruction += f"\n\n**Manual:** Go to {drive_url}"
        
        return instruction
    
    def extract_file_id_from_url(self, drive_url: str) -> Optional[str]:
        """Extract Google Drive file/folder ID from URL"""
        if not drive_url:
            return None
        
        import re
        
        # Various Google Drive URL patterns
        patterns = [
            r'/file/d/([a-zA-Z0-9_-]+)',      # File links
            r'/folders/([a-zA-Z0-9_-]+)',     # Folder links
            r'id=([a-zA-Z0-9_-]+)',           # Old format
            r'/open\?id=([a-zA-Z0-9_-]+)',    # Another format
        ]
        
        for pattern in patterns:
            match = re.search(pattern, drive_url)
            if match:
                return match.group(1)
        
        # If URL looks like just an ID
        if re.match(r'^[a-zA-Z0-9_-]+$', drive_url.strip()):
            return drive_url.strip()
        
        return None
    
    def download_file_from_url(self, drive_url: str, custom_filename: str = None) -> tuple[Optional[str], str]:
        """Download file from Google Drive URL"""
        if not self.is_available():
            return None, "❌ Google Drive not available"
        
        file_id = self.extract_file_id_from_url(drive_url)
        if not file_id:
            return None, "❌ Could not extract file ID from URL"
        
        try:
            # Get file info
            file_info = self.service.files().get(
                fileId=file_id,
                fields="id,name,size,mimeType"
            ).execute()
            
            filename = custom_filename or file_info.get('name', f'gdrive_file_{file_id}')
            
            # Log file type info
            mime_type = file_info.get('mimeType', '')
            if mime_type.startswith('video/'):
                logger.info(f"✅ Video file detected: {mime_type}")
            else:
                logger.info(f"📄 File type: {mime_type} (not a video - but that's ok!)")
            
            # Download file
            temp_dir = tempfile.gettempdir()
            local_path = os.path.join(temp_dir, filename)
            
            request = self.service.files().get_media(fileId=file_id)
            fh = io.FileIO(local_path, 'wb')
            downloader = MediaIoBaseDownload(fh, request)
            
            done = False
            while done is False:
                status, done = downloader.next_chunk()
                if status:
                    logger.info(f"📥 Download progress: {int(status.progress() * 100)}%")
            
            fh.close()
            
            file_size_mb = os.path.getsize(local_path) / (1024 * 1024)
            logger.info(f"✅ Downloaded: {filename} ({file_size_mb:.1f} MB)")
            
            return local_path, f"✅ Downloaded: {filename} ({file_size_mb:.1f} MB)"
            
        except Exception as e:
            logger.error(f"Error downloading file: {e}")
            return None, f"❌ Download failed: {str(e)}"
    
    def upload_file_to_folder(self, file_path: str, folder_url: str = None) -> tuple[bool, str]:
        """Upload file to Google Drive folder"""
        if not self.is_available():
            return False, "❌ Google Drive not available"
        
        try:
            # Determine folder ID
            folder_id = None
            if folder_url:
                folder_id = self.extract_file_id_from_url(folder_url)
            
            # Prepare file metadata
            file_name = os.path.basename(file_path)
            file_metadata = {
                'name': file_name,
                'parents': [folder_id] if folder_id else []
            }
            
            # Determine MIME type
            if file_path.endswith('.mp4'):
                mime_type = 'video/mp4'
            elif file_path.endswith('.aac'):
                mime_type = 'audio/aac'
            elif file_path.endswith('.mp3'):
                mime_type = 'audio/mpeg'
            else:
                mime_type = None
            
            # Upload file
            from googleapiclient.http import MediaFileUpload
            media = MediaFileUpload(file_path, mimetype=mime_type, resumable=True)
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id,name,webViewLink'
            ).execute()
            
            file_id = file.get('id')
            file_name = file.get('name')
            web_link = file.get('webViewLink')
            
            logger.info(f"✅ Uploaded: {file_name}")
            
            return True, f"✅ Uploaded: {file_name}\n🔗 Link: {web_link}"
            
        except Exception as e:
            logger.error(f"Error uploading file: {e}")
            return False, f"❌ Upload failed: {str(e)}"


def get_native_picker_instructions() -> str:
    """Get instructions for using native Google Drive picker"""
    return """
## 🎯 Google Drive Native Picker

### Why This is Better:
- ✅ **Use Google's own interface** - familiar and reliable
- ✅ **No complex browsing code** - just paste links
- ✅ **Works with any file** - private or shared
- ✅ **Simple setup** - same OAuth as before

### How It Works:

#### 📥 **Loading Videos:**
1. Click **"Open Google Drive Video Picker"**
2. **Google Drive opens** in your browser (filtered for videos)
3. **Select your video** → Right-click → **"Get link"**
4. **Copy the link** and paste it in the app
5. **Download & load** - video appears in trimmer

#### 📤 **Uploading Results:**
1. Click **"Choose Upload Folder"** (optional)
2. **Google Drive opens** → Navigate to desired folder
3. **Copy folder link** and paste it
4. **Trim your video** with upload enabled
5. **Files automatically upload** to chosen folder

### Benefits:
- **No custom file browser** - uses Google's proven interface
- **Works everywhere** - any device with a browser
- **Familiar UI** - everyone knows how to use Google Drive
- **Always up-to-date** - uses Google's latest interface
"""