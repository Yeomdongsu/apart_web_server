def read_file(file_path, encodings=['utf-8', 'cp949', 'euc-kr']):
    for enc in encodings:
        try:
            with open(file_path, "r", encoding=enc) as f:
                lines = f.readlines()
            return lines
    
        except UnicodeDecodeError:
            print(f"{enc} UnicodeDecodeError")
            continue

def parse_lines_to_dict(lines):
    result_dict = {}
    for line in lines:
        parts = line.split('|')
        key = parts[2].strip()
        value = f"{parts[1].strip()} {parts[3].strip()}"
        result_dict[key] = value
        
    return result_dict
