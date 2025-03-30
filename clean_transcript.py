import os
import sys

def process_file(input_file, output_file, words_to_remove):
    """
    处理文本文件，删除包含指定文字的行，并合并没有时间码的行到上一行
    
    参数:
    input_file (str): 输入文件路径
    output_file (str): 输出文件路径
    words_to_remove (list): 需要删除的包含这些词的行
    """
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        processed_lines = []
        
        for i, line in enumerate(lines):
            # 如果当前行包含需要删除的词，跳过
            if any(word in line for word in words_to_remove):
                continue
            
            # 检查是否有时间码 (格式为 XX:XX)
            has_timestamp = len(line) >= 5 and line[2:3] == ':' and line[0:2].isdigit() and line[3:5].isdigit()
            
            if not has_timestamp and i > 0 and processed_lines:
                # 没有时间码，合并到上一行（将换行符变为空格）
                processed_lines[-1] = processed_lines[-1].rstrip() + ' ' + line.strip() + '\n'
            elif has_timestamp:
                # 有时间码，添加为新行
                processed_lines.append(line)
        
        # 写入处理后的内容到输出文件
        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(processed_lines)
        
        return True
    except Exception as e:
        print(f"处理文件 {input_file} 时出错: {e}")
        return False

def process_folder(folder_path, output_folder, words_to_remove):
    """
    处理文件夹中所有的txt文件
    
    参数:
    folder_path (str): 输入文件夹路径
    output_folder (str): 输出文件夹路径
    words_to_remove (list): 需要删除的包含这些词的行
    """
    # 确保输出文件夹存在
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    # 获取所有txt文件
    txt_files = [f for f in os.listdir(folder_path) if f.endswith('.txt')]
    
    if not txt_files:
        print(f"在 {folder_path} 中没有找到txt文件")
        return
    
    success_count = 0
    
    for txt_file in txt_files:
        input_file_path = os.path.join(folder_path, txt_file)
        output_file_path = os.path.join(output_folder, txt_file)
        
        print(f"正在处理: {txt_file}")
        success = process_file(input_file_path, output_file_path, words_to_remove)
        
        if success:
            success_count += 1
    
    print(f"处理完成！共处理了 {success_count}/{len(txt_files)} 个文件")
    print(f"结果已保存到 {output_folder} 文件夹")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("用法: python script.py 输入文件夹 输出文件夹 [要删除的词1] [要删除的词2] ...")
        sys.exit(1)
    
    input_folder = sys.argv[1]
    output_folder = sys.argv[2]
    words_to_remove = sys.argv[3:] if len(sys.argv) > 3 else ["笑声", "掌声"]
    
    if not os.path.exists(input_folder):
        print(f"输入文件夹 {input_folder} 不存在")
        sys.exit(1)
    
    process_folder(input_folder, output_folder, words_to_remove)