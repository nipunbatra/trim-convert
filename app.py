import gradio as gr
import subprocess
import os
import tempfile
import shutil
import logging
import time
from pathlib import Path
try:
    from native_drive_picker import GoogleDrivePickerManager, get_native_picker_instructions, GOOGLE_DRIVE_AVAILABLE
except ImportError:
    GOOGLE_DRIVE_AVAILABLE = False
    GoogleDrivePickerManager = None
    def get_native_picker_instructions():
        return "Google Drive integration not available in this environment."

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def process_video_trim(video_file, start_time, end_time):
    """Process video trimming using the trim-convert.sh script"""
    logger.info(f"🎬 Starting trim process: file={video_file}, start={start_time}, end={end_time}")
    
    if not video_file or start_time is None or end_time is None:
        error_msg = "Please provide video file and both start/end times"
        logger.error(f"❌ {error_msg}")
        return None, None, None, error_msg
    
    try:
        # start_time and end_time are now numbers (seconds) from sliders
        start_seconds = float(start_time)
        end_seconds = float(end_time)
        
        logger.info(f"📊 Parsed times: start={start_seconds}s, end={end_seconds}s")
        
        if start_seconds >= end_seconds:
            error_msg = "Start time must be less than end time"
            logger.error(f"❌ {error_msg}")
            return None, None, None, error_msg
        
        # Check if input file exists
        if not os.path.exists(video_file):
            error_msg = f"Input video file not found: {video_file}"
            logger.error(f"❌ {error_msg}")
            return None, None, None, error_msg
        
        # Create temporary directory for output
        temp_dir = tempfile.mkdtemp()
        logger.info(f"📁 Created temp directory: {temp_dir}")
        
        input_path = video_file
        
        # Get the base filename without extension
        base_name = Path(input_path).stem
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
            input_path
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
                video_size = os.path.getsize(output_video)
                audio_size = os.path.getsize(output_audio)
                logger.info(f"📊 File sizes: video={video_size} bytes, audio={audio_size} bytes")
                
                # Check if video file is valid and convert for better web compatibility
                try:
                    test_duration = get_video_duration(output_video)
                    logger.info(f"✅ Output video duration: {test_duration} seconds")
                    if test_duration == 0:
                        logger.warning("⚠️ Output video duration is 0, may have encoding issues")
                    
                    # Check if trimmed video is web-compatible, if not, convert only the headers
                    display_video = output_video  # Start with original
                    
                    # Quick check if video might have compatibility issues
                    try:
                        # Test if ffprobe can read the file properly
                        probe_cmd = ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", output_video]
                        probe_result = subprocess.run(probe_cmd, capture_output=True, text=True)
                        
                        if probe_result.returncode == 0:
                            import json
                            probe_data = json.loads(probe_result.stdout)
                            format_info = probe_data.get('format', {})
                            
                            # Check if it needs web optimization
                            needs_conversion = False
                            
                            # If the file has issues or isn't web-optimized, do a quick fix
                            if needs_conversion or True:  # Always do quick web optimization for now
                                web_video_path = os.path.join(temp_dir, f"{base_name}_web.mp4")
                                
                                # Quick web compatibility fix - just fix headers and ensure proper format
                                web_convert_cmd = [
                                    "ffmpeg", "-y", "-i", output_video,
                                    "-c", "copy",  # Copy streams (fast)
                                    "-movflags", "+faststart",  # Optimize for web
                                    "-f", "mp4",  # Ensure MP4 format
                                    web_video_path
                                ]
                                
                                logger.info(f"🌐 Quick web optimization (stream copy)...")
                                web_result = subprocess.run(web_convert_cmd, capture_output=True, text=True)
                                
                                if web_result.returncode == 0 and os.path.exists(web_video_path):
                                    web_size = os.path.getsize(web_video_path)
                                    logger.info(f"✅ Web-optimized video: {web_video_path} ({web_size} bytes)")
                                    display_video = web_video_path
                                    
                                    # Verify the optimized video
                                    web_duration = get_video_duration(web_video_path)
                                    logger.info(f"🎬 Optimized video duration: {web_duration} seconds")
                                else:
                                    logger.warning(f"⚠️ Quick optimization failed: {web_result.stderr}")
                                    logger.info("Using original trimmed video")
                        else:
                            logger.warning("⚠️ Could not analyze trimmed video, using as-is")
                            
                    except Exception as e:
                        logger.warning(f"⚠️ Video analysis failed: {e}, using original")
                        
                except Exception as e:
                    logger.warning(f"⚠️ Could not verify output video: {e}")
                    display_video = output_video
                
                # Create MP3 version for audio player (better browser compatibility)
                timestamp = str(int(time.time() * 1000))
                temp_audio_dir = os.path.dirname(output_audio)
                audio_player_file = os.path.join(temp_audio_dir, f"player_audio_{timestamp}.mp3")
                
                # Convert AAC to MP3 for better browser support
                convert_cmd = [
                    "ffmpeg", "-y", "-i", output_audio, 
                    "-codec:a", "libmp3lame", "-b:a", "128k",
                    audio_player_file
                ]
                
                logger.info(f"🔄 Converting audio for player: {' '.join(convert_cmd)}")
                convert_result = subprocess.run(convert_cmd, capture_output=True, text=True)
                
                if convert_result.returncode == 0 and os.path.exists(audio_player_file):
                    logger.info(f"🎵 Created MP3 audio player file: {audio_player_file}")
                    logger.info(f"📊 Audio player file size: {os.path.getsize(audio_player_file)} bytes")
                else:
                    logger.warning(f"⚠️ MP3 conversion failed, using original AAC file")
                    audio_player_file = output_audio
                
                success_msg = f"✅ Successfully trimmed video from {start_seconds:.1f}s to {end_seconds:.1f}s"
                
                # No automatic upload - will be done manually after trimming
                
                logger.info(success_msg)
                return display_video, audio_player_file, output_audio, success_msg, output_video, output_audio
            else:
                error_msg = f"❌ Output files not created.\n\nScript STDOUT:\n{result.stdout}\n\nScript STDERR:\n{result.stderr}\n\nExpected files:\nVideo: {output_video}\nAudio: {output_audio}"
                logger.error(error_msg)
                return None, None, None, error_msg, None, None
        else:
            error_msg = f"❌ trim-convert.sh failed with return code {result.returncode}\n\nCommand run:\n{' '.join(cmd)}\n\nSTDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}"
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
        
        # Use ffprobe to get video duration
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

# Native Google Drive picker functions
def open_file_picker(drive_manager):
    """Open Google Drive for file selection (full access)"""
    if not drive_manager or not drive_manager.is_available():
        return "❌ Google Drive not available"
    
    instructions = drive_manager.open_drive_picker("file")
    return instructions

def open_folder_picker(drive_manager):
    """Open Google Drive for folder selection"""
    if not drive_manager or not drive_manager.is_available():
        return "❌ Google Drive not available"
    
    instructions = drive_manager.open_drive_picker("folder")
    return instructions

def download_from_drive_url(drive_manager, drive_url, custom_filename=""):
    """Download video from Google Drive URL"""
    if not drive_manager or not drive_manager.is_available():
        return None, "❌ Google Drive not available"
    
    if not drive_url or not drive_url.strip():
        return None, "⚠️ Please paste a Google Drive link"
    
    filename = custom_filename.strip() if custom_filename.strip() else None
    return drive_manager.download_file_from_url(drive_url, filename)

def download_from_google_drive(file_id, file_display, drive_manager):
    """Download selected file from Google Drive"""
    if not file_id or not drive_manager or not drive_manager.is_available():
        return None, "❌ No file selected or Google Drive unavailable"
    
    try:
        # Extract filename from display string
        filename = file_display.split(' (')[0] if file_display else f"video_{file_id}.mp4"
        
        logger.info(f"📥 Downloading {filename} from Google Drive...")
        local_path = drive_manager.download_file(file_id, filename)
        
        if local_path and os.path.exists(local_path):
            return local_path, f"✅ Downloaded: {filename}"
        else:
            return None, "❌ Download failed"
    except Exception as e:
        logger.error(f"Error downloading from Google Drive: {e}")
        return None, f"❌ Download error: {str(e)}"

# Initialize Google Drive manager
try:
    if GOOGLE_DRIVE_AVAILABLE and GoogleDrivePickerManager:
        # Check if running on HF Space and use secret
        oauth_json = os.getenv('OAUTH_CREDENTIALS_JSON')
        logger.info(f"🔍 Checking for OAuth secret... Found: {oauth_json is not None}")
        
        if oauth_json:
            logger.info(f"📝 OAuth secret length: {len(oauth_json)} characters")
            # Write the secret to a temporary file
            with open('oauth_credentials.json', 'w') as f:
                f.write(oauth_json)
            logger.info("✅ OAuth credentials loaded from HF secret and written to file")
            
            # Verify file was created
            if os.path.exists('oauth_credentials.json'):
                file_size = os.path.getsize('oauth_credentials.json')
                logger.info(f"✅ oauth_credentials.json created successfully ({file_size} bytes)")
            else:
                logger.error("❌ Failed to create oauth_credentials.json file")
        else:
            logger.info("ℹ️ No OAuth secret found - checking for local file")
            if os.path.exists('oauth_credentials.json'):
                logger.info("✅ Using local oauth_credentials.json file")
            else:
                logger.warning("⚠️ No OAuth credentials available (neither secret nor local file)")
        
        # Set environment variable to disable browser for HF Spaces
        if oauth_json:
            os.environ['GOOGLE_DRIVE_HEADLESS'] = 'true'
            logger.info("🌐 Set headless mode for HF Spaces")
        
        drive_manager = GoogleDrivePickerManager()
        drive_available = drive_manager.is_available()
    else:
        drive_manager = None
        drive_available = False
except Exception as e:
    logger.warning(f"Google Drive initialization failed: {e}")
    drive_manager = None
    drive_available = False

# Create the Gradio interface with custom CSS and JS
custom_css = """
.video-container video {
    width: 100%;
    max-height: 400px;
}
.slider-container {
    margin: 10px 0;
}
.drive-section {
    border: 1px solid #e0e0e0;
    padding: 15px;
    border-radius: 8px;
    margin: 10px 0;
}
"""

custom_js = """
function seekVideo(slider_value, video_id) {
    const video = document.querySelector('#' + video_id + ' video');
    if (video && !isNaN(slider_value)) {
        video.currentTime = slider_value;
    }
    return slider_value;
}
"""

with gr.Blocks(title="Video Trimmer Tool", theme=gr.themes.Soft(), css=custom_css) as demo:
    gr.Markdown("""
    # 🎬 Video Trimmer Demo
    Upload an MP4 video, set trim points, and generate trimmed video + audio files.
    """)
    
    # Native Google Drive picker section
    if drive_available:
        user_email = drive_manager.get_user_info() if drive_manager else "Unknown"
        with gr.Group():
            gr.Markdown("### 🔗 Google Drive Integration (Native Picker)")
            gr.Markdown(f"**👤 Signed in as:** {user_email}")
            
            # Video picker section
            with gr.Row():
                with gr.Column(scale=2):
                    gr.Markdown("#### 📁 Load Any File from Google Drive")
                    
                    open_picker_btn = gr.Button(
                        "🌍 Browse Your Entire Google Drive",
                        variant="primary",
                        size="lg"
                    )
                    
                    picker_instructions = gr.Textbox(
                        label="📝 Instructions",
                        value="Click the button above to open your full Google Drive - browse any folder!",
                        interactive=False,
                        lines=6
                    )
                    
                    drive_url_input = gr.Textbox(
                        label="🔗 Paste Any Google Drive File Link",
                        placeholder="https://drive.google.com/file/d/FILE_ID/view...",
                        info="Works with any file type - videos, docs, etc. from any folder"
                    )
                    
                    custom_filename_input = gr.Textbox(
                        label="🏷️ Custom Filename (Optional)",
                        placeholder="my_video.mp4"
                    )
                    
                    download_from_url_btn = gr.Button(
                        "📥 Download Video from Link",
                        variant="secondary"
                    )
                
                with gr.Column(scale=1):
                    drive_status = gr.Textbox(
                        label="📊 Status",
                        value="✅ Ready to pick from Google Drive",
                        interactive=False
                    )
            
            # Simplified note
            gr.Markdown("🚀 **Upload to Google Drive will be available after video trimming.**")
    else:
        with gr.Group():
            gr.Markdown("### 🔗 Google Drive Integration")
            if not GOOGLE_DRIVE_AVAILABLE:
                gr.Markdown("**⚠️ Google Drive libraries not installed.**")
                gr.Markdown("Install with: `pip install google-api-python-client google-auth google-auth-oauthlib`")
            else:
                gr.Markdown("**⚠️ Setup needed:** Create oauth_credentials.json file")
            
            with gr.Accordion("📋 Setup Instructions", open=False):
                gr.Markdown(get_native_picker_instructions())
    
    with gr.Row():
        with gr.Column(scale=2):
            # Video upload and display
            video_input = gr.File(
                label="📁 Upload MP4 Video",
                file_types=[".mp4", ".mov", ".avi", ".mkv"],
                type="filepath"
            )
            
            video_player = gr.Video(
                label="🎥 Video Player",
                show_label=True,
                elem_id="main_video_player",
                elem_classes=["video-container"]
            )
            
            video_info = gr.Textbox(
                label="📊 Video Info",
                interactive=False,
                value="Upload a video to see information"
            )
        
        with gr.Column(scale=1):
            # Trim controls
            gr.Markdown("### ✂️ Trim Settings")
            gr.Markdown("**🎯 Drag sliders to set trim points:**")
            
            with gr.Group():
                gr.Markdown("**🎯 Scrub to find start point:**")
                start_slider = gr.Slider(
                    minimum=0,
                    maximum=100,
                    value=0,
                    step=0.1,
                    label="⏯️ Start Time (scrub video)",
                    info="Drag to seek video and set start position",
                    elem_classes=["slider-container"]
                )
                
                start_time_display = gr.Textbox(
                    label="⏯️ Start Time",
                    value="0:00",
                    interactive=False,
                    info="Current start time"
                )
            
            with gr.Group():
                gr.Markdown("**🎯 Scrub to find end point:**")
                end_slider = gr.Slider(
                    minimum=0,
                    maximum=100,
                    value=100,
                    step=0.1,
                    label="⏹️ End Time (scrub video)",
                    info="Drag to seek video and set end position",
                    elem_classes=["slider-container"]
                )
                
                end_time_display = gr.Textbox(
                    label="⏹️ End Time",
                    value="1:40",
                    interactive=False,
                    info="Current end time"
                )
            
            trim_btn = gr.Button(
                "✂️ Trim Video",
                variant="primary",
                size="lg"
            )
            
            # Note about manual upload
            gr.Markdown("📝 **Note:** Upload options will appear after trimming is complete.")
            
            status_msg = gr.Textbox(
                label="📝 Status",
                interactive=False,
                value="Ready to trim..."
            )
    
    # Output section
    gr.Markdown("### 📤 Output Files")
    
    with gr.Row():
        with gr.Column():
            output_video = gr.Video(
                label="🎬 Trimmed Video",
                show_label=True
            )
        
        with gr.Column():
            output_audio_player = gr.Audio(
                label="🎵 Play Extracted Audio",
                show_label=True,
                type="filepath"
            )
            
            output_audio_download = gr.File(
                label="💾 Download Audio (AAC)",
                show_label=True
            )
    
    # Post-processing upload section (appears after trimming)
    if drive_available:
        with gr.Group(visible=False) as post_upload_section:
            gr.Markdown("### 🚀 Upload Trimmed Files to Google Drive")
            
            with gr.Row():
                with gr.Column(scale=2):
                    post_open_folder_btn = gr.Button(
                        "🌍 Choose Google Drive Upload Folder",
                        variant="primary"
                    )
                    
                    post_folder_instructions = gr.Textbox(
                        label="📝 Folder Instructions",
                        value="Click button above to choose where to upload your trimmed files",
                        interactive=False,
                        lines=4
                    )
                    
                    post_upload_folder_url = gr.Textbox(
                        label="📁 Upload Folder Link",
                        placeholder="https://drive.google.com/drive/folders/FOLDER_ID...",
                        info="Leave empty to upload to My Drive root"
                    )
                    
                    post_upload_btn = gr.Button(
                        "📤 Upload Files to Google Drive",
                        variant="secondary",
                        size="lg"
                    )
                
                with gr.Column(scale=1):
                    post_upload_status = gr.Textbox(
                        label="📊 Upload Status",
                        value="Ready to upload",
                        interactive=False
                    )
        
        # Hidden state to store file paths for post-upload
        trimmed_video_path = gr.State(None)
        trimmed_audio_path = gr.State(None)
    
    # Event handlers
    def update_video_and_sliders(video_file):
        info, duration, start_val, end_val = get_video_info(video_file)
        return (
            video_file,  # video_player
            info,  # video_info
            gr.Slider(minimum=0, maximum=duration, value=0, step=0.1),  # start_slider
            gr.Slider(minimum=0, maximum=duration, value=duration, step=0.1),  # end_slider
            "0:00",  # start_time_display
            format_time(duration)  # end_time_display
        )
    
    def update_start_display(start_val):
        return format_time(start_val)
    
    def update_end_display(end_val):
        return format_time(end_val)
    
    video_input.change(
        fn=update_video_and_sliders,
        inputs=[video_input],
        outputs=[video_player, video_info, start_slider, end_slider, start_time_display, end_time_display]
    )
    
    def update_start_and_seek(start_val):
        return format_time(start_val)
    
    def update_end_and_seek(end_val):
        return format_time(end_val)
    
    start_slider.change(
        fn=update_start_and_seek,
        inputs=[start_slider],
        outputs=[start_time_display],
        js="(value) => { const video = document.querySelector('#main_video_player video'); if (video && !isNaN(value)) { video.currentTime = value; } return value; }"
    )
    
    end_slider.change(
        fn=update_end_and_seek,
        inputs=[end_slider],
        outputs=[end_time_display],
        js="(value) => { const video = document.querySelector('#main_video_player video'); if (video && !isNaN(value)) { video.currentTime = value; } return value; }"
    )
    
    # Google Drive native picker event handlers
    if drive_available:
        # Open file picker (full Google Drive access)
        open_picker_btn.click(
            fn=lambda: open_file_picker(drive_manager),
            outputs=[picker_instructions]
        )
        
        # Download from URL
        download_from_url_btn.click(
            fn=lambda url, filename: download_from_drive_url(drive_manager, url, filename),
            inputs=[drive_url_input, custom_filename_input],
            outputs=[video_input, drive_status]
        ).then(
            fn=update_video_and_sliders,
            inputs=[video_input],
            outputs=[video_player, video_info, start_slider, end_slider, start_time_display, end_time_display]
        )
        
        # No pre-upload handlers needed
        
        # Post-upload event handlers
        post_open_folder_btn.click(
            fn=lambda: open_folder_picker(drive_manager),
            outputs=[post_folder_instructions]
        )
        
        def post_upload_files(video_path, audio_path, folder_url):
            if not video_path or not audio_path:
                return "❌ No files to upload"
            
            try:
                folder_url_clean = folder_url.strip() if folder_url and folder_url.strip() else None
                
                video_success, video_result = drive_manager.upload_file_to_folder(video_path, folder_url_clean)
                audio_success, audio_result = drive_manager.upload_file_to_folder(audio_path, folder_url_clean)
                
                if video_success and audio_success:
                    return f"✅ Files uploaded successfully:\n• {video_result}\n• {audio_result}"
                elif video_success:
                    return f"✅ {video_result}\n❌ Audio upload failed: {audio_result}"
                elif audio_success:
                    return f"✅ {audio_result}\n❌ Video upload failed: {video_result}"
                else:
                    return f"❌ Upload failed:\n• Video: {video_result}\n• Audio: {audio_result}"
                    
            except Exception as e:
                return f"❌ Upload error: {str(e)}"
        
        post_upload_btn.click(
            fn=post_upload_files,
            inputs=[trimmed_video_path, trimmed_audio_path, post_upload_folder_url],
            outputs=[post_upload_status]
        )
    
    # Trim button handler with Google Drive upload support
    if drive_available:
        # Simplified trim function that shows upload section after completion
        def trim_and_show_upload(video_file, start_time, end_time):
            result = process_video_trim(video_file, start_time, end_time)
            display_video, audio_player, audio_download, status, orig_video, orig_audio = result
            
            # Show post-upload section if trimming was successful
            show_upload = orig_video is not None and orig_audio is not None
            
            return (
                display_video, audio_player, audio_download, status,  # Original outputs
                orig_video, orig_audio,  # Store paths for post-upload
                gr.Group(visible=show_upload)  # Show/hide upload section
            )
        
        trim_btn.click(
            fn=trim_and_show_upload,
            inputs=[video_input, start_slider, end_slider],
            outputs=[output_video, output_audio_player, output_audio_download, status_msg, 
                    trimmed_video_path, trimmed_audio_path, post_upload_section]
        )
    else:
        # No Google Drive available - simple trim only
        def simple_trim(video_file, start_time, end_time):
            result = process_video_trim(video_file, start_time, end_time)
            return result[:4]  # Return only the first 4 outputs
        
        trim_btn.click(
            fn=simple_trim,
            inputs=[video_input, start_slider, end_slider],
            outputs=[output_video, output_audio_player, output_audio_download, status_msg]
        )

if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=None,  # Auto-find available port
        share=False,
        show_error=True,
        debug=True
    )