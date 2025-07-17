# trim-convert.sh

A fast and efficient tool for trimming MP4 videos with minimal processing and optional audio extraction.

## Features

- ✂️ **Trim videos** between specified start and end times
- 🔄 **Minimal processing** with smart stream copying when possible
- 🔊 **Extract audio** in AAC format automatically
- ⚡ **Cross-platform** compatibility (macOS and Linux)
- 🛠️ **Flexible options** with sensible defaults

## Installation

1. Clone this repository or download the script:
   ```bash
   curl -O https://raw.githubusercontent.com/nipunbatra/trim-convert/main/trim-convert.sh
   ```

2. Make the script executable:
   ```bash
   chmod +x trim-convert.sh
   ```

3. Ensure you have ffmpeg installed:
   - macOS: `brew install ffmpeg`
   - Ubuntu/Debian: `sudo apt install ffmpeg`
   - Fedora/CentOS: `sudo dnf install ffmpeg`

## Usage

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

```bash
# Trim from 1m30s to 5m45s
./trim-convert.sh -s 00:01:30 -e 00:05:45 video.mp4

# Trim from start to 10 minutes
./trim-convert.sh -e 00:10:00 video.mp4

# Trim from 2 minutes to the end
./trim-convert.sh -s 00:02:00 video.mp4

# Custom output name
./trim-convert.sh -o my_clip -s 00:01:30 -e 00:05:45 video.mp4

# Process entire file (just extract audio)
./trim-convert.sh video.mp4
```

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

## Requirements

- ffmpeg (version 4.0+)
- Bash shell

## License

MIT License - See LICENSE file for details

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.