#!/usr/bin/env python3
"""lhg-tax 提醒①（警告级，不拦截）：写入税务主题文档却缺免责声明时提醒补上。

触发：PostToolUse / Write|Edit。只做提醒，永远 exit 0、不拦截写入。
判定：文件为 .md 且内容含税务关键词（税/个税/扣除/汇算/申报），
      但不含免责声明关键词（仅供参考/请咨询专业人士/不构成）时，输出 additionalContext。

逃生方式（按推荐度排序）：
  1. 在文档末尾补上合规声明（推荐）。
  2. LHG_TAX_HOOKS_OFF=1（环境变量）关闭本插件全部 hooks。
  3. /plugin disable lhg-tax 停用整个插件。

设计原则：脚本内部出错时 fail-open，直接放行不骚扰用户。零第三方依赖。
"""

import json
import os
import re
import sys

TAX_RES = [re.compile(p) for p in
           ["个税", "税务", "专项附加扣除", "汇算", "申报", "退税", "补税", "扣除项"]]
DISC_RES = [re.compile(p) for p in
            ["仅供参考", "请咨询专业人士", "不构成"]]


def main() -> int:
    if os.environ.get("LHG_TAX_HOOKS_OFF") == "1":
        return 0
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
    except Exception:
        return 0  # fail-open

    tool_input = payload.get("tool_input", {}) or {}
    path = tool_input.get("file_path", "") or ""
    if not path.endswith(".md"):
        return 0
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            text = fh.read()
    except OSError:
        return 0

    if not any(r.search(text) for r in TAX_RES):
        return 0
    if any(r.search(text) for r in DISC_RES):
        return 0

    msg = ("【lhg-tax 提醒】这份文档涉及税务内容，但未检测到合规声明。"
           "建议在末尾补上：\"政策因地域与年份而异，更新快；"
           "本插件仅帮你整理扣除项清单与申报 checklist，具体请咨询专业人士。\""
           "（关闭提醒：LHG_TAX_HOOKS_OFF=1）")
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PostToolUse",
        "additionalContext": msg}}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
