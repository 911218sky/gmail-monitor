#!/bin/bash
# 提交前測試腳本

set -e

echo "🧪 執行語法檢查..."
python3 tests/test_syntax.py

echo ""
echo "✅ 所有測試通過！可以安全提交。"
