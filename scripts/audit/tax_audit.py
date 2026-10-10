#!/usr/bin/env python3
"""lhg-tax 确定性税务整理审计：14 条规则，零第三方依赖。

扫描目标目录的 Markdown 清单文档，输出 JSON 与人类可读报告；
有 blocker 时以 exit code 2 退出（供 hooks 与 CI 使用），仅 warning 时 exit 1。

用法：
    python3 tax_audit.py --target <目录> [--format json|text] [--fail-on blocker|warning|nit]

规则文案均为本项目原创（方法论思路受 bd-income-tax-skills / ca-agent /
itr-prep-skill / trz 等开源项目启发，未复制任何第三方原文案与代码）。
合规红线：只做信息整理检查，绝不输出税务筹划建议；政策数字必须带来源与日期。
"""

import argparse
import json
import os
import re
import sys

VERSION = "1.0.0"
TOOL = "lhg-tax/tax-audit"

SKIP_DIRS = {".git", "__pycache__", "node_modules", "dist", "build", "vendor"}
SCAN_EXTS = {".md", ".markdown", ".txt"}

SEVEN = ["婴幼儿照护", "子女教育", "继续教育", "大病医疗",
         "住房贷款", "住房租金", "赡养老人"]
STRUCT_KEYS = ["收入", "扣除", "材料", "时间"]
DISC_KEYS = ["仅供参考", "请咨询专业人士", "不构成"]
TAX_KEYS = ["个税", "税务", "专项附加扣除", "汇算", "申报", "退税", "补税", "扣除项"]

RED_RES = [re.compile(p) for p in
           ["合理避税", "避税方案", "节税建议", "教你少缴", "更划算",
            "更省税", "筹划方案", "税务筹划", "少缴税", "怎么分摊更"]]
TODO_RES = [re.compile(p) for p in ["TODO", "FIXME", "待补充", "待完善", "XXX"]]
LEAK_RES = [re.compile(r"\d{17}[\dXx]"), re.compile(r"(?<![\d-])\d{16,19}(?![\d-])")]
POLICY_NUM_RE = re.compile(r"\d[\d,.]*\s*(元|%|％|‰|万元)")
POLICY_CTX_RE = re.compile("税|扣除|退税|补税|汇算|申报|抵扣|减免")
SRC_DATE_RE = re.compile("来源|引自|核对日期|20\\d\\d[-/年]\\d{1,2}|最新政策为准")
BARE_NUM_RE = re.compile(r"(?<![\d.])\d{4,}(?![\d.])")
UNIT_RE = re.compile(r"\d[\d,.]*\s*(元|%|％|‰|万元|个月|年|天)")
HEARSAY_RE = re.compile("据说|据报道|听说|据传")
MAT_CLASSES = [("身份", ["身份证明", "基础信息"]),
               ("收入凭证", ["收入凭证", "工资条", "银行流水"]),
               ("扣除凭证", ["扣除凭证", "佐证材料", "佐证"]),
               ("申报辅助", ["回执", "申报记录", "银行账户"])]
TIME_KEYS = ["确认", "汇算"]


class Finding:
    __slots__ = ("rule_id", "severity", "category", "title",
                 "file", "line", "snippet", "detail")

    def __init__(self, rule_id, severity, category, title,
                 file, line, snippet, detail):
        self.rule_id = rule_id
        self.severity = severity
        self.category = category
        self.title = title
        self.file = file
        self.line = line
        self.snippet = snippet
        self.detail = detail

    def to_dict(self):
        return {"rule_id": self.rule_id, "severity": self.severity,
                "category": self.category, "title": self.title,
                "file": self.file, "line": self.line,
                "snippet": self.snippet, "detail": self.detail}


def collect_files(target):
    out = []
    for root, dirs, files in os.walk(target):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in files:
            if os.path.splitext(f)[1].lower() in SCAN_EXTS:
                out.append(os.path.join(root, f))
    return sorted(out)


def read_text(path):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            return fh.read()
    except OSError:
        return ""


def is_tax_doc(text, path):
    base = os.path.basename(path).lower()
    return (any(k in text for k in TAX_KEYS)
            or any(k in base for k in ["tax", "checklist", "清单", "扣除"]))


def check_struct(text, path, findings):
    """TAX-STRUCT-001: 清单四要素章节。"""
    if not is_tax_doc(text, path):
        return
    missing = [k for k in STRUCT_KEYS if k not in text]
    if missing:
        findings.append(Finding(
            "TAX-STRUCT-001", "blocker", "结构", "清单缺要素章节",
            path, 0, "缺失: %s" % "、".join(missing),
            "税务整理清单应含收入/扣除/材料/时间节点四要素，缺失 %s" % "、".join(missing)))


def check_seven(text, path, findings):
    """TAX-CMP-001: 专项附加扣除七项全覆盖。"""
    if not is_tax_doc(text, path):
        return
    if "扣除" not in text:
        return
    for item in SEVEN:
        if item not in text:
            findings.append(Finding(
                "TAX-CMP-001", "blocker", "完整性",
                "专项附加扣除缺项: %s" % item,
                path, 0, item,
                "七项专项附加扣除须逐项过一遍，缺「%s」；不适用也要注明" % item))


def check_redline(text, path, findings):
    """TAX-RED-001: 筹划建议表述零容忍。"""
    for i, ln in enumerate(text.split("\n"), 1):
        for r in RED_RES:
            m = r.search(ln)
            if m:
                findings.append(Finding(
                    "TAX-RED-001", "blocker", "红线", "出现筹划建议表述",
                    path, i, ln.strip()[:80],
                    "命中「%s」：本插件只做信息整理，绝不给筹划建议，请删除" % m.group(0)))
                break


def check_leak(text, path, findings):
    """TAX-LEAK-001: 身份证号/银行卡号。"""
    for i, ln in enumerate(text.split("\n"), 1):
        for r in LEAK_RES:
            m = r.search(ln)
            if m:
                findings.append(Finding(
                    "TAX-LEAK-001", "blocker", "红线", "疑似敏感号码",
                    path, i, "***",
                    "发现疑似身份证号/银行卡号：隐私红线，立即删除，改为「用户自行保管」"))
                break


def check_todo(text, path, findings):
    """TAX-TODO-001: TODO 残留。"""
    for i, ln in enumerate(text.split("\n"), 1):
        for r in TODO_RES:
            if r.search(ln):
                findings.append(Finding(
                    "TAX-TODO-001", "blocker", "红线", "TODO 残留",
                    path, i, ln.strip()[:80],
                    "清单交付前不许残留 TODO/待补充，补全或删除该行"))
                break


def check_disclaimer(text, path, findings):
    """TAX-DISC-001: 免责声明。"""
    if not is_tax_doc(text, path):
        return
    if not any(k in text for k in DISC_KEYS):
        findings.append(Finding(
            "TAX-DISC-001", "blocker", "合规", "缺失合规声明",
            path, 0, "",
            "税务主题文档必须带合规声明：政策因地域与年份而异，更新快；"
            "本插件仅帮你整理扣除项清单与申报 checklist，具体请咨询专业人士。"))


def check_policy_date(text, path, findings):
    """TAX-DATE-001: 政策数字须带来源与日期。"""
    lines = text.split("\n")
    for i, ln in enumerate(lines):
        if POLICY_NUM_RE.search(ln) and POLICY_CTX_RE.search(ln):
            if "用户提供" in ln or "用户口述" in ln:
                continue  # 用户自报的收入金额不是政策引用，不要求来源标注
            window = "\n".join(lines[max(0, i - 2):i + 3])
            if not SRC_DATE_RE.search(window):
                findings.append(Finding(
                    "TAX-DATE-001", "warning", "政策", "政策数字无来源日期",
                    path, i + 1, ln.strip()[:80],
                    "引用政策数字须同时写清来源与核对日期，或写「请以当地最新政策为准」"))


def check_amount_unit(text, path, findings):
    """TAX-NUM-001: 金额须有单位。"""
    for i, ln in enumerate(text.split("\n"), 1):
        if not POLICY_CTX_RE.search(ln):
            continue
        for m in BARE_NUM_RE.finditer(ln):
            num = m.group(0)
            after = ln[m.end():m.end() + 4]
            if not UNIT_RE.match(num + after) and not re.match(r"\s*(元|%|％|‰|万元|个月|年|天)", after):
                # 排除年份（如 2026 年、2025-12-01）
                if re.match(r"\s*年", after) or "-" in ln[max(0, m.start() - 1):m.end() + 1]:
                    continue
                findings.append(Finding(
                    "TAX-NUM-001", "warning", "政策", "金额无单位",
                    path, i, ln.strip()[:80],
                    "税务语境下的数字「%s」缺少单位，请写成「数字+元」并注明口径" % num))
                break


def check_mixed_currency(text, path, findings):
    """TAX-FMT-001: ￥ 与 元混用。"""
    if "￥" in text and re.search(r"\d+\s*元", text):
        findings.append(Finding(
            "TAX-FMT-001", "warning", "格式", "货币符号混用",
            path, 0, "",
            "同一文档混用「￥」与「元」，请统一为「数字+元」"))


def check_materials(text, path, findings):
    """TAX-MAT-001: 申报材料四类。"""
    if not is_tax_doc(text, path):
        return
    if "材料" not in text and "checklist" not in path.lower():
        return
    for cls, keys in MAT_CLASSES:
        if not any(k in text for k in keys):
            findings.append(Finding(
                "TAX-MAT-001", "warning", "材料", "申报材料缺类: %s" % cls,
                path, 0, cls,
                "申报材料建议按四类组织（身份/收入凭证/扣除凭证/申报辅助），缺「%s」" % cls))


def check_timeline(text, path, findings):
    """TAX-TIME-001: 关键时间节点。"""
    if not is_tax_doc(text, path):
        return
    missing = [k for k in TIME_KEYS if k not in text]
    if missing:
        findings.append(Finding(
            "TAX-TIME-001", "warning", "时间", "缺关键时间节点",
            path, 0, "缺失: %s" % "、".join(missing),
            "时间节点提醒建议覆盖年度确认与年度汇算，缺 %s" % "、".join(missing)))


def check_hearsay(text, path, findings):
    """TAX-SRC-001: 无具名来源的传闻表述。"""
    for i, ln in enumerate(text.split("\n"), 1):
        if HEARSAY_RE.search(ln):
            findings.append(Finding(
                "TAX-SRC-001", "warning", "政策", "传闻表述无具名来源",
                path, i, ln.strip()[:80],
                "政策引用须具名来源+日期，「据说/据报道」请补来源或删除"))


def check_heading_jump(text, path, findings):
    """TAX-HYG-001: 标题层级跳跃。"""
    prev = 0
    for i, ln in enumerate(text.split("\n"), 1):
        m = re.match(r"^(#{1,6})\s", ln)
        if m:
            lvl = len(m.group(1))
            if prev and lvl > prev + 1:
                findings.append(Finding(
                    "TAX-HYG-001", "nit", "格式", "标题层级跳跃",
                    path, i, ln.strip()[:60],
                    "标题从 %d 级直接跳到 %d 级，请逐级使用" % (prev, lvl)))
            prev = lvl


def check_table_cols(text, path, findings):
    """TAX-HYG-002: 表格列数不一致。"""
    in_table = False
    expect = 0
    for i, ln in enumerate(text.split("\n"), 1):
        stripped = ln.strip()
        if stripped.startswith("|") and stripped.endswith("|"):
            cols = stripped.count("|") - 1
            if re.match(r"^\|[\s:\-|]+\|$", stripped):
                in_table = True
                continue
            if not in_table:
                in_table = True
                expect = cols
            elif cols != expect:
                findings.append(Finding(
                    "TAX-HYG-002", "nit", "格式", "表格列数不一致",
                    path, i, stripped[:60],
                    "表格该行 %d 列，与表头 %d 列不一致" % (cols, expect)))
                in_table = False
        elif in_table and stripped:
            in_table = False


RULES = [check_struct, check_seven, check_redline, check_leak, check_todo,
         check_disclaimer, check_policy_date, check_amount_unit,
         check_mixed_currency, check_materials, check_timeline,
         check_hearsay, check_heading_jump, check_table_cols]


def audit(target):
    findings = []
    files = collect_files(target)
    for path in files:
        text = read_text(path)
        rel = os.path.relpath(path, target)
        for rule in RULES:
            rule(text, rel, findings)
    sev_count = {"blocker": 0, "warning": 0, "nit": 0}
    for f in findings:
        sev_count[f.severity] = sev_count.get(f.severity, 0) + 1
    return {
        "tool": TOOL, "version": VERSION,
        "summary": {"files": len(files), "rules_run": len(RULES),
                    "blocker": sev_count["blocker"],
                    "warning": sev_count["warning"],
                    "nit": sev_count["nit"]},
        "findings": [f.to_dict() for f in findings],
    }


def fmt_text(d):
    s = d["summary"]
    out = ["[%s v%s] 扫描 %d 个文件，%d 条规则" %
           (d["tool"], d["version"], s["files"], s["rules_run"])]
    out.append("blocker=%d warning=%d nit=%d" %
               (s["blocker"], s["warning"], s["nit"]))
    for f in d["findings"]:
        loc = f["file"] + (":%d" % f["line"] if f["line"] else "")
        out.append("[%s] %s %s :: %s" %
                   (f["severity"].upper(), f["rule_id"], loc, f["title"]))
        out.append("    %s" % f["detail"])
    if not d["findings"]:
        out.append("全部通过，无发现。")
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", required=True)
    ap.add_argument("--format", default="text", choices=["json", "text"])
    ap.add_argument("--fail-on", default="blocker",
                    choices=["blocker", "warning", "nit"])
    args = ap.parse_args()
    d = audit(args.target)
    if args.format == "json":
        print(json.dumps(d, ensure_ascii=False, indent=2))
    else:
        print(fmt_text(d))
    order = {"blocker": 0, "warning": 1, "nit": 2}
    thresh = order[args.fail_on]
    worst = 3
    for f in d["findings"]:
        worst = min(worst, order.get(f["severity"], 3))
    if worst > thresh:
        return 0
    return 2 if worst == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
