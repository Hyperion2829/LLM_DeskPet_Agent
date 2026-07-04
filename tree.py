import os

# 过滤掉不需要展示的巨型文件夹或缓存
EXCLUDE_DIRS = {'.git', 'models', 'LLaMA-Factory', '__pycache__', '.conda', 'venv', 'env'}

def print_tree(startpath):
    for root, dirs, files in os.walk(startpath):
        # 过滤目录
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        
        level = root.replace(startpath, '').count(os.sep)
        indent = ' ' * 4 * level
        print(f"{indent}{os.path.basename(root)}/")
        
        subindent = ' ' * 4 * (level + 1)
        for f in files:
            # 过滤掉 print_tree 脚本自身
            if f != "print_tree.py":
                print(f"{subindent}{f}")

if __name__ == "__main__":
    print_tree('.')