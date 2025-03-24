import argparse
import re
import os


# How to run this script on terminal:
# python update.py "Ted_Talk/ted_talk_cn.txt" "Ted_Talk/ted_talk_en.txt"
# Ex. python3 update.py "Ted_Talk/Elon Musk_ The future we're building -- and boring _ TED - CN.txt" "Ted_Talk/Elon Musk_ The future we're building -- and boring _ TED - EN.txt"
# Testing...
# The script will output the following files:
# - ted_talk_cn_newfix.txt (flattened and cleaned Chinese transcript)
# - ted_talk_en_newfix.txt  (flattened and cleaned English transcript)
# - ted_talk_en_updated.txt (English transcript with updated timestamps)
# - ted_talk_en_update_log.txt  (Log file detailing the changes made to the English transcript)


# Regex pattern for a timestamp at the start of a line (format: MM:SS)
timestamp_pattern = re.compile(r'^(\d{2}:\d{2})')

def clean_line(line):
    """
    Remove any text enclosed in parentheses, either standard or full-width.
    For example, it removes (Laughter), (Audience), (Applause), （笑声）.
    """
    # This regex matches both types of parentheses.
    cleaned = re.sub(r'[（\(][^）\)]*[）\)]', '', line)
    return cleaned.strip()

def flatten_transcript(file_path):
    """
    Reads the transcript file and flattens it so that each segment (starting with a timestamp)
    is combined into a single line.
    
    For any line, if (after stripping leading spaces) it starts with "(" or "（",
    it is skipped entirely.
    
    Returns a list of tuples: (timestamp, full_text).
    """
    segments = []
    current_timestamp = None
    current_text = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for raw_line in f:
            # Remove newline and surrounding spaces.
            line = raw_line.rstrip("\n").strip()
            if not line:
                continue  # Skip empty lines.
            # If the entire line (before processing timestamp) starts with a parenthesis, skip it.
            if line.lstrip().startswith("(") or line.lstrip().startswith("（"):
                continue
            # Check if the line starts with a timestamp.
            match = timestamp_pattern.match(line)
            if match:
                # Extract timestamp and content.
                ts = match.group(1)
                content = line[len(ts):].strip()
                # If the content (after timestamp) starts with a parenthesis, skip this segment.
                if content.lstrip().startswith("(") or content.lstrip().startswith("（"):
                    continue
                # If there's an ongoing segment, save it.
                if current_timestamp is not None and current_text:
                    segments.append((current_timestamp, " ".join(current_text)))
                current_timestamp = ts
                # Clean the content and start a new segment.
                content = clean_line(content)
                if content:
                    current_text = [content]
                else:
                    current_text = []
            else:
                # For continuation lines: if they start with a parenthesis, skip them.
                if line.lstrip().startswith("(") or line.lstrip().startswith("（"):
                    continue
                # Otherwise, clean and append the line.
                cleaned = clean_line(line)
                if cleaned:
                    current_text.append(cleaned)
        # Append the last segment if it exists.
        if current_timestamp is not None and current_text:
            segments.append((current_timestamp, " ".join(current_text)))
    return segments

def write_flat_file(segments, output_path):
    """
    Writes the flattened segments to a file, one segment per line in the format:
    TIMESTAMP text...
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        for ts, text in segments:
            f.write(f"{ts} {text}\n")

def update_english_timestamps(cn_segments, en_segments):
    """
    Compares the Chinese and English segments (assumed to be aligned by index).
    Returns a new list of English segments updated with the Chinese timestamps
    and a log list detailing the changes.
    """
    updated_segments = []
    update_log = []
    total = min(len(cn_segments), len(en_segments))
    for idx in range(total):
        cn_ts, _ = cn_segments[idx]
        en_ts, en_text = en_segments[idx]
        if cn_ts != en_ts:
            update_log.append(f"Segment {idx+1}: English timestamp changed from {en_ts} to {cn_ts}")
            updated_segments.append((cn_ts, en_text))
        else:
            updated_segments.append((en_ts, en_text))
    # Append any extra English segments.
    for idx in range(total, len(en_segments)):
        en_ts, en_text = en_segments[idx]
        updated_segments.append((en_ts, en_text))
    return updated_segments, update_log

def main():
    parser = argparse.ArgumentParser(
        description="Process transcript files: flatten, clean (removing annotation lines), and update English timestamps to match Chinese."
    )
    parser.add_argument("chinese_file", help="Path to the Chinese transcript text file")
    parser.add_argument("english_file", help="Path to the English transcript text file")
    args = parser.parse_args()

    # Flatten and clean both transcripts.
    cn_segments = flatten_transcript(args.chinese_file)
    en_segments = flatten_transcript(args.english_file)
    
    # Define output file names based on input file names.
    base_cn = os.path.splitext(os.path.basename(args.chinese_file))[0]
    base_en = os.path.splitext(os.path.basename(args.english_file))[0]
    
    new_fix_cn_file = f"{base_cn}_newfix.txt"
    new_fix_en_file = f"{base_en}_newfix.txt"
    updated_en_file = f"{base_en}_updated.txt"
    update_log_file = f"{base_en}_update_log.txt"
    
    # Write new fixed (flattened and cleaned) files.
    write_flat_file(cn_segments, new_fix_cn_file)
    write_flat_file(en_segments, new_fix_en_file)
    
    print(f"New fixed Chinese file written to: {new_fix_cn_file}")
    print(f"New fixed English file written to: {new_fix_en_file}")
    
    # Update English timestamps based on Chinese segments.
    updated_en_segments, update_log = update_english_timestamps(cn_segments, en_segments)
    
    # Write updated English transcript.
    write_flat_file(updated_en_segments, updated_en_file)
    print(f"Updated English transcript written to: {updated_en_file}")
    
    # Write update log.
    with open(update_log_file, 'w', encoding='utf-8') as f:
        for log_entry in update_log:
            f.write(log_entry + "\n")
    print(f"Update log written to: {update_log_file}")

if __name__ == "__main__":
    main()
