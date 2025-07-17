# Video Trimmer Tool

A fast and efficient video trimming toolkit with an interactive web interface for MP4 video processing. Features visual trimming with drag-to-scrub sliders and automatic audio extraction.

## Features

- **Interactive Web Interface**: Visual video scrubbing with drag-to-trim sliders
- **Smart Trimming**: Find exact cut points with real-time video seeking
- **Audio Extraction**: Automatic AAC extraction with built-in player
- **Multiple Formats**: Support for MP4, MOV, AVI, and MKV files
- **Fast Processing**: Stream copying when possible for speed
- **Download**: Get both trimmed video and extracted audio files

## How to Use

1. **Upload Video**: Drag & drop your video file or click to upload
2. **Set Trim Points**: Use the sliders to scrub through the video and find your desired start/end points
3. **Trim**: Click "Trim Video" to process
4. **Download**: Get your trimmed video and extracted audio files

## Technical Details

- Uses ffmpeg for high-quality video processing
- Preserves original quality when possible through stream copying
- Falls back to fast, high-quality encoding when precision is required
- Outputs web-optimized MP4 video and AAC audio files

## Supported Formats

- **Input**: MP4, MOV, AVI, MKV
- **Output**: MP4 video + AAC audio

The tool automatically handles format conversion and optimization for web playback.