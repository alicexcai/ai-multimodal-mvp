import os

print(sorted([int(name.replace(".mp4", "")) for name in os.listdir('data/video_clips')]))