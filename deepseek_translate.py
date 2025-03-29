import re
import os
import time
import sys
from openai import OpenAI
import argparse

def parse_transcript(transcript_text):
    """Parse subtitle text with timecodes"""
    lines = transcript_text.strip().split('\n')
    parsed_lines = []
    
    for line in lines:
        # Check if the line starts with a timecode
        time_match = re.match(r'^(\d{2}:\d{2})\s+(.*)', line)
        if time_match:
            timestamp = time_match.group(1)
            content = time_match.group(2)
            parsed_lines.append((timestamp, content))
        else:
            # Handle lines without timecodes (like empty lines or special markers)
            parsed_lines.append((None, line))
    
    return parsed_lines

def translate_transcript(api_key, transcript_text, model="deepseek/deepseek-chat-v3-0324", batch_size=10, max_retries=3, retry_delay=5):
    """Use API to translate subtitles while preserving timecodes"""
    import time
    
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )
    
    parsed_lines = parse_transcript(transcript_text)
    
    # Process in batches to avoid overly long requests
    translated_transcript = []
    
    for i in range(0, len(parsed_lines), batch_size):
        batch = parsed_lines[i:i+batch_size]
        batch_num = i//batch_size + 1
        
        # Prepare text for translation
        batch_text = ""
        for timestamp, content in batch:
            if timestamp:
                batch_text += f"{timestamp} {content}\n"
            else:
                batch_text += f"{content}\n"
        
        prompt = f"""
Please translate the following English subtitles to Chinese. Strictly maintain the original format, especially the timecodes must match exactly with the original.
When translating, please note the following points:
1. All timecodes (like 00:27) must remain unchanged
2. Preserve all markers in the original text, such as (Laughter) etc.
3. Provide fluent, accurate Chinese translation
4. Do not add or remove any timecodes

Here is the text to translate:
{batch_text}

Please return the Chinese translation directly in the original format, without adding any extra explanations.
"""
        
        # Implement retry logic
        retry_count = 0
        success = False
        
        while retry_count < max_retries and not success:
            try:
                if retry_count > 0:
                    print(f"Retrying batch {batch_num} (Retry {retry_count})...")
                    # Wait before retrying to avoid rate limits
                    time.sleep(retry_delay)
                
                completion = client.chat.completions.create(
                    extra_headers={
                        "HTTP-Referer": "https://transcript-translator.app",
                        "X-Title": "Transcript Translator",
                    },
                    model=model,
                    messages=[
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    timeout=30  # Set API request timeout
                )
                
                # Add safety checks
                if (completion is None or 
                    not hasattr(completion, 'choices') or 
                    len(completion.choices) == 0 or 
                    not hasattr(completion.choices[0], 'message') or
                    not hasattr(completion.choices[0].message, 'content')):
                    raise ValueError("API returned invalid or empty format")
                
                translated_batch = completion.choices[0].message.content
                translated_transcript.append(translated_batch)
                print(f"Successfully translated batch {batch_num}")
                success = True
                
                # Brief delay to avoid triggering rate limits with rapid requests
                time.sleep(1)
                
            except Exception as e:
                retry_count += 1
                print(f"Error translating batch {batch_num} (Attempt {retry_count}/{max_retries}): {str(e)}")
                
                # If maximum retries reached, add original text to avoid content loss
                if retry_count >= max_retries:
                    print(f"Batch {batch_num} failed, using original text instead")
                    translated_transcript.append(batch_text)
    
    return "\n".join(translated_transcript)

def main():
    parser = argparse.ArgumentParser(description='Translate English subtitles to Chinese while maintaining timecode format')
    parser.add_argument('input_file', help='Input subtitle file path')
    parser.add_argument('output_file', help='Output translated subtitle file path')
    parser.add_argument('--api_key', required=True, help='OpenRouter API key')
    parser.add_argument('--model', default="deepseek/deepseek-chat-v3-0324", 
                        help='Translation model, default is deepseek/deepseek-chat-v3-0324')
    parser.add_argument('--batch_size', type=int, default=10, 
                        help='Number of lines per API request, default is 10')
    parser.add_argument('--max_retries', type=int, default=3,
                        help='Maximum retry attempts for failed API requests, default is 3')
    parser.add_argument('--retry_delay', type=int, default=5,
                        help='Wait time between retries (seconds), default is 5')
    parser.add_argument('--continue_from', type=int, default=0,
                        help='Continue translation from specified batch, used to resume interrupted translations')
    
    args = parser.parse_args()
    
    try:
        # Ensure input file exists
        if not os.path.exists(args.input_file):
            print(f"Error: Input file '{args.input_file}' does not exist")
            sys.exit(1)
            
        with open(args.input_file, 'r', encoding='utf-8') as f:
            transcript_text = f.read()
        
        # Check for existing output file (for continuation)
        existing_translation = ""
        continue_processing = False
        
        if args.continue_from > 0 and os.path.exists(args.output_file):
            with open(args.output_file, 'r', encoding='utf-8') as f:
                existing_translation = f.read()
                if existing_translation:
                    continue_processing = True
                    print(f"Detected existing translation file, will continue translation after it")
        
        # If continuing from a specific batch, truncate the input text accordingly
        if args.continue_from > 0:
            lines = transcript_text.strip().split('\n')
            start_index = args.continue_from * args.batch_size
            if start_index < len(lines):
                if continue_processing:
                    print(f"Continuing translation from batch {args.continue_from} (skipping first {start_index} lines)")
                transcript_text = '\n'.join(lines[start_index:])
            else:
                print(f"Warning: Specified batch {args.continue_from} exceeds total line count")
        
        print(f"Starting translation process, batch size: {args.batch_size}, max retries: {args.max_retries}")
        
        translated_text = translate_transcript(
            args.api_key, 
            transcript_text, 
            model=args.model,
            batch_size=args.batch_size,
            max_retries=args.max_retries,
            retry_delay=args.retry_delay
        )
        
        # If continuing, append new translation to existing one
        if continue_processing:
            translated_text = existing_translation + "\n" + translated_text
        
        with open(args.output_file, 'w', encoding='utf-8') as f:
            f.write(translated_text)
        
        print(f"Translation complete! Saved to {args.output_file}")
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()