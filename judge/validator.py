import ast
from typing import Tuple, List

FORBIDDEN_MODULES = {
    "os", "sys", "subprocess", "socket", "urllib", "requests", 
    "shutil", "pathlib", "ctypes", "multiprocessing", "threading", "builtins"
}

FORBIDDEN_BUILTINS = {"eval", "exec", "compile", "__import__", "open"}

class CodeValidator:
    """Kiểm tra mã nguồn sinh viên trước khi đưa vào Sandbox"""
    
    @staticmethod
    def validate(code_str: str) -> Tuple[bool, str]:
        try:
            tree = ast.parse(code_str)
        except SyntaxError as e:
            return False, f"Syntax Error: {e.msg} (Dòng {e.lineno})"

        for node in ast.walk(tree):
            # 1. Kiểm tra import modules cấm
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root_module = alias.name.split('.')[0]
                    if root_module in FORBIDDEN_MODULES:
                        return False, f"Bảo mật: Không được phép import thư viện '{alias.name}'"
            
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    root_module = node.module.split('.')[0]
                    if root_module in FORBIDDEN_MODULES:
                        return False, f"Bảo mật: Không được phép import từ thư viện '{node.module}'"

            # 2. Kiểm tra gọi hàm nguy hiểm
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id in FORBIDDEN_BUILTINS:
                    return False, f"Bảo mật: Không được phép sử dụng hàm '{node.func.id}()'"

        return True, "Code hợp lệ"