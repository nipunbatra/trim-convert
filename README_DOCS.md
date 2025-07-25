A fast and efficient video trimming toolkit with both a **web interface** and **command-line tool** for MP4 video processing. Features visual trimming with drag-to-scrub sliders and automatic audio extraction.

**Documentation**: https://nipunbatra.github.io/video-toolkit/

## Features

- **Web Interface**: Interactive Gradio demo with drag-to-trim sliders
- **Google Drive Integration**: Load videos from and upload results to Google Drive
- **Command Line**: Fast bash script for automated processing  
- **Smart Trimming**: Visual video scrubbing to find exact cut points
- **Audio Extraction**: Automatic AAC extraction with built-in player
- **Minimal Processing**: Stream copying when possible for speed
- **Cross-Platform**: Works on macOS, Linux, and Windows WSL

## Prerequisites

- **ffmpeg** (version 4.0 or higher) - The core dependency for video processing
- **Bash shell** - Available on macOS, Linux, and Windows WSL

### Installing ffmpeg

| Platform | Command |
|----------|---------|
| macOS | `brew install ffmpeg` |
| Ubuntu/Debian | `sudo apt update && sudo apt install ffmpeg` |
| Fedora/CentOS | `sudo dnf install ffmpeg` |
| Windows | Download from [ffmpeg.org](https://ffmpeg.org/download.html) or use `winget install FFmpeg` |

## Installation

### Quick Install (Recommended)

**Step 1:** Download and make executable in one step
```bash
curl -O https://raw.githubusercontent.com/nipunbatra/video-toolkit/main/trim-convert.sh && chmod +x trim-convert.sh
```

**Step 2:** Verify the script works
```bash
./trim-convert.sh --help
```

### Manual Install

**Step 1:** Clone this repository
```bash
git clone https://github.com/nipunbatra/video-toolkit.git
cd video-toolkit
```

**Step 2:** Make the script executable
```bash
chmod +x trim-convert.sh
```

**Note:** The `chmod +x` command grants execute permission to the script file. This is required for shell scripts to run.

**Step 3:** Test the installation
```bash
./trim-convert.sh --help
```

### System-wide Installation (Optional)

**Step 1:** Copy script to system directory
```bash
sudo cp trim-convert.sh /usr/local/bin/trim-convert
```

**Note:** The `sudo` command requires administrator privileges to copy files to system directories like `/usr/local/bin/`.

**Step 2:** Test system-wide access
```bash
trim-convert --help
```

Now you can use `trim-convert` from any directory.

## Gradio Web Interface

For an interactive video trimming experience, use the web interface:

![Video Trimmer Interface](demo/screenshot-ui.jpg)

### Quick Start
```bash
# Install dependencies
pip install -r requirements.txt

# Launch the web interface
./run_demo.sh
```

### Features
- **Video Upload**: Drag & drop MP4/MOV/AVI files or load from Google Drive
- **Google Drive Integration**: Browse your entire Google Drive to pick videos
- **Visual Trimming**: Scrub sliders to find exact start/end points
- **Live Preview**: Video seeks to slider position for precise editing
- **Audio Playback**: Built-in player for extracted audio
- **Download**: Get both trimmed video and AAC audio files
- **Google Drive Upload**: Upload trimmed files back to any folder in your Google Drive

The web interface automatically converts times and calls the command-line script for processing.

### Google Drive Setup (Optional)

To enable Google Drive integration:

1. **Create OAuth credentials**: Follow instructions in `SIMPLE_GOOGLE_SETUP.md`
2. **Download `oauth_credentials.json`** and place in this directory
3. **Run the app** - it will open your browser for one-time authentication
4. **Done!** Browse your entire Google Drive and upload results back

**Note**: Google Drive integration is completely optional - the app works perfectly without it.

## File Permissions

### Understanding Script Permissions

Shell scripts require execute permission to run. When you download a script, it typically doesn't have execute permission by default for security reasons.

### Setting Execute Permission

```bash
chmod +x trim-convert.sh
```

### Verifying Permissions

Check if the script has execute permission:
```bash
ls -l trim-convert.sh
```

Look for `x` in the permissions (e.g., `-rwxr-xr-x`). The `x` indicates execute permission.

### Common Permission Issues

- **"Permission denied"**: Script lacks execute permission - run `chmod +x`
- **"Operation not permitted"**: Need `sudo` for system directories
- **"Command not found"**: Script not in current directory or PATH

## Command Line Usage

```bash
./trim-convert.sh [options] input.mp4
```

### Options

| Option | Description |
|--------|-------------|
| `-s, --start TIME` | Start time (format: HH:MM:SS or seconds) |
| `-e, --end TIME` | End time (format: HH:MM:SS or seconds) |
| `-o, --output PREFIX` | Output file prefix (default: "trimmed") |
| `-h, --help` | Show help message |

### Examples

#### Basic Trimming
```bash
# Trim from 1m30s to 5m45s
./trim-convert.sh -s 00:01:30 -e 00:05:45 video.mp4

# Trim from start to 10 minutes
./trim-convert.sh -e 00:10:00 video.mp4

# Trim from 2 minutes to the end
./trim-convert.sh -s 00:02:00 video.mp4
```

#### Advanced Usage
```bash
# Custom output name
./trim-convert.sh -o my_clip -s 00:01:30 -e 00:05:45 video.mp4

# Process entire file (extract audio only)
./trim-convert.sh video.mp4

# Using seconds instead of HH:MM:SS format
./trim-convert.sh -s 90 -e 345 video.mp4

# Batch processing multiple files
for file in *.mp4; do
    ./trim-convert.sh -s 00:00:10 -e 00:01:00 "$file"
done
```

#### Time Format Options
- **HH:MM:SS**: `00:01:30` (1 minute 30 seconds)
- **MM:SS**: `01:30` (1 minute 30 seconds)
- **Seconds**: `90` (90 seconds)
- **Decimal seconds**: `90.5` (90.5 seconds)

## How It Works

1. The script analyzes the input video to determine if it can use stream copying (no re-encoding) based on keyframe positioning
2. It attempts to use the fastest method possible while maintaining quality
3. If stream copying would result in imprecise cuts, it falls back to re-encoding
4. The audio track is extracted as a separate AAC file

## Output

- `PREFIX.mp4`: The trimmed video file
- `PREFIX.aac`: The extracted audio file

## Technical Details

- Uses ffmpeg's stream copying (`-c copy`) when possible to avoid quality loss
- Falls back to high-quality, fast encoding when necessary (`-c:v libx264 -preset ultrafast -crf 17`)
- Handles keyframe detection for optimal cutting points
- Works with both relative (seconds) and absolute (HH:MM:SS) time formats

## Demo Videos

This repository includes sample copyright-free videos for testing:

| File | Description | Source | License |
|------|-------------|---------|---------|
| `demo/sample-10s.mp4` | 10-second test pattern | Generated with ffmpeg | Public Domain |
| `demo/sample-30s.mp4` | 30-second test pattern | Generated with ffmpeg | Public Domain |

All demo videos are verified to be free to use, modify, and distribute.

## Performance Notes

- **Stream copying**: Fastest method, preserves original quality
- **Re-encoding**: Used when precision is required, high-quality preset
- **Memory usage**: Minimal - processes videos without loading entire file into memory
- **Supported formats**: MP4, AVI, MOV, MKV (output always MP4)

## Troubleshooting

### Common Issues

| Problem | Solution |
|---------|----------|
| "ffmpeg not found" | Install ffmpeg using your package manager |
| "Permission denied" | Run `chmod +x trim-convert.sh` to make script executable |
| "Invalid time format" | Use HH:MM:SS or seconds format |
| "No keyframes found" | Video will be re-encoded (slower but precise) |
| "Command not found" | Check if script is in current directory or PATH |
| "Operation not permitted" | Use `sudo` for system-wide installation |

### Performance Tips

- Use stream copying when possible by aligning cuts with keyframes
- For bulk processing, consider processing multiple files in parallel
- Use SSD storage for better I/O performance with large files

## Requirements

- **ffmpeg** (version 4.0 or higher)
- **Bash shell** (version 4.0 or higher recommended)
- **Available disk space** equal to at least 2x the size of your largest video file

## License

MIT License - See [LICENSE](https://github.com/nipunbatra/video-toolkit/blob/main/LICENSE) file for details

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

## 📖 Documentation Website

This repository has an auto-generated documentation website at: **https://nipunbatra.github.io/video-toolkit**

### How Documentation Works

- **Single source**: Edit only this `README.md` file
- **Auto-build**: GitHub Actions automatically updates the website
- **No manual work**: Never touch the `docs/` folder
- **Live updates**: Changes appear on the website when you push to main

### Making Documentation Changes

1. **Edit this file**: `README.md` (you're reading it now!)
2. **Commit and push**: `git add . && git commit -m "Update docs" && git push`
3. **Done**: Website updates automatically in ~2 minutes

**⚠️ Important**: Never edit files in the `docs/` folder - they're auto-generated!