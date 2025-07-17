# Demo Videos

This directory contains sample videos for testing the video processing tool.

## Available Videos

### sample-10s.mp4
- **Duration**: 10 seconds
- **Resolution**: 1920x1080
- **Video**: Colorful test pattern with moving elements
- **Audio**: 440Hz sine wave tone (perfect for testing audio extraction)
- **Source**: Generated using ffmpeg
- **License**: Public Domain (generated content)
- **Download**: Run `./download-samples.sh` to create this file

### sample-30s.mp4
- **Duration**: 30 seconds
- **Resolution**: 1280x720
- **Video**: Colorful test pattern with moving elements
- **Audio**: 1000Hz sine wave tone (different frequency for variety)
- **Source**: Generated using ffmpeg
- **License**: Public Domain (generated content)
- **Download**: Run `./download-samples.sh` to create this file

## Usage

**Step 1:** Create the sample videos
```bash
./download-samples.sh
```

**Step 2:** Test the video processing tool with these samples

Trim the 10-second video to first 5 seconds:
```bash
../trim-convert.sh -e 00:00:05 sample-10s.mp4
```

Extract middle portion of the 30-second video:
```bash
../trim-convert.sh -s 00:00:10 -e 00:00:20 sample-30s.mp4
```

Extract audio from the entire video:
```bash
../trim-convert.sh sample-10s.mp4
```

**Step 3:** Check the output files
```bash
ls -la trimmed.*
```

## License Information

All videos in this directory are generated content and are free to use, modify, and distribute:

- **Public Domain**: Generated test patterns have no copyright restrictions
- **Safe to use**: Perfect for testing and development without any legal concerns
- **No attribution required**: Use freely in your projects

These videos are created using ffmpeg's built-in test pattern generators, making them completely safe for any use case.