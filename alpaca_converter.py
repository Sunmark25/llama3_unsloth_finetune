import os
import re
import json
import glob
from pathlib import Path

def parse_transcript(file_path):
    """Parse text file with timestamps, return a list of (timestamp, text) pairs"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Directly match timestamps and corresponding text, without trying to merge into paragraphs
    segments = re.findall(r'(\d+:\d+)\s+(.*?)(?=\n\d+:\d+|\n\n|\Z)', content, re.DOTALL)
    
    # Process matching results, return a list of (timestamp, cleaned text) tuples
    result = []
    for timestamp, text in segments:
        text = text.strip()
        if text:  # Only include non-empty text
            result.append((timestamp, text))
    
    return result

def create_alpaca_data(cn_file, en_file, translation_direction="en2cn"):
    """
    Create aligned Alpaca format data based on timestamps
    
    Parameters:
    cn_file: Path to Chinese text file
    en_file: Path to English text file
    translation_direction: Translation direction, "en2cn" means English to Chinese, "cn2en" means Chinese to English
    """
    # Parse texts of both languages, get lists of (timestamp, text)
    cn_segments = parse_transcript(cn_file)
    en_segments = parse_transcript(en_file)
    
    # Create mappings from timestamps to text
    cn_map = {timestamp: text for timestamp, text in cn_segments}
    en_map = {timestamp: text for timestamp, text in en_segments}
    
    # Find timestamps common to both languages
    common_timestamps = sorted(set(cn_map.keys()) & set(en_map.keys()))
    
    # Report timestamp matching status
    print(f"Chinese segments: {len(cn_segments)}, English segments: {len(en_segments)}")
    print(f"Matching timestamps: {len(common_timestamps)}")
    
    if len(cn_segments) != len(en_segments):
        print(f"Warning: Chinese and English segment counts differ, difference: {abs(len(cn_segments) - len(en_segments))}")
    
    if len(common_timestamps) < min(len(cn_segments), len(en_segments)):
        print(f"Warning: {min(len(cn_segments), len(en_segments)) - len(common_timestamps)} segments ignored due to timestamp mismatch")
    
    # Extract talk name
    talk_name = Path(en_file).stem.split(' * ')[0]
    
    # Create Alpaca data based on translation direction
    alpaca_data = []
    
    if translation_direction == "en2cn":
        instruction = f"Translate the following TED Talk segment from '{talk_name}' into Chinese."
        for timestamp in common_timestamps:
            alpaca_data.append({
                "instruction": instruction,
                "input": en_map[timestamp],
                "output": cn_map[timestamp]
            })
    else:  # cn2en
        instruction = f"Translate the following TED Talk segment from '{talk_name}' into English."
        for timestamp in common_timestamps:
            alpaca_data.append({
                "instruction": instruction,
                "input": cn_map[timestamp],
                "output": en_map[timestamp]
            })
    
    return alpaca_data

def main():
    # Command-line argument parsing
    import argparse
    parser = argparse.ArgumentParser(description='Convert TED Talk transcripts to timestamp-aligned Alpaca format')
    parser.add_argument('--dir', type=str, default='clean_translated_transcript', help='Directory containing TED Talk transcripts')
    parser.add_argument('--output', type=str, default='alpaca_data.json', help='Output JSON file')
    parser.add_argument('--direction', type=str, choices=['en2cn', 'cn2en', 'both'], default='both',
                        help='Translation direction: en2cn, cn2en, or both')
    args = parser.parse_args()
    
    ted_dir = args.dir
    all_files = os.listdir(ted_dir)
    
    # Find all Chinese and English file pairs
    cn_files = sorted([os.path.join(ted_dir, f) for f in all_files if f.endswith('CN.txt')])
    en_files = sorted([os.path.join(ted_dir, f) for f in all_files if f.endswith('EN.txt')])
    
    # Ensure file pair counts match
    if len(cn_files) != len(en_files):
        print(f"Error: Chinese file count ({len(cn_files)}) does not match English file count ({len(en_files)})!")
        return
    
    all_alpaca_data = []
    
    # Process each file pair
    for cn_file, en_file in zip(cn_files, en_files):
        print(f"Processing {Path(cn_file).name} and {Path(en_file).name}...")
        
        # Generate data based on selected direction
        if args.direction in ['en2cn', 'both']:
            en2cn_data = create_alpaca_data(cn_file, en_file, "en2cn")
            all_alpaca_data.extend(en2cn_data)
            print(f"  Added {len(en2cn_data)} English to Chinese examples")
            
        if args.direction in ['cn2en', 'both']:
            cn2en_data = create_alpaca_data(cn_file, en_file, "cn2en")
            all_alpaca_data.extend(cn2en_data)
            print(f"  Added {len(cn2en_data)} Chinese to English examples")
    
    # Save as JSON file
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(all_alpaca_data, f, ensure_ascii=False, indent=2)
    
    print(f"Conversion complete! Total examples: {len(all_alpaca_data)}")
    print(f"Data saved to {args.output}")

if __name__ == "__main__":
    main()