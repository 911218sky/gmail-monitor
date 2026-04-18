#!/usr/bin/env python3
"""測試所有 Python 文件的語法"""

import py_compile
import sys
from pathlib import Path

def test_syntax():
    """檢查所有 Python 文件語法"""
    src_dir = Path(__file__).parent.parent / "src"
    errors = []
    
    for py_file in src_dir.glob("*.py"):
        try:
            py_compile.compile(py_file, doraise=True)
            print(f"✅ {py_file.name}")
        except py_compile.PyCompileError as e:
            errors.append(f"❌ {py_file.name}: {e}")
            print(f"❌ {py_file.name}")
            print(f"   {e}")
    
    if errors:
        print(f"\n❌ 發現 {len(errors)} 個語法錯誤")
        sys.exit(1)
    else:
        print(f"\n✅ 所有文件語法正確")
        sys.exit(0)

if __name__ == "__main__":
    test_syntax()
