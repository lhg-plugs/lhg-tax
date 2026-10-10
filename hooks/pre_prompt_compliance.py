#!/usr/bin/env python3
"""lhg-tax 提醒②（提示级，不拦截）：用户发起税务咨询时，先注入合规前置说明。

触发：UserPromptSubmit。prompt 含税务意图关键词时，输出一段简短 system 提醒；
      无关 prompt 零输出、不打扰。

逃生方式：LHG_TAX_HOOKS_OFF=1（环境变量）关闭本插件全部 hooks；
          或 /plugin disable lhg-tax 停用整个插件。

设计原则：只在命中时输出一句话提醒；内部出错 fail-open。零第三方依赖。
"""

import json
import os
import re
import sys

INTENT_RE = re.compile("个税|税务|专项附加扣除|年度汇算|退税|补税|报税|纳税")


def main() -> int:
    if os.environ.get("LHG_TAX_HOOKS_OFF") == "1":
        return 0
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
    except Exception:
        return 0  # fail-open

    prompt = payload.get("prompt", "") or ""
    if not INTENT_RE.search(prompt):
        return 0

    msg = ("【lhg-tax 合规前置】本次为税务主题咨询：本插件只做信息整理"
           "（收入构成、扣除项清单、申报 checklist），不提供税务筹划建议；"
           "政策因地域与年份而异、更新快，凡引用政策数字须写清来源与核对日期，"
           "不确定的写\"请以当地最新政策为准\"；最终申报由用户本人在官方渠道亲手完成。")
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "UserPromptSubmit",
        "additionalContext": msg}}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
