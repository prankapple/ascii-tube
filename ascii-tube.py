import cv2
import os
import sys
import numpy as np
import shutil
from yt_dlp import YoutubeDL
from colorama import init

# Initialize Colorama for colored text in terminal
init()

# Block characters for conversion (in order of increasing "intensity")
BLOCK_CHARS = [' ', '░', '▒', '▓', '█']

def get_terminal_size():
    """Get the current size of the terminal."""
    try:
        size = shutil.get_terminal_size((80, 20))  # Default size if detection fails
        return size.columns, size.lines
    except:
        return 80, 20

def image_to_ascii_with_color(image, width):
    """Convert an image frame to blocks with color."""
    height, original_width, _ = image.shape
    aspect_ratio = height / original_width
    new_height = int(width * aspect_ratio * 0.55)  # Adjust height for block aspect ratio
    
    # Resize the image once, instead of repeatedly resizing inside loops
    resized_image = cv2.resize(image, (width, new_height))
    
    # Convert to grayscale and normalize using vectorized NumPy operations
    grayscale_image = cv2.cvtColor(resized_image, cv2.COLOR_BGR2GRAY)
    min_val, max_val = np.min(grayscale_image), np.max(grayscale_image)
    max_val = max_val if max_val != min_val else min_val + 1  # Avoid division by zero
    normalized_image = np.clip((grayscale_image - min_val) / (max_val - min_val) * 255, 0, 255).astype(np.uint8)
    
    # Vectorize ASCII character selection
    indices = (normalized_image / 255 * (len(BLOCK_CHARS) - 1)).astype(np.int32)
    ascii_image = np.array(BLOCK_CHARS)[indices]

    # Convert image to ANSI colored string with vectorized color selection
    r, g, b = resized_image[..., 2], resized_image[..., 1], resized_image[..., 0]
    color_str = "\n".join("".join(f"\033[38;2;{r[i,j]};{g[i,j]};{b[i,j]}m{ascii_image[i,j]}\033[0m" 
                                  for j in range(ascii_image.shape[1])) for i in range(ascii_image.shape[0]))

    return color_str

def play_video_as_ascii_with_color(video_path, frame_skip=2):
    """Play video as blocks in the terminal with color."""
    term_width, _ = get_terminal_size()
    frame_width = min(term_width, 80)  # Restrict to terminal size or 80 for performance

    # Open the video using OpenCV
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        print("\033[1;31mError: Unable to open video.\033[0m")
        return
    
    frame_count = 0
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break  # Exit if video has ended
            
            # Skip frames for better performance
            if frame_count % frame_skip != 0:
                frame_count += 1
                continue

            # Convert and display the frame as ASCII blocks with color
            block_frame = image_to_ascii_with_color(frame, width=frame_width)
            os.system('cls' if os.name == 'nt' else 'clear')
            print(block_frame)
            
            # Control frame rate and performance
            if cv2.waitKey(1) == 27:  # Break on 'ESC' key press
                break

            frame_count += 1

    except KeyboardInterrupt:
        pass
    finally:
        cap.release()

def download_youtube_video(url):
    """Download YouTube video using yt-dlp."""
    ydl_opts = {
        'format': 'mp4[height<=360]',  # Download a video with resolution 360p or lower for better performance
        'outtmpl': 'video.mp4',  # Downloaded video will be saved as 'video.mp4'
        'quiet': True
    }
    try:
        with YoutubeDL(ydl_opts) as ydl:
            print("\033[1;32mDownloading video...\033[0m")
            ydl.download([url])
            return 'video.mp4'
    except Exception as e:
        print(f"\033[1;31mError downloading video: {e}\033[0m")
        return None

if __name__ == "__main__":
    # Prompt the user for the YouTube URL
    video_url = input("\033[1;34mEnter YouTube URL: \033[0m")

    # Step 1: Download the YouTube video
    video_path = download_youtube_video(video_url)
    
    if video_path:
        # Step 2: Play the video as blocks in the terminal
        play_video_as_ascii_with_color(video_path, frame_skip=3)  # Skipping every 3rd frame for performance

        # Step 3: Clean up by removing the downloaded video
        os.remove(video_path)
