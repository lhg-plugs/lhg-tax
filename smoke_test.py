#!/usr/bin/env python3
"""lhg-tax 插件冒烟测试：全部绿才算过。

检查项：
 1. 三个 JSON 合法（plugin.json / marketplace.json / hooks.json）
 2. 4 个 SKILL.md 都有 name/description frontmatter，且 >=150 行
 3. 4 个 commands 都有 description frontmatter
 4. 2 个 agents 都有 name/description/tools/model frontmatter
 5. skills 平台中立：不含 Claude Code 专有工具名；有出品区与自检节
 6. fixtures：坏 fixture 的埋点规则必须全部命中且脚本 exit!=0；
    好 fixture 零 blocker 且 exit==0
 7. hooks 脚本：税务文档缺声明提醒 / 有声明不提醒 / 非税务不提醒 /
    逃生开关 / prompt 合规前置

用法：python3 smoke_test.py [--repo <插件根目录>]
退出码：0=全绿，1=有失败。
"""

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile

PASS, FAIL = "PASS", "FAIL"
results = []


def check(name, cond, detail=""):
    results.append((PASS if cond else FAIL, name, detail))
    return cond


def read(p):
    with open(p, encoding="utf-8") as f:
        return f.read()


def frontmatter(path):
    """解析 markdown 顶部 --- YAML 块（只取一层 key: value）。"""
    text = read(path)
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end < 0:
        return {}
    fm = {}
    for ln in text[3:end].split("\n"):
        m = re.match(r"^([A-Za-z0-9_-]+)\s*:\s*(.*)$", ln)
        if m:
            fm[m.group(1)] = m.group(2).strip().strip('"').strip("'")
    return fm


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, timeout=120, **kw)


# 预期的埋点命中（坏 fixture 必须全部命中）
TAX_BAD_MUST = {
    "TAX-STRUCT-001", "TAX-CMP-001", "TAX-RED-001", "TAX-LEAK-001",
    "TAX-TODO-001", "TAX-DISC-001", "TAX-DATE-001", "TAX-NUM-001",
    "TAX-FMT-001", "TAX-MAT-001", "TAX-TIME-001", "TAX-SRC-001",
    "TAX-HYG-001", "TAX-HYG-002",
}
# 平台中立红线：skill 正文不许出现这些 Claude Code 专有表述
NEUTRAL_DENY = ["Task tool", "Bash tool", "Edit tool", "Write tool", "Read tool",
                "AskUserQuestion", "subagent_type", "PreToolUse", "PostToolUse",
                "${CLAUDE_", "CLAUDE_PLUGIN_ROOT", "CLAUDE_PROJECT_DIR"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=os.path.dirname(os.path.abspath(__file__)))
    args = ap.parse_args()
    repo = os.path.abspath(args.repo)
    AUDIT = os.path.join(repo, "scripts", "audit")

    # 1. JSON 合法
    for rel in [".claude-plugin/plugin.json", ".claude-plugin/marketplace.json",
                "hooks/hooks.json"]:
        p = os.path.join(repo, rel)
        try:
            d = json.loads(read(p))
            check("JSON 合法: " + rel, True)
            if rel.endswith("plugin.json"):
                check("plugin.json name==lhg-tax",
                      d.get("name") == "lhg-tax", str(d.get("name")))
                check("plugin.json 有 version/description/author",
                      all(d.get(k) for k in ("version", "description", "author")))
            if rel.endswith("marketplace.json"):
                ps = d.get("plugins", [])
                check("marketplace.json source==./",
                      len(ps) == 1 and ps[0].get("source") == "./" and
                      ps[0].get("name") == "lhg-tax", str(ps))
            if rel.endswith("hooks.json"):
                check("hooks.json 顶层有 hooks 包装", "hooks" in d)
                evts = d["hooks"]
                check("hooks.json 有 PostToolUse+UserPromptSubmit",
                      "PostToolUse" in evts and "UserPromptSubmit" in evts,
                      str(list(evts)))
        except Exception as e:
            check("JSON 合法: " + rel, False, str(e))

    # 2. SKILL.md frontmatter + 行数 + 中立 + 出品区
    for skill in ["lhg-tax-income", "lhg-tax-deductions",
                  "lhg-tax-checklist", "lhg-tax-audit"]:
        p = os.path.join(repo, "skills", skill, "SKILL.md")
        fm = frontmatter(p)
        check("skill frontmatter: " + skill,
              bool(fm.get("name")) and bool(fm.get("description")),
              "name=%s" % fm.get("name"))
        nlines = len(read(p).split("\n"))
        check("skill 行数>=150: %s (%d 行)" % (skill, nlines),
              nlines >= 150, str(nlines))
        body = read(p)
        bad_words = [w for w in NEUTRAL_DENY if w in body]
        check("skill 平台中立: " + skill, not bad_words, "命中: %s" % bad_words)
        check("skill 有出品区: " + skill,
              "出品：刘洪光" in body and "https://github.com/lhg-skills" in body)
        check("skill 有自检与反馈: " + skill, "自检与反馈" in body)
        check("skill 有合规声明: " + skill, "具体请咨询专业人士" in body)

    # 3. commands
    for cmd in ["tax", "deductions", "checklist", "audit"]:
        p = os.path.join(repo, "commands", cmd + ".md")
        fm = frontmatter(p)
        check("command description: " + cmd,
              bool(fm.get("description")), str(fm.get("description"))[:60])
        check("command 有合规声明: " + cmd, "具体请咨询专业人士" in read(p))

    # 4. agents
    for ag in ["collector", "auditor"]:
        p = os.path.join(repo, "agents", ag + ".md")
        fm = frontmatter(p)
        check("agent frontmatter: " + ag,
              all(fm.get(k) for k in ("name", "description", "tools", "model")),
              str({k: fm.get(k) for k in ("name", "model")}))

    # 5. 审计脚本冒烟
    def audit_hits(script, target):
        r = run([sys.executable, os.path.join(AUDIT, script),
                 "--target", os.path.join(repo, target), "--format", "json"])
        try:
            d = json.loads(r.stdout)
        except Exception:
            return None, r.returncode, []
        return d["summary"], r.returncode, [f["rule_id"] for f in d["findings"]]

    s, code, ids = audit_hits("tax_audit.py", "fixtures/tax-bad")
    check("tax 坏 fixture exit!=0", code != 0, "exit=%d" % code)
    check("tax 坏 fixture blocker>0", s and s["blocker"] > 0, str(s))
    missing = TAX_BAD_MUST - set(ids)
    check("tax 埋点全命中 (%d/%d)" % (len(TAX_BAD_MUST - missing), len(TAX_BAD_MUST)),
          not missing, "缺失: %s" % sorted(missing))

    s, code, ids = audit_hits("tax_audit.py", "fixtures/tax-good")
    check("tax 好 fixture 零 blocker", s and s["blocker"] == 0, str(s))
    check("tax 好 fixture 零 warning", s and s["warning"] == 0, str(s))
    check("tax 好 fixture exit==0", code == 0, "exit=%d" % code)

    n_rules = json.loads(run(
        [sys.executable, os.path.join(AUDIT, "tax_audit.py"),
         "--target", os.path.join(repo, "fixtures/tax-good"),
         "--format", "json"]).stdout)["summary"]["rules_run"]
    check("规则总数>=12 (%d)" % n_rules, n_rules >= 12, str(n_rules))

    # 6. hooks 脚本
    def hook(script, payload, env=None):
        e = dict(os.environ)
        e.update(env or {})
        return run([sys.executable, os.path.join(repo, "hooks", script)],
                   input=payload, env=e)

    with tempfile.TemporaryDirectory() as td:
        tax_nodisc = os.path.join(td, "清单.md")
        open(tax_nodisc, "w", encoding="utf-8").write(
            "# 申报清单\n\n补税金额超过400元的需要办理年度汇算。\n")
        tax_disc = os.path.join(td, "清单2.md")
        open(tax_disc, "w", encoding="utf-8").write(
            "# 申报清单\n\n补税相关内容，仅供参考，具体请咨询专业人士。\n")
        nontax = os.path.join(td, "notes.md")
        open(nontax, "w", encoding="utf-8").write("# 读书笔记\n\n今天读了三章。\n")

        r = hook("post_write_disclaimer.py",
                 json.dumps({"tool_input": {"file_path": tax_nodisc}}))
        check("hook: 税务文档缺声明提醒",
              r.returncode == 0 and "additionalContext" in r.stdout, r.stdout[:80])
        r = hook("post_write_disclaimer.py",
                 json.dumps({"tool_input": {"file_path": tax_disc}}))
        check("hook: 有声明不提醒", not r.stdout.strip(), r.stdout[:80])
        r = hook("post_write_disclaimer.py",
                 json.dumps({"tool_input": {"file_path": nontax}}))
        check("hook: 非税务文档不提醒", not r.stdout.strip(), r.stdout[:80])
        r = hook("post_write_disclaimer.py",
                 json.dumps({"tool_input": {"file_path": tax_nodisc}}),
                 {"LHG_TAX_HOOKS_OFF": "1"})
        check("hook: 逃生开关生效", r.returncode == 0 and not r.stdout.strip())

    r = hook("pre_prompt_compliance.py",
             json.dumps({"prompt": "帮我看看今年的个税汇算"}))
    check("hook: 税务 prompt 合规前置",
          r.returncode == 0 and "additionalContext" in r.stdout, r.stdout[:80])
    r = hook("pre_prompt_compliance.py",
             json.dumps({"prompt": "帮我写个周报"}))
    check("hook: 非税务 prompt 不打扰", not r.stdout.strip(), r.stdout[:80])
    r = hook("pre_prompt_compliance.py",
             json.dumps({"prompt": "个税怎么报"}),
             {"LHG_TAX_HOOKS_OFF": "1"})
    check("hook: prompt 逃生开关生效",
          r.returncode == 0 and not r.stdout.strip())

    # 报告
    print("=" * 60)
    print("lhg-tax 冒烟测试报告")
    print("=" * 60)
    fails = 0
    for st, name, detail in results:
        mark = "✓" if st == PASS else "✗"
        print("%s %s %s" % (mark, st, name))
        if detail and st == FAIL:
            print("    → %s" % detail)
        if st == FAIL:
            fails += 1
    print("=" * 60)
    print("共 %d 项，通过 %d，失败 %d" % (len(results), len(results) - fails, fails))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
