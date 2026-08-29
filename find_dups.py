import os

def get_flac_files_in_album_dirs(root_dir):
    """Gets all .flac files in directories that have more than one .flac file (i.e., album directories)."""
    album_dirs = {}
    for foldername, _, filenames in os.walk(root_dir):
        # Filter out only .flac files in the current directory
        flac_files = [f for f in filenames if f.endswith('.flac')]
        if len(flac_files) > 1:  # Consider it an album directory only if there is more than one .flac file
            album_dirs[foldername] = flac_files
    return album_dirs

def compare_file_size(size1, size2, threshold_kb=100):
    """Compares if two file sizes are within the threshold (in KB)."""
    return abs(size1 - size2) <= threshold_kb * 1024

def is_filename_subset(filename1, filename2):
    """Checks if filename1 (without extension) is a subset of filename2 or vice versa."""
    name1 = os.path.splitext(filename1)[0]
    name2 = os.path.splitext(filename2)[0]
    return name1 in name2 or name2 in name1

def find_similar_flac_pairs(album_dirs):
    """Finds similar flac file pairs based on size and filename subset condition."""
    for folder, flac_files in album_dirs.items():
        # Create a list of (file_path, file_size) tuples for each .flac file in the album directory
        file_paths = [(os.path.join(folder, f), os.path.getsize(os.path.join(folder, f))) for f in flac_files]
        
        # Compare each pair of files for size similarity and filename subset
        for i in range(len(file_paths)):
            for j in range(i + 1, len(file_paths)):
                file1, size1 = file_paths[i]
                file2, size2 = file_paths[j]
                
                if compare_file_size(size1, size2) and is_filename_subset(os.path.basename(file1), os.path.basename(file2)):
                    # Print the full location of the file with its stem name (excluding the .flac extension)
                    print(f"rm '{os.path.splitext(file2)[0]}.flac'")
                    os.remove(f"{os.path.splitext(file2)[0]}.flac")

def main(root_dir):
    album_dirs = get_flac_files_in_album_dirs(root_dir)
    if not album_dirs:
        print("No album directories found.")
        return
    
    find_similar_flac_pairs(album_dirs)

if __name__ == "__main__":
    # Provide the root directory here
    root_directory = "/Users/dean/dj/music/deezer"
    main(root_directory)
