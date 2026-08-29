import librosa
import numpy as np
from scipy.signal import find_peaks
import soundfile as sf
import os
import pathlib

def detect_phrases(input_path, output_prefix, prominence=0.5, distance=20):
    """
    Split a music track into phrases based on audio feature changes.
    
    Parameters:
    input_path (str): Path to input audio file
    output_prefix (str): Prefix for output files
    prominence (float): Minimum prominence for peak detection (0-1)
    distance (int): Minimum number of frames between peaks
    
    Returns:
    int: Number of detected phrases
    """
    # Load audio file
    y, sr = librosa.load(input_path, sr=None)
    
    # Extract features
    hop_length = 512
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13, hop_length=hop_length)
    chroma = librosa.feature.chroma_cqt(y=y, sr=sr, hop_length=hop_length)
    
    # Normalize features
    mfcc = librosa.util.normalize(mfcc)
    chroma = librosa.util.normalize(chroma)
    
    # Compute novelty curve using combined features
    novelty = np.sum(np.diff(mfcc, axis=1)**2, axis=0) + np.sum(np.diff(chroma, axis=1)**2, axis=0)
    
    # Find peaks in novelty curve
    peaks, _ = find_peaks(novelty, 
                         prominence=prominence*np.max(novelty),
                         distance=distance)
    
    # Convert peaks to sample indices
    boundaries = [0] + (peaks * hop_length).tolist() + [len(y)]
    
    # Split and save phrases
    pathlib.Path(output_prefix).mkdir(parents=True, exist_ok=True)
    for i in range(len(boundaries)-1):
        start = boundaries[i]
        end = boundaries[i+1]
        phrase = y[start:end]
        sf.write(f"{output_prefix}/phrase_{i:03}.wav", phrase, sr)
    
    return len(boundaries)-1

# Example usage
prefix = "Frankel & Harper/Trimmers EP/0103 Frankel & Harper - Trimmers (Instinct UK Remix)"
num_phrases = detect_phrases(f"/Users/dean/dj/music/deezer/v3/{prefix}.flac", f"/Users/dean/dj/music/phrases/{prefix}/")
print(f"Detected {num_phrases} phrases")
