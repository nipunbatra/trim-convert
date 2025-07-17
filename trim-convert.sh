#!/bin/bash

# Simple and fast MP4 trimming script for macOS

# Parse command line options
if [ "$1" == "-h" ] || [ "$1" == "--help" ]; then
    echo "Usage: $0 [options] input.mp4"
    echo "Options:"
    echo "  -s, --start TIME    Start time (format: HH:MM:SS, default: beginning of file)"
    echo "  -e, --end TIME      End time (format: HH:MM:SS, default: end of file)"
    echo "  -o, --output PREFIX Output file prefix (default: trimmed)"
    echo "  -h, --help          Show this help message"
    exit 1
fi

# Initialize variables with defaults
START_TIME=""
END_TIME=""
OUTPUT_PREFIX="trimmed"
INPUT_FILE=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -s|--start)
            START_TIME="$2"
            shift 2
            ;;
        -e|--end)
            END_TIME="$2"
            shift 2
            ;;
        -o|--output)
            OUTPUT_PREFIX="$2"
            shift 2
            ;;
        *)
            # Assume the last argument is the input file
            INPUT_FILE="$1"
            shift
            ;;
    esac
done

# Check if input file is provided
if [ -z "$INPUT_FILE" ]; then
    echo "Error: No input file specified."
    exit 1
fi

# Validate input file exists
if [ ! -f "$INPUT_FILE" ]; then
    echo "Error: Input file '$INPUT_FILE' does not exist."
    exit 1
fi

# Extract file extension
EXT="${INPUT_FILE##*.}"

# Output file names
VIDEO_OUTPUT="${OUTPUT_PREFIX}.${EXT}"
AUDIO_OUTPUT="${OUTPUT_PREFIX}.aac"

echo "🎬 Processing video: $INPUT_FILE"

# Get video duration
duration=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$INPUT_FILE")

# Build ffmpeg command based on parameters
FF_CMD="ffmpeg -v warning -stats -i \"$INPUT_FILE\""

# Add start time if specified
if [ ! -z "$START_TIME" ]; then
    FF_CMD="$FF_CMD -ss $START_TIME"
    echo "⏱️  Start time: $START_TIME"
else
    echo "⏱️  Start time: Beginning of file"
fi

# Add end time if specified
if [ ! -z "$END_TIME" ]; then
    FF_CMD="$FF_CMD -to $END_TIME"
    echo "⏱️  End time: $END_TIME"
else
    echo "⏱️  End time: End of file"
fi

# Try to use stream copy for speed
echo "🔄 Processing video - using fast copy method..."
FF_CMD="$FF_CMD -c:v copy -c:a copy -avoid_negative_ts 1 \"$VIDEO_OUTPUT\""

# Execute the command
eval $FF_CMD

# Check if the command succeeded
if [ $? -ne 0 ]; then
    echo "⚠️  Fast method failed, trying with re-encoding..."
    # If stream copy failed, fall back to re-encoding
    FF_CMD="ffmpeg -v warning -stats -i \"$INPUT_FILE\""
    
    # Add time parameters again
    if [ ! -z "$START_TIME" ]; then
        FF_CMD="$FF_CMD -ss $START_TIME"
    fi
    
    if [ ! -z "$END_TIME" ]; then
        FF_CMD="$FF_CMD -to $END_TIME"
    fi
    
    # Use encoding parameters
    FF_CMD="$FF_CMD -c:v libx264 -preset ultrafast -crf 17 -c:a aac -b:a 128k \"$VIDEO_OUTPUT\""
    
    # Execute the fallback command
    eval $FF_CMD
fi

echo "🎵 Extracting audio (AAC)..."
ffmpeg -v warning -stats -i "$VIDEO_OUTPUT" -vn -acodec copy "$AUDIO_OUTPUT"

# Get file sizes
video_size=$(du -h "$VIDEO_OUTPUT" | cut -f1)
audio_size=$(du -h "$AUDIO_OUTPUT" | cut -f1)

echo "✅ Done!"
echo "📼 Trimmed video: $VIDEO_OUTPUT ($video_size)"
echo "🔊 Audio file: $AUDIO_OUTPUT ($audio_size)"