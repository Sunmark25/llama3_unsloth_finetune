## How to Use This Script

1. Save the above code to the `alpaca_converter.py` file

2. Basic usage:
   ```bash
   python alpaca_converter.py
   ```
   This will process all files in the `Ted_Talk` directory by default, generate data in both Chinese-to-English and English-to-Chinese directions, and save the results to `alpaca_data.json`

3. Advanced options:
   ```bash
   # Generate only English-to-Chinese data
   python alpaca_converter.py --direction en2cn

   # Generate only Chinese-to-English data
   python alpaca_converter.py --direction cn2en

   # Specify output filename
   python alpaca_converter.py --output my_alpaca_data.json

   # Specify directory (if TED Talk files are in another location)
   python alpaca_converter.py --dir path/to/ted/talks
   ```

## How the Script Works

1. **File pairing**: The script finds all files with `-CN.txt` and `-EN.txt` suffixes and pairs them together.

2. **Transcript parsing**: It uses regular expressions to parse the timestamp-marked text and organizes it into paragraphs.

3. **Creating Alpaca data**: For each file pair, it creates instruction-input-output triplets according to the specified translation direction (English-to-Chinese or Chinese-to-English).

4. **Saving JSON**: It saves all data as an Alpaca-formatted JSON file.