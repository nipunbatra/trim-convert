#!/bin/bash

# Download script for sample videos
# All videos are verified to be copyright-free and safe to use

echo "Creating sample videos for testing..."
echo "All videos will be copyright-free and safe to use for testing."
echo

# Check if curl is available
if ! command -v curl &> /dev/null; then
    echo "Error: curl is required but not installed."
    exit 1
fi

# Create a temporary directory for downloads
TEMP_DIR=$(mktemp -d)

# Function to download and verify a video
download_video() {
    local url="$1"
    local filename="$2"
    local description="$3"
    
    echo "Downloading $filename - $description"
    
    if curl -L -o "$TEMP_DIR/$filename" "$url"; then
        # Basic verification that we got a video file
        if file "$TEMP_DIR/$filename" | grep -q "video\|MP4\|media"; then
            mv "$TEMP_DIR/$filename" "$filename"
            echo "SUCCESS: Downloaded $filename"
        else
            echo "ERROR: Downloaded file is not a valid video"
            rm -f "$TEMP_DIR/$filename"
            return 1
        fi
    else
        echo "ERROR: Failed to download $filename"
        return 1
    fi
}

# Create sample videos using ffmpeg (ensures they're always available)
echo "Creating sample videos using ffmpeg..."

# Check if ffmpeg is available
if ! command -v ffmpeg &> /dev/null; then
    echo "Error: ffmpeg is required to create sample videos."
    echo "Please install ffmpeg first, then run this script."
    exit 1
fi

# Create 10-second sample video
echo "Creating sample-10s.mp4 (10-second test pattern)..."
ffmpeg -f lavfi -i testsrc2=duration=10:size=1920x1080:rate=30 -f lavfi -i sine=frequency=440:duration=10 -c:v libx264 -preset ultrafast -crf 23 -c:a aac -b:a 128k sample-10s.mp4 -y 2>/dev/null

if [ $? -eq 0 ]; then
    echo "SUCCESS: Created sample-10s.mp4 (10-second test pattern)"
else
    echo "ERROR: Failed to create sample-10s.mp4"
fi

# Create 30-second sample video  
echo "Creating sample-30s.mp4 (30-second test pattern)..."
ffmpeg -f lavfi -i testsrc2=duration=30:size=1280x720:rate=30 -f lavfi -i sine=frequency=1000:duration=30 -c:v libx264 -preset ultrafast -crf 23 -c:a aac -b:a 128k sample-30s.mp4 -y 2>/dev/null

if [ $? -eq 0 ]; then
    echo "SUCCESS: Created sample-30s.mp4 (30-second test pattern)"
else
    echo "ERROR: Failed to create sample-30s.mp4"
fi

# Clean up
rm -rf "$TEMP_DIR"

echo
echo "Sample video creation complete!"
echo "You can now test the video processing tool with these samples:"
echo
echo "Step 1: Trim the 10-second video to first 5 seconds"
echo "  ../trim-convert.sh -e 00:00:05 sample-10s.mp4"
echo
echo "Step 2: Extract middle portion of the 30-second video"
echo "  ../trim-convert.sh -s 00:00:10 -e 00:00:20 sample-30s.mp4"
echo
echo "Step 3: Extract audio from entire video"
echo "  ../trim-convert.sh sample-10s.mp4"