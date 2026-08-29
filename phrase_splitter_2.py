import argparse
import librosa
import numpy as np
import soundfile as sf
from scipy.signal import find_peaks
from math import ceil
import pathlib

def detect_phrases(input_path, output_dir, min_phrase_beats=16, max_phrase_beats=64):
    # Load audio with high precision
    y, sr = librosa.load(input_path, sr=None, mono=True)
    
    # Detect tempo and beats
    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr, units='frames')
    beat_times = librosa.frames_to_time(beat_frames, sr=sr)
    
    # If not enough beats detected, generate evenly spaced beats using estimated tempo
    if len(beat_times) < 10:
        duration = librosa.get_duration(y=y, sr=sr)
        beat_times = np.arange(0, duration, 60/tempo)
    
    # Convert beat times to sample indices
    beat_samples = (beat_times * sr).astype(int)
    
    # Calculate RMS energy for each beat segment
    rms_energy = []
    for i in range(len(beat_samples)-1):
        segment = y[beat_samples[i]:beat_samples[i+1]]
        rms_energy.append(np.sqrt(np.mean(segment**2)))
    
    # Find phrase boundaries using energy changes
    energy_diff = np.abs(np.diff(rms_energy))
    peaks, _ = find_peaks(energy_diff, 
                        distance=min_phrase_beats,
                        prominence=np.percentile(energy_diff, 75))
    
    # Create phrase groups based on energy peaks and typical lengths
    phrase_boundaries = [0] + sorted(peaks) + [len(beat_samples)-1]
    phrases = []
    
    # Merge boundaries based on typical phrase lengths
    final_boundaries = [0]
    for boundary in phrase_boundaries[1:-1]:
        phrase_length = boundary - final_boundaries[-1]
        nearest_multiple = min_phrase_beats * round(phrase_length/min_phrase_beats)
        if abs(phrase_length - nearest_multiple) > min_phrase_beats/2:
            final_boundaries.append(boundary)
        else:
            final_boundaries.append(final_boundaries[-1] + nearest_multiple)
    
    final_boundaries.append(len(beat_samples)-1)
    
    pathlib.Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Split audio into phrases and save
    for i in range(len(final_boundaries)-1):
        start_beat = final_boundaries[i]
        end_beat = final_boundaries[i+1]
        
        # Get start/end samples with 50ms fade-in/out
        start_sample = max(0, beat_samples[start_beat] - int(0.05 * sr))
        end_sample = min(len(y), beat_samples[end_beat] + int(0.05 * sr))
        
        phrase = y[start_sample:end_sample]
        sf.write(f"{output_dir}/phrase_{i+1:03d}.wav", phrase, sr)
    
    return len(final_boundaries)-1

if __name__ == "__main__":
    root = '/Users/dean/dj/music/deezer/v3/'  # Harcoded for now

    parser = argparse.ArgumentParser()
    parser.add_argument("input_file", help="Path to input audio file")
    parser.add_argument("output_dir", help="Directory to save phrase segments")
    args = parser.parse_args()
    
    prefix = args.input_file.replace(root, '').split('.')[0]

    num_phrases = detect_phrases(args.input_file, f"{args.output_dir}/{prefix}")
    print(f"Created {num_phrases} phrase segments in {args.output_dir}")
