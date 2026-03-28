def parse_dummy_file(file_path):
    data = {}
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                if ':' in line:
                    key, value = line.split(':', 1)
                    data[key.strip()] = value.strip()
    except FileNotFoundError:
        print(f"Error: File {file_path} not found.")
    return data
