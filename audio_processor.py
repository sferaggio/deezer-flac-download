import argparse
import os
import numpy as np
import librosa
import soundfile as sf
from typing import List, Dict, Tuple, Optional

# Configure logging
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def read_m3u_playlist(file_path: str) -> List[str]:
    """Read audio file paths from an M3U playlist"""
    try:
        with open(file_path, 'r') as f:
            lines = [line.strip() for line in f.readlines()]
        
        # Filter valid audio files and resolve relative paths
        playlist_dir = os.path.dirname(os.path.abspath(file_path))
        valid_extensions = ('.wav', '.mp3', '.flac', '.ogg', '.aiff')
        audio_files = []
        
        for line in lines:
            if line and not line.startswith('#') and line.lower().endswith(valid_extensions):
                # Handle relative paths
                if not os.path.isabs(line):
                    line = os.path.join(playlist_dir, line)
                if os.path.exists(line):
                    audio_files.append(line)
                else:
                    logger.warning(f"File not found in playlist: {line}")
        
        logger.info(f"Found {len(audio_files)} tracks in playlist: {file_path}")
        return audio_files
    except Exception as e:
        logger.error(f"Error reading playlist {file_path}: {str(e)}")
        raise

def analyze_beats(y: np.ndarray, sr: int) -> Tuple[float, np.ndarray, np.ndarray]:
    """
    Analyze BPM and beat positions
    Returns:
        bpm: Estimated tempo
        beat_frames: Frame indices of beats
        beat_times: Time positions of beats (in seconds)
    """
    try:
        tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr, units='frames')
        beat_times = librosa.frames_to_time(beat_frames, sr=sr)
        logger.info(f"Detected BPM: {tempo[0]:.2f}")
        return tempo, beat_frames, beat_times
    except Exception as e:
        logger.error(f"Beat analysis failed: {str(e)}")
        raise

def analyze_key(y: np.ndarray, sr: int) -> Tuple[str, str]:
    """
    Analyze musical key using chromagram and profile correlation
    Returns:
        key: Estimated key (e.g., 'C', 'D#')
        mode: 'major' or 'minor'
    """
    try:
        chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
        chroma_avg = np.mean(chroma, axis=1)
        
        # Key profiles (Krumhansl-Schmuckler)
        major_profile = [6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88]
        minor_profile = [6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17]
        
        # Normalize profiles
        major_profile = np.array(major_profile) / np.sum(major_profile)
        minor_profile = np.array(minor_profile) / np.sum(minor_profile)
        
        correlations = {}
        for shift in range(12):
            rotated = np.roll(chroma_avg, shift)
            correlations[shift] = (
                np.corrcoef(rotated, major_profile)[0, 1],
                np.corrcoef(rotated, minor_profile)[0, 1]
            )
        
        # Find best match
        best_shift = 0
        best_corr = -np.inf
        best_mode = ''
        keys = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        
        for shift, (major_corr, minor_corr) in correlations.items():
            if major_corr > best_corr:
                best_corr = major_corr
                best_shift = shift
                best_mode = 'major'
            if minor_corr > best_corr:
                best_corr = minor_corr
                best_shift = shift
                best_mode = 'minor'
        
        key = keys[best_shift]
        logger.info(f"Detected key: {key} {best_mode}")
        return key, best_mode
    except Exception as e:
        logger.error(f"Key analysis failed: {str(e)}")
        raise

def calculate_segment_novelty(y: np.ndarray, sr: int, beat_frames: np.ndarray) -> np.ndarray:
    """
    Calculate novelty score for beat-synchronous segments
    Returns array of novelty scores for each beat
    """
    try:
        onset_env = librosa.onset.onset_strength(y=y, sr=sr)
        beat_onset_env = librosa.util.sync(onset_env, beat_frames)
        return beat_onset_env
    except Exception as e:
        logger.error(f"Novelty calculation failed: {str(e)}")
        raise

def find_optimal_segment(
    beat_times: np.ndarray,
    novelty_scores: np.ndarray,
    tempo: float,
    min_duration: float = 60.0,
    max_duration: float = 90.0
) -> Tuple[float, float]:
    """
    Find the most interesting segment within duration constraints
    that aligns with musical phrases (multiples of 16/32/64 beats)
    Returns (start_time, end_time)
    """
    try:
        # Calculate possible phrase lengths in beats
        phrase_lengths = [16, 32, 64]
        possible_beat_counts = []
        
        for length in phrase_lengths:
            n_min = int(np.ceil(min_duration * tempo / 60))
            n_max = int(np.floor(max_duration * tempo / 60))
            
            # Find multiples of phrase length within duration range
            n_phrases_min = max(1, int(np.ceil(n_min / length)))
            n_phrases_max = int(np.floor(n_max / length))
            
            for n in range(n_phrases_min, n_phrases_max + 1):
                beat_count = length * n
                if n_min <= beat_count <= n_max:
                    possible_beat_counts.append(beat_count)
        
        if not possible_beat_counts:
            raise ValueError("No valid phrase combinations found for duration constraints")
        
        # Find segment with highest average novelty
        best_score = -np.inf
        best_segment = (0, 0)
        
        for beat_count in sorted(possible_beat_counts, reverse=True):
            for start_idx in range(len(novelty_scores) - beat_count + 1):
                segment_novelty = novelty_scores[start_idx:start_idx+beat_count]
                avg_novelty = np.mean(segment_novelty)
                
                if avg_novelty > best_score:
                    best_score = avg_novelty
                    start_time = beat_times[start_idx]
                    end_time = beat_times[start_idx + beat_count - 1]
                    best_segment = (start_time, end_time)
        
        logger.info(f"Selected segment: {best_segment[0]:.2f}s to {best_segment[1]:.2f}s")
        return best_segment
    except Exception as e:
        logger.error(f"Segment selection failed: {str(e)}")
        raise

def time_stretch_audio(
    y: np.ndarray,
    sr: int,
    original_tempo: float,
    target_tempo: float
) -> np.ndarray:
    """
    Time-stretch audio while preserving pitch using phase vocoder
    Returns stretched audio
    """
    try:
        stretch_factor = original_tempo / target_tempo
        return librosa.effects.time_stretch(y, rate=stretch_factor[0])
    except Exception as e:
        logger.error(f"Time stretching failed: {str(e)}")
        raise

def process_track(
    file_path: str,
    target_tempo: Optional[float] = None,
    min_duration: float = 60.0,
    max_duration: float = 90.0,
    no_stretch: bool = False
) -> Dict:
    """
    Full processing pipeline for a single track
    Returns dictionary with all processing results
    """
    try:
        logger.info(f"Processing: {os.path.basename(file_path)}")
        
        # Load audio
        y, sr = librosa.load(file_path, sr=None, mono=True)
        
        # Analysis stages
        tempo, beat_frames, beat_times = analyze_beats(y, sr)
        key, mode = analyze_key(y, sr)
        novelty = calculate_segment_novelty(y, sr, beat_frames)
        start_time, end_time = find_optimal_segment(beat_times, novelty, tempo, min_duration, max_duration)
        
        # Extract segment
        start_sample = int(start_time * sr)
        end_sample = int(end_time * sr)
        segment = y[start_sample:end_sample]
        
        # Time stretching if needed and not disabled
        if target_tempo and abs(tempo - target_tempo) > 1 and not no_stretch:
            logger.info(f"Stretching from {tempo[0]:.2f} BPM to {target_tempo:.2f} BPM")
            segment = time_stretch_audio(segment, sr, tempo, target_tempo)
        elif target_tempo and not no_stretch:
            logger.info(f"Tempo already matches target ({target_tempo:.2f} BPM)")
        
        return {
            'audio': segment,
            'sr': sr,
            'tempo': tempo,
            'key': key,
            'mode': mode,
            'start_time': start_time,
            'end_time': end_time,
            'file_name': os.path.basename(file_path)
        }
    except Exception as e:
        logger.error(f"Failed to process {file_path}: {str(e)}")
        raise

def process_group(files: List[str], output_dir: str, no_stretch: bool = False) -> None:
    """Process a group of files with tempo normalization"""
    # First pass: analyze all tempos
    tempos = []
    for file in files:
        y, sr = librosa.load(file, sr=None, mono=True)
        tempo, _, _ = analyze_beats(y, sr)
        tempos.append(tempo)
    
    avg_tempo = np.mean(tempos)
    logger.info(f"Group average BPM: {avg_tempo:.2f}")
    
    # Second pass: process with tempo normalization
    os.makedirs(output_dir, exist_ok=True)
    for file in files:
        result = process_track(file, target_tempo=avg_tempo, no_stretch=no_stretch)
        output_path = os.path.join(output_dir, f"processed_{result['file_name']}")
        sf.write(output_path, result['audio'], result['sr'])
        logger.info(f"Exported: {output_path}")

def main():
    parser = argparse.ArgumentParser(
        description="Audio Processor: Extract optimal segments with tempo/key normalization",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "files", 
        nargs="*",
        help="Audio files to process"
    )
    parser.add_argument(
        "-p", "--playlist",
        help="M3U playlist file containing audio tracks"
    )
    parser.add_argument(
        "-o", "--output-dir",
        default="output",
        help="Output directory for processed files"
    )
    parser.add_argument(
        "--min-duration",
        type=float,
        default=60.0,
        help="Minimum segment duration in seconds"
    )
    parser.add_argument(
        "--max-duration",
        type=float,
        default=90.0,
        help="Maximum segment duration in seconds"
    )
    parser.add_argument(
        "--no-stretch",
        action="store_true",
        help="Skip time stretching to average BPM"
    )
    
    args = parser.parse_args()
    
    try:
        all_files = []
        
        # Add individual files
        all_files.extend(args.files)
        
        # Add playlist files if specified
        if args.playlist:
            playlist_files = read_m3u_playlist(args.playlist)
            all_files.extend(playlist_files)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_files = [f for f in all_files if not (f in seen or seen.add(f))]
        
        if not unique_files:
            logger.error("No valid audio files found in input")
            exit(1)
        
        logger.info(f"Processing {len(unique_files)} files")
        process_group(unique_files, args.output_dir, no_stretch=args.no_stretch)
        logger.info("Processing completed successfully")
    except Exception as e:
        logger.exception("Fatal error during processing")
        exit(1)

if __name__ == "__main__":
    main()
