import re

# Path to your log file
log_file_path = "/Users/dean/Downloads/tracks.log"
# Path to save the .m3u playlist
playlist_file_path = "playlist.m3u"

# Regex patterns to match file paths
patterns = [
    r"Wrote \d+ bytes: (.+\.flac)",  # Pattern for "Wrote ... bytes" lines
    r'Path "(.+\.flac)" already exists'  # Pattern for "Path ... already exists" lines
]

# List to store file paths
file_paths = []

# Read the log file and extract file paths
with open(log_file_path, 'r') as log_file:
    for line in log_file:
        for pattern in patterns:
            match = re.search(pattern, line)
            if match:
                file_paths.append(match.group(1))
                break

# Write the .m3u playlist file
with open(playlist_file_path, 'w') as playlist_file:
    playlist_file.write("#EXTM3U\n")
    playlist_file.writelines(f"{path}\n" for path in file_paths)

print(f"Playlist saved as {playlist_file_path}")
