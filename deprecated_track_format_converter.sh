#!/bin/bash

# Script: deprecated_track_format_converter.sh
# Status: DEPRECATED - superseded by ./track_format_converter, which handles
#         more source formats, caps quality instead of guessing, and manages
#         playlists. Kept only for reference.
# Description: Convert FLAC files from an M3U playlist to XDJ-700 compatible AIFF and MP3 formats
# Usage: ./deprecated_track_format_converter.sh <path_to_m3u_playlist>

# Check if input provided
if [ $# -eq 0 ]; then
    echo "Usage: $0 <path_to_m3u_playlist>"
    exit 1
fi

M3U_FILE="$1"

# Check if file exists
if [ ! -f "$M3U_FILE" ]; then
    echo "Error: M3U playlist '$M3U_FILE' not found!"
    exit 1
fi

# Get playlist name without extension
PLAYLIST_NAME=$(basename "$M3U_FILE" .m3u)
if [ "$PLAYLIST_NAME" = "$(basename "$M3U_FILE")" ]; then
    echo "Error: Playlist must have .m3u extension!"
    exit 1
fi

# Create output directories
QUALITY_DIR="$HOME/Music/QUALITY_${PLAYLIST_NAME}"
MP3_DIR="$HOME/Music/MP3_${PLAYLIST_NAME}"

mkdir -p "$QUALITY_DIR"
mkdir -p "$MP3_DIR"

echo "Processing playlist: $PLAYLIST_NAME"
echo "Quality output directory: $QUALITY_DIR"
echo "MP3 output directory: $MP3_DIR"

# Process each file in the playlist
CONVERSION_ERRORS=0
PROCESSED_COUNT=0

while IFS= read -r LINE; do
    echo "Text read from file: $LINE"

    # Skip #EXTM3U line
    if [ "$LINE" = "#EXTM3U" ]; then
        continue
    fi

    # Get filename without path
    FILENAME=$(basename "$LINE")
    
    # Get filename without extension and clean it (remove numeric prefixes)
    BASENAME=$(basename "$LINE" .flac)
    CLEAN_BASENAME=$(echo "$BASENAME" | sed -E 's/^[0-9]+[[:space:]]*//')
    
    echo "Processing: $CLEAN_BASENAME"
    
    # AIFF conversion (for QUALITY folder)
    AIFF_OUTPUT="$QUALITY_DIR/${CLEAN_BASENAME}.aiff"
    echo "Converting to AIFF: $AIFF_OUTPUT"
    

    ffmpeg -nostdin -i "$LINE" -write_id3v2 1 -c:v copy -acodec pcm_s16le -ar 44100 -ac 2 -map_metadata 0 -id3v2_version 3 "$AIFF_OUTPUT" >> "/tmp/ffmpeg-aiff-$(date).log" 2>&1
    
    # MP3 conversion (for MP3 folder)
    MP3_OUTPUT="$MP3_DIR/${CLEAN_BASENAME}.mp3"
    echo "Converting to MP3: $MP3_OUTPUT"
    
    ffmpeg -nostdin -i "$LINE" -c:v copy -acodec libmp3lame -ab 320k -ar 44100 -ac 2 -map_metadata 0 -id3v2_version 3 -write_id3v1 1 "$MP3_OUTPUT" >> "/tmp/ffmpeg-mp3-$(date).log" 2>&1
    
    echo "Successfully processed: $CLEAN_BASENAME"
    PROCESSED_COUNT=$((PROCESSED_COUNT + 1))
    
done < "$M3U_FILE"

echo "Conversion complete!"
echo "Processed $PROCESSED_COUNT files successfully."
echo "Files saved to:"
echo "  - AIFF: $QUALITY_DIR"
echo "  - MP3: $MP3_DIR"

if [ $CONVERSION_ERRORS -gt 0 ]; then
    echo "There were $CONVERSION_ERRORS conversion errors. Some files may not have been processed correctly."
else
    echo "All files were converted successfully."
fi
