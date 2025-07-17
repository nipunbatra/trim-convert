#!/usr/bin/env python3

import gradio as gr
import subprocess
import os
import tempfile
import shutil
import logging
import time
from pathlib import Path

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
"""

with gr.Blocks(title="Video Trimmer Tool", theme=gr.themes.Soft(), css=custom_css) as demo:
    gr.Markdown("""
    # 🎬 Video Trimmer Tool - Local Edition
    Upload a video file, set trim points using the sliders, and get both trimmed video and extracted audio files.
    
    **Features:**
    - ✂️ **Precise trimming** with visual sliders
    - 🎵 **Audio extraction** (AAC format)
    - 🚀 **Fast processing** using your proven trim-convert.sh script
    - 📁 **Local files only** - no cloud complexity
    
    **Supported formats:** MP4, MOV, AVI, MKV
    """)
    
    with gr.Row():
        with gr.Column(scale=2):
            # Video upload and display
            video_input = gr.File(
                label="📁 Upload Video File",
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
                gr.Markdown("**🎯 Start point:**")
                start_slider = gr.Slider(
                    minimum=0,
                    maximum=100,
                    value=0,
                    step=0.1,
                    label="⏯️ Start Time",
                    info="Drag to set start position",
                    elem_classes=["slider-container"]
                )
                
                start_time_display = gr.Textbox(
                    label="⏯️ Start Time",
                    value="0:00",
                    interactive=False,
                    info="Current start time"
                )
            
            with gr.Group():
                gr.Markdown("**🎯 End point:**")
                end_slider = gr.Slider(
                    minimum=0,
                    maximum=100,
                    value=100,
                    step=0.1,
                    label="⏹️ End Time",
                    info="Drag to set end position",
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
    
    # Trim button handler
    trim_btn.click(
        fn=process_video_trim,
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