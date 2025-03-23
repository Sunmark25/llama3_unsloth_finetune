import os
import re
import json
import glob
from pathlib import Path

def parse_transcript(file_path):
    """Parse transcript file with timestamps, return a list of paragraphs"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Use regular expressions to match timestamps and text
    # Format example: "00:25 Good morning, how are you?"
    segments = re.findall(r'(\d+:\d+)\s+(.*?)(?=\n\d+:\d+|\n\n|\Z)', content, re.DOTALL)
    
    # Process matching results into paragraphs
    paragraphs = []
    current_paragraph = ""
    
    for timestamp, text in segments:
        text = text.strip()
        if text:
            if current_paragraph:
                current_paragraph += " " + text
            else:
                current_paragraph = text
            
            # If the text ends with a period, question mark, or exclamation mark, consider it the end of a paragraph
            if re.search(r'[.?!。？！]\s*$', text):
                paragraphs.append(current_paragraph)
                current_paragraph = ""
    
    # Add the last paragraph (if any)
    if current_paragraph:
        paragraphs.append(current_paragraph)
    
    return paragraphs

def create_alpaca_data(cn_file, en_file, translation_direction="en2cn"):
    """
    Create Alpaca format data based on Chinese and English files
    
    Parameters:
    cn_file: Chinese transcript file path
    en_file: English transcript file path
    translation_direction: Translation direction, "en2cn" means English to Chinese, "cn2en" means Chinese to English
    """
    cn_paragraphs = parse_transcript(cn_file)
    en_paragraphs = parse_transcript(en_file)
    
    # Ensure paragraph counts match, take the smaller count
    min_length = min(len(cn_paragraphs), len(en_paragraphs))
    
    alpaca_data = []
    
    talk_name = Path(en_file).stem.split(' * ')[0]  # Extract the talk title
    
    if translation_direction == "en2cn":
        instruction = f"Translate the following English TED Talk segment from '{talk_name}' into Chinese."
        for i in range(min_length):
            alpaca_data.append({
                "instruction": instruction,
                "input": en_paragraphs[i],
                "output": cn_paragraphs[i]
            })
    else:  # cn2en
        instruction = f"Translate the following Chinese TED Talk segment from '{talk_name}' into English."
        for i in range(min_length):
            alpaca_data.append({
                "instruction": instruction,
                "input": cn_paragraphs[i],
                "output": en_paragraphs[i]
            })
    
    return alpaca_data

def main():
    # Command-line argument parsing
    import argparse
    parser = argparse.ArgumentParser(description='Convert TED Talk transcripts to Alpaca format')
    parser.add_argument('--dir', type=str, default='Ted_Talk', help='Directory containing TED Talk transcripts')
    parser.add_argument('--output', type=str, default='alpaca_data.json', help='Output JSON file')
    parser.add_argument('--direction', type=str, choices=['en2cn', 'cn2en', 'both'], default='both',
                        help='Translation direction: en2cn, cn2en, or both')
    args = parser.parse_args()
    
    ted_dir = args.dir
    all_files = os.listdir(ted_dir)
    
    # Find all CN and EN file pairs.
    cn_files = sorted([os.path.join(ted_dir, f) for f in all_files if f.endswith('CN.txt')])
    en_files = sorted([os.path.join(ted_dir, f) for f in all_files if f.endswith('EN.txt')])
    
    # Ensure the number of file pairs matches
    assert len(cn_files) == len(en_files), "CN and EN file counts don't match"
    
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
    
    # Save data as a JSON file
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(all_alpaca_data, f, ensure_ascii=False, indent=2)
    
    print(f"Conversion complete! Total examples: {len(all_alpaca_data)}")
    print(f"Data saved to {args.output}")

if __name__ == "__main__":
    main()