#!/bin/bash

echo "🚀 Setting up Video Trimmer Demo..."

# Install Python dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Run the demo with auto-reload
echo "🎬 Starting Gradio demo with auto-reload..."
echo "💡 The demo will auto-reload when you save changes to video_trimmer_demo.py"
python -c "
import subprocess
import time
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class ReloadHandler(FileSystemEventHandler):
    def __init__(self):
        self.process = None
        self.start_server()
    
    def start_server(self):
        if self.process:
            self.process.terminate()
            self.process.wait()
        print('🔄 Starting/Restarting Gradio server...')
        self.process = subprocess.Popen(['python', 'video_trimmer_demo.py'])
    
    def on_modified(self, event):
        if event.src_path.endswith('video_trimmer_demo.py'):
            print('📝 File changed, reloading...')
            time.sleep(0.5)  # Brief delay to ensure file is fully written
            self.start_server()

handler = ReloadHandler()
observer = Observer()
observer.schedule(handler, '.', recursive=False)
observer.start()

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    observer.stop()
    if handler.process:
        handler.process.terminate()
observer.join()
"