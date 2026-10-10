<!-- About 简介（推送后填写到仓库 About 栏）：
个人税务助手，扣除项清单与申报checklist整理（仅供参考） ｜ 一键安装：/plugin marketplace add lhg-plugs/lhg-tax
-->
<!-- topics（推送后打）：claude-code, claude-plugin, agent-skills, tax, finance -->

# lhg-tax：个人税务助手

> **一句话介绍**：个人税务信息整理助手——收入构成梳理、专项附加扣除七项清单、易漏项提醒、申报材料 checklist、时间节点提醒，一句话开整。
>
> **一键安装**：在 Claude Code 里运行
> ```
> /plugin marketplace add lhg-plugs/lhg-tax
> /plugin install lhg-tax@lhg-plugs
> ```

> **合规声明**：政策因地域与年份而异，更新快；本插件仅帮你整理扣除项清单与申报 checklist，具体请咨询专业人士。

## 它是什么

`lhg-tax` 是一个 Claude Code 插件（plugin 为主、skill 为辅）：

- **4 个命令**（小白入口）：`tax` 整理主流程（收入→扣除→易漏项→材料→时间节点），`deductions` 专项附加扣除单项梳理，`checklist` 申报材料清单，`audit` 整理成果自查
- **4 个平台中立 skill**（方法论，可移植到豆包/Workbuddy 等 agent 平台）：收入构成梳理、专项附加扣除梳理、申报材料与时间节点、自查方法论
- **2 个专家 agent**：资料收集助手、独立审计员
- **2 个提醒 hooks**：税务文档缺合规声明提醒、税务咨询合规前置（均可一键豁免，不骚扰）
- **14 条确定性自查规则**：纯 Python、零第三方依赖，重点拦截筹划建议、编造政策数字、缺失声明三类红线

## 合规定位（必读）

本插件只做**信息整理**，不做**筹划建议**：

- ✅ 帮你把收入构成、扣除项、申报材料整理成清单
- ✅ 提醒易漏项、时间节点、材料缺什么
- ❌ 不给"怎么填更划算""怎么分摊更省税"这类筹划建议
- ❌ 不编造税率与政策数字：凡引用政策数字必须写清来源与核对日期，不确定的写"请以当地最新政策为准"
- ❌ 不代办申报：最终填报与提交一律由你本人在官方渠道（个人所得税 App / 自然人电子税务局 / 办税服务厅）亲手完成
- ❌ 不收集身份证号、银行卡号等敏感信息

## 4 个命令用法

| 命令 | 作用 | 示例 |
|---|---|---|
| `/lhg-tax:tax` | 整理主流程：收入构成 → 扣除项清单 → 易漏项提醒 → 申报材料 checklist → 时间节点 | `/lhg-tax:tax 二孩、有房贷、父母均超60岁` |
| `/lhg-tax:deductions` | 专项附加扣除单项梳理（七项逐项过） | `/lhg-tax:deductions 今年多了个孩子` |
| `/lhg-tax:checklist` | 申报材料清单 + 时间节点 + 提交前五问 | `/lhg-tax:checklist` |
| `/lhg-tax:audit` | 整理成果自查（脚本 + 人工评审） | `/lhg-tax:audit` |

## 自查说明

每次交付清单前跑一遍自查：

1. 先跑 `scripts/audit/tax_audit.py`（14 条规则，零 LLM 成本）；
2. 发现分三级：**blocker**（必须修：筹划建议表述、敏感号码、缺合规声明、TODO 残留、七项缺项）、**warning**（修或写豁免理由：政策数字缺来源日期、金额格式问题）、**nit**（顺手修）；
3. 再人工过四项：口径一致性、适用性复核、时效性、隐私复核。

blocker 清零才算做完；为清零改规则算作弊，不许。

## 目录结构

```
lhg-tax/
├── .claude-plugin/          # plugin.json（插件清单）+ marketplace.json（本仓即市场）
├── commands/                # 4 个命令：tax / deductions / checklist / audit
├── skills/                  # 4 个平台中立 skill（收入/扣除/申报清单/自查）
├── agents/                  # 2 个专家 agent（collector / auditor）
├── hooks/                   # 2 个提醒（缺声明提醒 / 合规前置）+ 豁免说明
├── scripts/audit/           # 14 条确定性自查规则（零第三方依赖）
├── fixtures/                # 冒烟测试用例（坏/好对照）
├── smoke_test.py            # 一键冒烟测试
├── ATTRIBUTION.md           # 灵感来源与许可声明
└── LICENSE                  # MIT
```

## 什么时候用 / 什么时候不用（FAQ）

**什么时候用：**

- 你想在年度汇算前把收入、扣除项、申报材料一次性整理清楚时 → 用 `/lhg-tax:tax`
- 你家今年有变化（新生儿、买房、换城市、父母满 60 岁），想更新专项附加扣除时 → 用 `/lhg-tax:deductions`
- 你要开始申报了，想对一遍"材料齐不齐、时间节点别错过"时 → 用 `/lhg-tax:checklist`
- 你想检查一份整理好的清单有没有硬伤时 → 跑 `/lhg-tax:audit`

**什么时候不用：**

- 你想问"怎么填能少缴税""哪种分摊方式更划算"→ 本插件不回答这类筹划问题，请咨询专业人士
- 你希望 AI 替你在个税 App 里点提交 → 不代办，提交是你的法律行为，必须亲手完成
- 你要的是精确税额计算 → 本插件不做税额计算，只做信息整理；税额以官方渠道计算为准
- 你的情况复杂（境外所得、多处经营所得、历史欠税等）→ 直接咨询专业人士，本插件只覆盖常见整理场景

**合规问答：**

- Q：插件里的政策数字可信吗？
  A：插件默认不写具体政策数字；凡引用的数字都标注了来源与核对日期。政策更新快，务必以个税 App / 当地税务机关最新口径为准。
- Q：按插件整理的清单申报，出问题谁负责？
  A：清单仅供参考，不构成税务建议；申报责任在纳税人本人，重要事项请咨询专业人士。
- Q：我的收入数据会被上传吗？
  A：不会。本插件的整理与审计脚本都在本地运行，不上传任何数据；且插件不收集身份证号、银行卡号。

## lhg-plugs 插件矩阵

| 插件 | 一句话 | 安装 |
|---|---|---|
| [lhg-tax](https://github.com/lhg-plugs/lhg-tax) | 个人税务助手：收入构成、扣除项清单、申报 checklist 整理（仅供参考） | `/plugin install lhg-tax@lhg-plugs` |
| [lhg-fullstack](https://github.com/lhg-plugs/lhg-fullstack) | 小白一句话 → 高质量全栈应用 | `/plugin install lhg-fullstack@lhg-plugs` |
| [lhg-money-plan](https://github.com/lhg-plugs/lhg-money-plan) | 理财规划助手：收支→预算→储蓄目标（非投资建议） | `/plugin install lhg-money-plan@lhg-plugs` |
| [lhg-insurance](https://github.com/lhg-plugs/lhg-insurance) | 保险配置助手：家庭保障缺口分析→四险种配置方案→条款坑点清单 | `/plugin install lhg-insurance@lhg-plugs` |
| [lhg-fund-dca](https://github.com/lhg-plugs/lhg-fund-dca) | 基金定投助手：目标→定投计划→筛选框架→纪律执行（非投资建议） | `/plugin install lhg-fund-dca@lhg-plugs` |
| *（更多插件见 [lhg-plugs 组织](https://github.com/lhg-plugs)）* | | |

## 自检与反馈

本插件自带质检：每次使用后可跑 `python3 smoke_test.py` 一键验证（JSON 合法、skill/command/agent 完整性、14 条规则、fixtures 命中、hooks 行为）。

发现 bug 或有改进建议，以 `[QC] <一句话问题>` 为标题提交到 https://github.com/lhg-plugs/lhg-tax/issues，正文写清"复现步骤 → 实际表现 → 期望表现"。

## 出品：刘洪光

本插件由真人出镜 IP「刘洪光」（安徽合肥）出品，归属 [lhg-skills](https://github.com/lhg-skills)。

- GitHub 主页：https://github.com/lhg-skills —— 全部 skill 开源在此，欢迎 star
- 视频号：搜「刘洪光实名上网」
- 微信：lhgsmsw
