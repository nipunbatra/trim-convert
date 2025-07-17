#!/usr/bin/env python3

import gradio as gr
import subprocess
import os
import tempfile
import shutil
import logging
import time
from pathlib import Path
import pickle
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Google Drive configuration
SCOPES = ['https://www.googleapis.com/auth/drive.file']
TOKEN_FILE = 'oauth_token.pickle'
CREDENTIALS_FILE = 'oauth_credentials.json'

def get_google_drive_service():
    """Get Google Drive service with local OAuth credentials"""
    creds = None
    
    # Check if token file exists
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'rb') as token:
            creds = pickle.load(token)
    
    # If no valid credentials, authenticate
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDENTIALS_FILE):
                logger.warning("⚠️ Google Drive credentials file not found. Local Google Drive integration disabled.")
                return None
            
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save credentials for next run
        with open(TOKEN_FILE, 'wb') as token:
            pickle.dump(creds, token)
    
    return build('drive', 'v3', credentials=creds)

def list_drive_videos(service, folder_id=None):
    """List video files from Google Drive"""
    try:
        query = "mimeType contains 'video/'"
        if folder_id:
            query += f" and '{folder_id}' in parents"
        
        results = service.files().list(
            q=query,
            pageSize=50,
            fields="nextPageToken, files(id, name, size, mimeType, parents)"
        ).execute()
        
        items = results.get('files', [])
        return items
    except Exception as e:
        logger.error(f"❌ Error listing Drive videos: {e}")
        return []

def extract_drive_file_id(input_str):
    """Extract file ID from Drive link or return input if it's already a file ID"""
    import re
    
    # Check if it's a Drive link
    drive_link_patterns = [
        r'https://drive\.google\.com/file/d/([a-zA-Z0-9-_]+)',
        r'https://drive\.google\.com/open\?id=([a-zA-Z0-9-_]+)',
        r'https://docs\.google\.com/file/d/([a-zA-Z0-9-_]+)'
    ]
    
    for pattern in drive_link_patterns:
        match = re.search(pattern, input_str)
        if match:
            return match.group(1)
    
    # Check if it's already a file ID (alphanumeric string)
    if re.match(r'^[a-zA-Z0-9-_]+$', input_str.strip()):
        return input_str.strip()
    
    return None

def download_from_drive(service, file_id, filename):
    """Download a file from Google Drive"""
    try:
        request = service.files().get_media(fileId=file_id)
        
        # Create temporary file
        temp_dir = tempfile.mkdtemp()
        temp_file = os.path.join(temp_dir, filename)
        
        with open(temp_file, 'wb') as fh:
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()
                if status:
                    logger.info(f"📥 Download progress: {int(status.progress() * 100)}%")
        
        logger.info(f"✅ Downloaded: {filename}")
        return temp_file
    except Exception as e:
        logger.error(f"❌ Error downloading from Drive: {e}")
        return None

def load_video_from_path_or_drive(input_path):
    """Load video from local path or Google Drive"""
    if not input_path:
        return None, "Please enter a file path or Drive link"
    
    # Check if it's a local file path
    if os.path.exists(input_path):
        return input_path, f"✅ Local file: {os.path.basename(input_path)}"
    
    # Try to extract Drive file ID
    file_id = extract_drive_file_id(input_path)
    if file_id:
        try:
            service = get_google_drive_service()
            if not service:
                return None, "❌ Google Drive service not available. Check oauth_credentials.json"
            
            # Get file info
            file_info = service.files().get(fileId=file_id).execute()
            filename = file_info['name']
            
            # Download file
            temp_file = download_from_drive(service, file_id, filename)
            if temp_file:
                return temp_file, f"✅ Downloaded from Drive: {filename}"
            else:
                return None, f"❌ Failed to download from Drive"
        except Exception as e:
            logger.error(f"❌ Error loading from Drive: {e}")
            return None, f"❌ Drive error: {str(e)}"
    
    return None, f"❌ Invalid path or Drive link: {input_path}"

def process_video_trim(video_file, start_time, end_time):
    """Process video trimming using the trim-convert.sh script"""
    logger.info(f"🎬 Starting trim process: file={video_file}, start={start_time}, end={end_time}")
    
    if not video_file or start_time is None or end_time is None:
        error_msg = "Please provide video file and both start/end times"
        logger.error(f"❌ {error_msg}")
        return None, None, None, error_msg
    
    try:
        start_seconds = float(start_time)
        end_seconds = float(end_time)
        
        logger.info(f"📊 Parsed times: start={start_seconds}s, end={end_seconds}s")
        
        if start_seconds >= end_seconds:
            error_msg = "Start time must be less than end time"
            logger.error(f"❌ {error_msg}")
            return None, None, None, error_msg
        
        if not os.path.exists(video_file):
            error_msg = f"Input video file not found: {video_file}"
            logger.error(f"❌ {error_msg}")
            return None, None, None, error_msg
        
        # Create temporary directory for output
        temp_dir = tempfile.mkdtemp()
        logger.info(f"📁 Created temp directory: {temp_dir}")
        
        # Get the base filename without extension
        base_name = Path(video_file).stem
        output_prefix = os.path.join(temp_dir, f"{base_name}_trimmed")
        
        # The script will create these files based on the prefix
        output_video = f"{output_prefix}.mp4"
        output_audio = f"{output_prefix}.aac"
        
        logger.info(f"📤 Output files will be: video={output_video}, audio={output_audio}")
        
        # Check if trim-convert.sh script exists
        script_path = "./trim-convert.sh"
        if not os.path.exists(script_path):
            error_msg = f"trim-convert.sh script not found at: {script_path}"
            logger.error(f"❌ {error_msg}")
            return None, None, None, error_msg
        
        # Convert seconds to HH:MM:SS format for the script
        def seconds_to_time(seconds):
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            secs = seconds % 60
            return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"
        
        start_time_str = seconds_to_time(start_seconds)
        end_time_str = seconds_to_time(end_seconds)
        
        logger.info(f"🕒 Converted times: start={start_time_str}, end={end_time_str}")
        
        # Call the trim-convert.sh script with proper format
        cmd = [
            "bash", script_path,
            "-s", start_time_str,
            "-e", end_time_str, 
            "-o", output_prefix,
            video_file
        ]
        
        logger.info(f"🚀 Running command: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, capture_output=True, text=True, cwd='.')
        
        logger.info(f"📋 Command finished with return code: {result.returncode}")
        logger.info(f"📤 STDOUT: {result.stdout}")
        if result.stderr:
            logger.warning(f"⚠️  STDERR: {result.stderr}")
        
        if result.returncode == 0:
            # Check if files were created
            video_exists = os.path.exists(output_video)
            audio_exists = os.path.exists(output_audio)
            
            logger.info(f"📁 File check: video_exists={video_exists}, audio_exists={audio_exists}")
            
            if video_exists and audio_exists:
                success_msg = f"✅ Successfully trimmed video from {start_seconds:.1f}s to {end_seconds:.1f}s"
                logger.info(success_msg)
                return output_video, output_audio, output_audio, success_msg
            else:
                error_msg = f"❌ Output files not created.\n\nScript STDOUT:\n{result.stdout}\n\nScript STDERR:\n{result.stderr}"
                logger.error(error_msg)
                return None, None, None, error_msg
        else:
            error_msg = f"❌ trim-convert.sh failed with return code {result.returncode}\n\nSTDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}"
            logger.error(error_msg)
            return None, None, None, error_msg
            
    except Exception as e:
        error_msg = f"❌ Unexpected error: {str(e)}"
        logger.exception(error_msg)
        return None, None, None, error_msg

def get_video_duration(video_file):
    """Get video duration in seconds"""
    if not video_file:
        return 0
    
    try:
        logger.info(f"📺 Getting duration for: {video_file}")
        
        cmd = [
            "ffprobe", "-v", "quiet", "-print_format", "json", 
            "-show_format", "-show_streams", video_file
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            import json
            data = json.loads(result.stdout)
            duration = float(data['format']['duration'])
            logger.info(f"⏱️ Video duration: {duration} seconds")
            return duration
        else:
            logger.warning(f"⚠️ Could not get duration: {result.stderr}")
            return 0
    except Exception as e:
        logger.exception(f"❌ Error getting video duration: {e}")
        return 0

def format_time(seconds):
    """Format seconds to mm:ss"""
    if seconds is None:
        return "0:00"
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes}:{secs:02d}"

def get_video_info(video_file):
    """Get video duration and basic info"""
    if not video_file:
        return "No video uploaded", 0, 0, 0
    
    logger.info(f"📹 Processing video upload: {video_file}")
    
    duration = get_video_duration(video_file)
    if duration > 0:
        minutes = int(duration // 60)
        seconds = int(duration % 60)
        info = f"📹 Video loaded! Duration: {minutes}:{seconds:02d} ({duration:.1f}s)"
        logger.info(f"✅ {info}")
        return info, duration, 0, duration
    else:
        info = "📹 Video loaded! (Could not determine duration)"
        logger.warning(f"⚠️ {info}")
        return info, 100, 0, 100

# Create the Gradio interface
custom_css = """
.video-container video {
    width: 100%;
    max-height: 400px;
}
.slider-container {
    margin: 10px 0;
}
.video-controls {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-top: 10px;
    padding: 10px;
    background: #f5f5f5;
    border-radius: 8px;
}
.control-button {
    padding: 8px 16px;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 14px;
}
.play-button {
    background: #4CAF50;
    color: white;
}
.pause-button {
    background: #f44336;
    color: white;
}
.seek-button {
    background: #2196F3;
    color: white;
}
.time-display {
    font-family: monospace;
    font-size: 14px;
    color: #333;
    min-width: 100px;
}
"""

with gr.Blocks(title="Video Trimmer Tool", theme=gr.themes.Soft(), css=custom_css, head="""
<script>
// Enhanced video controls
function seekVideo(time) {
    const videos = document.querySelectorAll('video');
    videos.forEach(video => {
        if (video.src && video.readyState >= 2) {
            video.currentTime = time;
        }
    });
}

function playVideo() {
    const videos = document.querySelectorAll('video');
    videos.forEach(video => {
        if (video.src && video.readyState >= 2) {
            video.play();
        }
    });
}

function pauseVideo() {
    const videos = document.querySelectorAll('video');
    videos.forEach(video => {
        if (video.src && video.readyState >= 2) {
            video.pause();
        }
    });
}

function getCurrentTime() {
    const videos = document.querySelectorAll('video');
    for (let video of videos) {
        if (video.src && video.readyState >= 2) {
            return video.currentTime;
        }
    }
    return 0;
}

function updateVideoSeek() {
    const startSlider = document.querySelector('input[type="range"]');
    const endSlider = document.querySelectorAll('input[type="range"]')[1];
    
    if (startSlider && endSlider) {
        startSlider.addEventListener('input', (e) => {
            seekVideo(parseFloat(e.target.value));
        });
        
        endSlider.addEventListener('input', (e) => {
            seekVideo(parseFloat(e.target.value));
        });
    }
}

// Initialize after DOM loads
document.addEventListener('DOMContentLoaded', updateVideoSeek);
// Also try after a delay for dynamic content
setTimeout(updateVideoSeek, 2000);
</script>
""") as demo:
    gr.Markdown("""
    # 🎬 Video Trimmer Tool - Local Edition with Google Drive
    Upload a video file or select from Google Drive, set trim points using the sliders, and get both trimmed video and extracted audio files.
    
    **Features:**
    - ✂️ **Precise trimming** with visual sliders
    - 🎵 **Audio extraction** (AAC format)
    - 🚀 **Fast processing** using your proven trim-convert.sh script
    - 📁 **Local files** + **Google Drive integration** with your own credentials
    
    **Supported formats:** MP4, MOV, AVI, MKV
    """)
    
    # Input Source Selection
    with gr.Tab("📁 Input Source"):
        with gr.Row():
            with gr.Column():
                gr.Markdown("### 📂 Local File Upload")
                local_video_input = gr.File(
                    label="📁 Upload Video File",
                    file_types=[".mp4", ".mov", ".avi", ".mkv"],
                    type="filepath"
                )
                
                local_load_btn = gr.Button("📥 Load Local Video", variant="primary")
            
            with gr.Column():
                gr.Markdown("### ☁️ Google Drive / Remote Path")
                gr.Markdown("**💡 Supports:**")
                gr.Markdown("- Local paths: `/path/to/video.mp4`")
                gr.Markdown("- Drive links: `https://drive.google.com/file/d/FILE_ID/view`")
                gr.Markdown("- Drive file IDs: `1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74mMjoeAiGQ`")
                
                remote_video_input = gr.Textbox(
                    label="📹 Video Path or Drive Link",
                    placeholder="Enter file path, Drive link, or file ID",
                    lines=1,
                    max_lines=1
                )
                
                remote_load_btn = gr.Button("📥 Load Remote Video", variant="primary")
                browse_drive_btn = gr.Button("📂 Browse Drive", variant="secondary")
        
        # Universal status display
        load_status = gr.Textbox(
            label="📝 Load Status",
            interactive=False,
            value="Select a video source above"
        )
    
    # Unified Video Player and Controls
    with gr.Tab("🎬 Video Player & Trimmer"):
        with gr.Row():
            with gr.Column(scale=3):
                # Main video player
                main_video_player = gr.Video(
                    label="🎥 Video Player",
                    show_label=True,
                    elem_id="main_video_player",
                    elem_classes=["video-container"]
                )
                
                # Integrated video controls
                with gr.Row():
                    play_btn = gr.Button("▶️ Play", variant="success", size="sm")
                    pause_btn = gr.Button("⏸️ Pause", variant="secondary", size="sm")
                    seek_current_btn = gr.Button("📍 Seek to Current", variant="info", size="sm")
                
                # Video scrubber
                gr.Markdown("### 🎛️ Video Scrubber")
                video_scrubber = gr.Slider(
                    minimum=0,
                    maximum=100,
                    value=0,
                    step=0.1,
                    label="📹 Video Position",
                    info="Scrub through the video"
                )
                
                current_time_display = gr.Textbox(
                    label="⏰ Current Time",
                    value="0:00",
                    interactive=False
                )
            
            with gr.Column(scale=1):
                # Video info and trim controls
                video_info = gr.Textbox(
                    label="📊 Video Info",
                    interactive=False,
                    value="Load a video to see information"
                )
                
                gr.Markdown("### ✂️ Trim Settings")
                
                start_slider = gr.Slider(
                    minimum=0,
                    maximum=100,
                    value=0,
                    step=0.1,
                    label="⏯️ Start Time",
                    info="Trim start position"
                )
                
                start_time_display = gr.Textbox(
                    label="⏯️ Start Time",
                    value="0:00",
                    interactive=False
                )
                
                end_slider = gr.Slider(
                    minimum=0,
                    maximum=100,
                    value=100,
                    step=0.1,
                    label="⏹️ End Time",
                    info="Trim end position"
                )
                
                end_time_display = gr.Textbox(
                    label="⏹️ End Time",
                    value="1:40",
                    interactive=False
                )
                
                # Seek buttons
                with gr.Row():
                    seek_start_btn = gr.Button("🎯 Seek Start", variant="secondary", size="sm")
                    seek_end_btn = gr.Button("🎯 Seek End", variant="secondary", size="sm")
                
                trim_btn = gr.Button(
                    "✂️ Trim Video",
                    variant="primary",
                    size="lg"
                )
                
                status_msg = gr.Textbox(
                    label="📝 Status",
                    interactive=False,
                    value="Ready to trim..."
                )
    
    # Output and Save Options
    with gr.Tab("💾 Output & Save"):
        with gr.Row():
            with gr.Column():
                gr.Markdown("### 📤 Output Files")
                
                output_video = gr.Video(
                    label="🎬 Trimmed Video",
                    show_label=True
                )
                
                output_audio_player = gr.Audio(
                    label="🎵 Play Extracted Audio",
                    show_label=True,
                    type="filepath"
                )
                
                output_audio_download = gr.File(
                    label="💾 Download Audio (AAC)",
                    show_label=True
                )
            
            with gr.Column():
                gr.Markdown("### 🔄 Save Options")
                
                # Local save path
                local_output_path = gr.Textbox(
                    label="📁 Local Output Folder",
                    placeholder="/path/to/output/folder",
                    value="./output",
                    lines=1
                )
                
                # Google Drive save path
                drive_output_path = gr.Textbox(
                    label="☁️ Google Drive Output Folder",
                    placeholder="Drive folder ID or path",
                    lines=1
                )
                
                with gr.Row():
                    save_local_btn = gr.Button("💾 Save Locally", variant="secondary")
                    save_drive_btn = gr.Button("☁️ Save to Drive", variant="info")
                
                save_status = gr.Textbox(
                    label="📝 Save Status",
                    interactive=False,
                    value="Trim a video to enable save options"
                )
    
    # Google Drive upload functionality
    def upload_to_drive(video_file, audio_file, drive_folder_path):
        """Upload trimmed files to Google Drive"""
        if not video_file or not audio_file:
            return "❌ No files to upload. Please trim a video first."
        
        if not drive_folder_path:
            return "❌ Please enter a Google Drive folder path or ID"
        
        try:
            service = get_google_drive_service()
            if not service:
                return "❌ Google Drive service not available. Check oauth_credentials.json"
            
            # Extract folder ID if it's a Drive link
            folder_id = extract_drive_file_id(drive_folder_path)
            if not folder_id:
                # Try to use as folder ID directly
                folder_id = drive_folder_path.strip()
            
            from googleapiclient.http import MediaFileUpload
            
            uploaded_files = []
            
            # Upload video file
            video_name = os.path.basename(video_file)
            video_metadata = {
                'name': video_name,
                'parents': [folder_id] if folder_id else []
            }
            video_media = MediaFileUpload(video_file, resumable=True)
            video_upload = service.files().create(
                body=video_metadata,
                media_body=video_media,
                fields='id,name'
            ).execute()
            uploaded_files.append(f"📹 {video_upload['name']}")
            
            # Upload audio file
            audio_name = os.path.basename(audio_file)
            audio_metadata = {
                'name': audio_name,
                'parents': [folder_id] if folder_id else []
            }
            audio_media = MediaFileUpload(audio_file, resumable=True)
            audio_upload = service.files().create(
                body=audio_metadata,
                media_body=audio_media,
                fields='id,name'
            ).execute()
            uploaded_files.append(f"🎵 {audio_upload['name']}")
            
            return f"✅ Uploaded to Google Drive:\n" + "\n".join(uploaded_files)
            
        except Exception as e:
            logger.error(f"❌ Error uploading to Drive: {e}")
            return f"❌ Upload failed: {str(e)}"
    
    def save_files_locally(video_file, audio_file, local_path):
        """Save trimmed files to local directory"""
        if not video_file or not audio_file:
            return "❌ No files to save. Please trim a video first."
        
        if not local_path:
            local_path = "./output"
        
        try:
            # Create output directory
            os.makedirs(local_path, exist_ok=True)
            
            # Copy files to output directory
            import shutil
            video_name = os.path.basename(video_file)
            audio_name = os.path.basename(audio_file)
            
            new_video_path = os.path.join(local_path, video_name)
            new_audio_path = os.path.join(local_path, audio_name)
            
            shutil.copy2(video_file, new_video_path)
            shutil.copy2(audio_file, new_audio_path)
            
            return f"✅ Saved locally:\n📹 {new_video_path}\n🎵 {new_audio_path}"
            
        except Exception as e:
            logger.error(f"❌ Error saving locally: {e}")
            return f"❌ Save failed: {str(e)}"
    
    # Save button handlers
    save_local_btn.click(
        fn=save_files_locally,
        inputs=[output_video, output_audio_download, local_output_path],
        outputs=[save_status]
    )
    
    save_drive_btn.click(
        fn=upload_to_drive,
        inputs=[output_video, output_audio_download, drive_output_path],
        outputs=[save_status]
    )

    # Hidden tab for legacy compatibility
    with gr.Tab("☁️ Google Drive (Legacy)", visible=False):
        def get_drive_files():
            """Get list of video files from Google Drive"""
            try:
                service = get_google_drive_service()
                if not service:
                    return gr.Dropdown(choices=[], value=None, label="❌ Google Drive not available")
                
                videos = list_drive_videos(service)
                if not videos:
                    return gr.Dropdown(choices=[], value=None, label="📁 No videos found in Drive")
                
                choices = [(f"{video['name']} ({video.get('size', 'Unknown')} bytes)", video['id']) for video in videos]
                return gr.Dropdown(choices=choices, value=None, label="📹 Select Video from Drive")
            except Exception as e:
                logger.error(f"❌ Error getting Drive files: {e}")
                return gr.Dropdown(choices=[], value=None, label="❌ Error loading Drive files")
        
        def load_drive_video(file_id):
            """Load selected video from Google Drive"""
            if not file_id:
                return None, "Please select a video file first"
            
            try:
                service = get_google_drive_service()
                if not service:
                    return None, "❌ Google Drive service not available"
                
                # Get file info
                file_info = service.files().get(fileId=file_id).execute()
                filename = file_info['name']
                
                # Download file
                temp_file = download_from_drive(service, file_id, filename)
                if temp_file:
                    return temp_file, f"✅ Loaded: {filename}"
                else:
                    return None, f"❌ Failed to download: {filename}"
            except Exception as e:
                logger.error(f"❌ Error loading Drive video: {e}")
                return None, f"❌ Error: {str(e)}"
        
        with gr.Row():
            with gr.Column():
                gr.Markdown("### 🔗 Google Drive Integration")
                gr.Markdown("**💡 Tips:**")
                gr.Markdown("- **File Path**: `/path/to/your/video.mp4` or `C:\\path\\to\\video.mp4`")
                gr.Markdown("- **Drive Link**: `https://drive.google.com/file/d/FILE_ID/view`")
                gr.Markdown("- **Drive File ID**: `1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74mMjoeAiGQ`")
                
                drive_file_path = gr.Textbox(
                    label="📹 Video File Path or Drive Link",
                    placeholder="Enter file path, Drive link, or file ID",
                    info="Supports local paths, Google Drive links, or file IDs",
                    lines=1,
                    max_lines=1
                )
                
                drive_output_path = gr.Textbox(
                    label="📁 Output Folder Path",
                    placeholder="/path/to/output/folder",
                    value="./drive_output",
                    info="Where to save trimmed videos",
                    lines=1,
                    max_lines=1
                )
                
                with gr.Row():
                    load_drive_btn = gr.Button("📥 Load Video", variant="primary")
                    browse_drive_btn = gr.Button("📂 Browse Drive", variant="secondary")
                
                drive_status = gr.Textbox(
                    label="📝 Drive Status",
                    interactive=False,
                    value="Enter a file path or Drive link above"
                )
            
            with gr.Column():
                drive_video_player = gr.Video(
                    label="🎥 Drive Video Player",
                    show_label=True
                )
                
                drive_video_info = gr.Textbox(
                    label="📊 Drive Video Info",
                    interactive=False,
                    value="Load a video from Drive to see information"
                )
        
        # Drive video controls (same as local)
        with gr.Row():
            with gr.Column():
                gr.Markdown("### ✂️ Trim Settings")
                
                with gr.Group():
                    drive_start_slider = gr.Slider(
                        minimum=0,
                        maximum=100,
                        value=0,
                        step=0.1,
                        label="⏯️ Start Time"
                    )
                    
                    drive_start_time_display = gr.Textbox(
                        label="⏯️ Start Time",
                        value="0:00",
                        interactive=False
                    )
                    
                    drive_seek_start_btn = gr.Button(
                        "🎯 Seek to Start",
                        variant="secondary",
                        size="sm"
                    )
                
                with gr.Group():
                    drive_end_slider = gr.Slider(
                        minimum=0,
                        maximum=100,
                        value=100,
                        step=0.1,
                        label="⏹️ End Time"
                    )
                    
                    drive_end_time_display = gr.Textbox(
                        label="⏹️ End Time",
                        value="1:40",
                        interactive=False
                    )
                    
                    drive_seek_end_btn = gr.Button(
                        "🎯 Seek to End",
                        variant="secondary",
                        size="sm"
                    )
                
                drive_trim_btn = gr.Button(
                    "✂️ Trim Drive Video",
                    variant="primary",
                    size="lg"
                )
                
                drive_status_msg = gr.Textbox(
                    label="📝 Status",
                    interactive=False,
                    value="Ready to trim..."
                )
        
        # Drive output section
        gr.Markdown("### 📤 Output Files")
        
        with gr.Row():
            with gr.Column():
                drive_output_video = gr.Video(
                    label="🎬 Trimmed Video",
                    show_label=True
                )
            
            with gr.Column():
                drive_output_audio_player = gr.Audio(
                    label="🎵 Play Extracted Audio",
                    show_label=True,
                    type="filepath"
                )
                
                drive_output_audio_download = gr.File(
                    label="💾 Download Audio (AAC)",
                    show_label=True
                )
        
        # Drive event handlers (legacy tab)
        
        def load_and_update_drive_video(input_path):
            if not input_path:
                return None, "Please enter a file path or Drive link", None, None, None, None, None
            
            temp_file, status = load_video_from_path_or_drive(input_path)
            if temp_file:
                info, duration, start_val, end_val = get_video_info(temp_file)
                return (
                    temp_file,  # drive_video_player
                    status,     # drive_status
                    info,       # drive_video_info
                    gr.Slider(minimum=0, maximum=duration, value=0, step=0.1),  # drive_start_slider
                    gr.Slider(minimum=0, maximum=duration, value=duration, step=0.1),  # drive_end_slider
                    "0:00",     # drive_start_time_display
                    format_time(duration)  # drive_end_time_display
                )
            else:
                return None, status, "Failed to load video", None, None, None, None
        
        # Set up Drive event handlers
        # browse_drive_btn click handler moved to unified interface
        
        load_drive_btn.click(
            fn=load_and_update_drive_video,
            inputs=[drive_file_path],
            outputs=[drive_video_player, drive_status, drive_video_info, drive_start_slider, drive_end_slider, drive_start_time_display, drive_end_time_display]
        )
        
        # Drive slider event handlers
        drive_start_slider.change(
            fn=lambda x: format_time(x),
            inputs=[drive_start_slider],
            outputs=[drive_start_time_display]
        )
        
        drive_end_slider.change(
            fn=lambda x: format_time(x),
            inputs=[drive_end_slider],
            outputs=[drive_end_time_display]
        )
        
        # Drive seek button handlers
        drive_seek_start_btn.click(
            fn=None,
            inputs=[drive_start_slider],
            outputs=[],
            js="(start_time) => { const videos = document.querySelectorAll('video'); videos.forEach(v => { if (v.src && v.readyState >= 2) v.currentTime = start_time; }); }"
        )
        
        drive_seek_end_btn.click(
            fn=None,
            inputs=[drive_end_slider],
            outputs=[],
            js="(end_time) => { const videos = document.querySelectorAll('video'); videos.forEach(v => { if (v.src && v.readyState >= 2) v.currentTime = end_time; }); }"
        )
        
        # Drive trim button - need to modify to use output path
        def trim_drive_video(video_file, start_time, end_time, output_path):
            """Trim video with custom output path"""
            if not video_file:
                return None, None, None, "❌ Please load a video first"
            
            # Create output directory
            os.makedirs(output_path, exist_ok=True)
            
            # Call the main trim function but intercept the output
            result = process_video_trim(video_file, start_time, end_time)
            
            if result[0]:  # If video was successfully trimmed
                # Move files to custom output path
                import shutil
                base_name = Path(video_file).stem
                new_video = os.path.join(output_path, f"{base_name}_trimmed.mp4")
                new_audio = os.path.join(output_path, f"{base_name}_trimmed.aac")
                
                try:
                    shutil.move(result[0], new_video)
                    shutil.move(result[1], new_audio)
                    return new_video, new_audio, new_audio, f"✅ Trimmed and saved to: {output_path}"
                except Exception as e:
                    return result[0], result[1], result[2], f"✅ Trimmed but move failed: {str(e)}"
            
            return result
        
        drive_trim_btn.click(
            fn=trim_drive_video,
            inputs=[drive_video_player, drive_start_slider, drive_end_slider, drive_output_path],
            outputs=[drive_output_video, drive_output_audio_player, drive_output_audio_download, drive_status_msg]
        )
    
    # Event handlers for unified interface
    def load_local_video(video_file):
        """Load local video file"""
        if not video_file:
            return None, "Please select a video file", "No video loaded", None, None, None, None, None
        
        info, duration, start_val, end_val = get_video_info(video_file)
        return (
            video_file,  # main_video_player
            f"✅ Local file: {os.path.basename(video_file)}",  # load_status
            info,  # video_info
            gr.Slider(minimum=0, maximum=duration, value=0, step=0.1),  # start_slider
            gr.Slider(minimum=0, maximum=duration, value=duration, step=0.1),  # end_slider
            gr.Slider(minimum=0, maximum=duration, value=0, step=0.1),  # video_scrubber
            "0:00",  # start_time_display
            format_time(duration)  # end_time_display
        )
    
    def load_remote_video(input_path):
        """Load video from path or Drive link"""
        if not input_path:
            return None, "Please enter a file path or Drive link", "No video loaded", None, None, None, None, None
        
        temp_file, status = load_video_from_path_or_drive(input_path)
        if temp_file:
            info, duration, start_val, end_val = get_video_info(temp_file)
            return (
                temp_file,  # main_video_player
                status,     # load_status
                info,       # video_info
                gr.Slider(minimum=0, maximum=duration, value=0, step=0.1),  # start_slider
                gr.Slider(minimum=0, maximum=duration, value=duration, step=0.1),  # end_slider
                gr.Slider(minimum=0, maximum=duration, value=0, step=0.1),  # video_scrubber
                "0:00",     # start_time_display
                format_time(duration)  # end_time_display
            )
        else:
            return None, status, "Failed to load video", None, None, None, None, None
    
    def update_start_display(start_val):
        return format_time(start_val)
    
    def update_end_display(end_val):
        return format_time(end_val)
    
    def update_current_time_display(current_val):
        return format_time(current_val)
    
    def browse_drive_files():
        """Browse Drive files and show some examples"""
        try:
            service = get_google_drive_service()
            if not service:
                return "❌ Google Drive credentials not found. Please add oauth_credentials.json"
            
            videos = list_drive_videos(service)
            if not videos:
                return "📁 No videos found in your Google Drive"
            
            result = f"✅ Found {len(videos)} videos in your Drive:\n\n"
            for i, video in enumerate(videos[:10]):  # Show first 10
                result += f"{i+1}. {video['name']} (ID: {video['id']})\n"
            
            if len(videos) > 10:
                result += f"\n... and {len(videos) - 10} more videos"
            
            result += "\n\n💡 Copy a file ID and paste it in the input above!"
            return result
        except Exception as e:
            logger.error(f"❌ Error browsing Drive: {e}")
            return f"❌ Error: {str(e)}"
    
    # Connect event handlers to unified interface
    local_load_btn.click(
        fn=load_local_video,
        inputs=[local_video_input],
        outputs=[main_video_player, load_status, video_info, start_slider, end_slider, video_scrubber, start_time_display, end_time_display]
    )
    
    remote_load_btn.click(
        fn=load_remote_video,
        inputs=[remote_video_input],
        outputs=[main_video_player, load_status, video_info, start_slider, end_slider, video_scrubber, start_time_display, end_time_display]
    )
    
    browse_drive_btn.click(
        fn=browse_drive_files,
        outputs=[load_status]
    )
    
    # Slider change handlers
    start_slider.change(
        fn=update_start_display,
        inputs=[start_slider],
        outputs=[start_time_display]
    )
    
    end_slider.change(
        fn=update_end_display,
        inputs=[end_slider],
        outputs=[end_time_display]
    )
    
    video_scrubber.change(
        fn=update_current_time_display,
        inputs=[video_scrubber],
        outputs=[current_time_display]
    )
    
    # Video control button handlers
    play_btn.click(
        fn=None,
        inputs=[],
        outputs=[],
        js="() => { const videos = document.querySelectorAll('video'); videos.forEach(v => { if (v.src && v.readyState >= 2) v.play(); }); }"
    )
    
    pause_btn.click(
        fn=None,
        inputs=[],
        outputs=[],
        js="() => { const videos = document.querySelectorAll('video'); videos.forEach(v => { if (v.src && v.readyState >= 2) v.pause(); }); }"
    )
    
    seek_current_btn.click(
        fn=None,
        inputs=[video_scrubber],
        outputs=[],
        js="(current_time) => { const videos = document.querySelectorAll('video'); videos.forEach(v => { if (v.src && v.readyState >= 2) v.currentTime = current_time; }); }"
    )
    
    # Seek button handlers for trim points
    seek_start_btn.click(
        fn=None,
        inputs=[start_slider],
        outputs=[],
        js="(start_time) => { const videos = document.querySelectorAll('video'); videos.forEach(v => { if (v.src && v.readyState >= 2) v.currentTime = start_time; }); }"
    )
    
    seek_end_btn.click(
        fn=None,
        inputs=[end_slider],
        outputs=[],
        js="(end_time) => { const videos = document.querySelectorAll('video'); videos.forEach(v => { if (v.src && v.readyState >= 2) v.currentTime = end_time; }); }"
    )
    
    # Video scrubber seeking
    video_scrubber.change(
        fn=None,
        inputs=[video_scrubber],
        outputs=[],
        js="(scrub_time) => { const videos = document.querySelectorAll('video'); videos.forEach(v => { if (v.src && v.readyState >= 2) v.currentTime = scrub_time; }); }"
    )
    
    # Trim button handler
    trim_btn.click(
        fn=process_video_trim,
        inputs=[main_video_player, start_slider, end_slider],
        outputs=[output_video, output_audio_player, output_audio_download, status_msg]
    )

if __name__ == "__main__":
    import sys
    
    # Enable auto-reload for development
    auto_reload = "--reload" in sys.argv or "--dev" in sys.argv
    
    demo.launch(
        server_name="0.0.0.0",
        server_port=7890,  # Use specific port to avoid conflicts
        share=False,
        show_error=True,
        debug=True,
        # Note: auto-reload not supported in this Gradio version
    )