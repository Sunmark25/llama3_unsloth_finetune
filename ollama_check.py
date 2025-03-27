import re
import argparse
from ollama import chat  # 使用 ollama 来调用本地 LLM

"""
先運行
python3 update.py "Ted_Talk/Elon Musk_ The future we're building -- and boring _ TED - CN.txt" "Ted_Talk/Elon Musk_ The future we're building -- and boring _ TED - EN.txt"   
後運行翻譯腳本
python3 ollama_check.py "Correct_tran/Elon Musk_ The future we're building -- and boring _ TED - EN_updated.txt" "Correct_tran/Elon Musk_ The future we're building -- and boring _ TED - CN_newfix.txt"
"""
def extract_timestamp_and_content(line):
    """
    从字幕行中提取时间码和后面的文本。
    假设时间码格式为 HH:MM（如 00:13），后面跟空格及文本。
    """
    match = re.match(r"(\d\d:\d\d)\s*(.*)", line)
    if match:
        return match.group(1), match.group(2)
    else:
        return None, line

def contains_chinese(text):
    """简单判断文本中是否包含中文字符"""
    for ch in text:
        if '\u4e00' <= ch <= '\u9fff':
            return True
    return False

def check_translation(chinese_line, english_line):
    """
    使用 ollama 的 LLM 检查给定的中文和英文句子是否为对应翻译。
    采用宽松的判断标准，只有在存在严重翻译错误或完全不相关的内容时才会返回否定结果。
    """
    # 添加示例来引导模型理解宽松标准
    example = """
    示例：
    中文: 00:15 我是学政务专业的，
    英文: 00:15 I was a government major,
    判断: 是（这是对应的中英文翻译）
    """
    
    prompt = (
        "请判断下面两句话是否为对应的中英文翻译。请采用非常宽松的标准，只有在存在严重翻译错误或完全不相关的内容时才回答\"否\"。"
        "如果翻译大致传达了原文的主要意思，即使有一些差异，用词不同，或有小的遗漏或增加，也请回答\"是\"。请只回答\"是\"或\"否\"，不要解释。"
        f"{example}\n\n"
        f"中文: {chinese_line}\n英文: {english_line}\n判断: "
    )
    
    response = chat(model='qwen2.5', messages=[{'role': 'user', 'content': prompt}])
    answer = response.message.content.strip().lower()
    
    # 更宽松的判断标准：只要回答中包含"是"，就认为是有效翻译
    return "是" in answer or "yes" in answer

def compare_subtitles(file1, file2):
    """
    读取两个字幕文件，逐行比较时间码和翻译对应性。
    若时间码不匹配或翻译不对应，则记录下相应行号、时间码及原因。
    """
    with open(file1, 'r', encoding='utf-8') as f:
        lines1 = [line.strip() for line in f if line.strip()]
    with open(file2, 'r', encoding='utf-8') as f:
        lines2 = [line.strip() for line in f if line.strip()]
    
    mismatches = []
    max_lines = max(len(lines1), len(lines2))
    
    for i in range(max_lines):
        if i < len(lines1):
            ts1, content1 = extract_timestamp_and_content(lines1[i])
        else:
            ts1, content1 = None, ""
        if i < len(lines2):
            ts2, content2 = extract_timestamp_and_content(lines2[i])
        else:
            ts2, content2 = None, ""
        
        # 先比较时间码是否一致
        if ts1 != ts2:
            mismatches.append((i + 1, ts1, ts2, "时间码不匹配"))
            continue  # 时间码不一致，则不再检查翻译
        
        # 如果时间码一致，尝试判断哪一句为中文、哪一句为英文
        if contains_chinese(content1) and not contains_chinese(content2):
            chinese_text = content1
            english_text = content2
        elif contains_chinese(content2) and not contains_chinese(content1):
            chinese_text = content2
            english_text = content1
        else:
            # 如果两句均为中文或均为英文，则跳过翻译检查
            continue
        
        # 调用 ollama 检查翻译对应性
        if not check_translation(chinese_text, english_text):
            mismatches.append((i + 1, ts1, ts2, "翻译不对应"))
    
    return mismatches

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="比较两个字幕文件的时间码和翻译是否对应")
    parser.add_argument('file1', help='字幕文件1（例如英文字幕或中文字幕）')
    parser.add_argument('file2', help='字幕文件2（对应翻译的字幕）')
    args = parser.parse_args()
    
    mismatches = compare_subtitles(args.file1, args.file2)
    if mismatches:
        print("发现不对应的项：")
        for line_no, ts1, ts2, reason in mismatches:
            print(f"第 {line_no} 行: 时间码1 = {ts1}, 时间码2 = {ts2}, 原因: {reason}")
    # 如果所有行均对应则不输出任何内容
