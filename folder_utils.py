import re
import logging

logger = logging.getLogger(__name__)

def extract_drive_folder_id(input_str):
    """Extract folder ID from Drive folder link or return input if it's already a folder ID"""
    if not input_str:
        return None
    
    input_str = input_str.strip()
    logger.info(f"🗂️ Extracting folder ID from: {input_str}")
    
    # Check if it's a Drive folder link - comprehensive patterns
    folder_link_patterns = [
        r'https://drive\.google\.com/drive/folders/([a-zA-Z0-9-_]+)',
        r'drive\.google\.com/drive/folders/([a-zA-Z0-9-_]+)',  # Without https
        r'/folders/([a-zA-Z0-9-_]+)',  # Just the /folders/ part
        r'folders/([a-zA-Z0-9-_]+)'   # Without leading slash
    ]
    
    for pattern in folder_link_patterns:
        match = re.search(pattern, input_str)
        if match:
            folder_id = match.group(1)
            logger.info(f"✅ Extracted folder ID: {folder_id}")
            return folder_id
    
    # Check if it's already a folder ID (alphanumeric string with hyphens/underscores)
    if re.match(r'^[a-zA-Z0-9-_]{25,}$', input_str):  # At least 25 chars for Drive folder IDs
        logger.info(f"✅ Using direct folder ID: {input_str}")
        return input_str
    
    logger.warning(f"❌ Could not extract folder ID from: {input_str}")
    return None