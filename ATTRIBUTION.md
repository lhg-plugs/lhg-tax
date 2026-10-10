# 灵感来源与致谢（Attribution）

本插件的**方法论灵感**来自以下优秀的开源项目与公开办事指南，
**所有实现代码、检测规则与文案均为原创**，未复制任何第三方的原文案与代码。

| 项目 | 作者 / 来源 | 许可 | 链接 | 借鉴了什么思路 |
|---|---|---|---|---|
| bd-income-tax-skills | arifulislamat | MIT | https://github.com/arifulislamat/bd-income-tax-skills | "每个税率/阈值都标注来源"（references/sources.md）与"税率验证日期"的做法；本插件 TAX-DATE-001 规则与"政策数字必须带来源与日期"的纪律受其启发 |
| ca-agent | vartika1 | 开源 | https://github.com/vartika1/ca-agent | "只整理、不代办，最终提交永远是用户的法律行为"与"数据不出本机"的隐私设计；本插件"不代办申报、不收集证件号"的红线受其启发 |
| itr-prep-skill | rajkumar-dhanasekaran | 开源 | https://github.com/rajkumar-dhanasekaran/itr-prep-skill | "收集→核对→材料包"的整理流水线与提交前核对清单思想 |
| trz | svedbg | MIT + CC BY 4.0 | https://github.com/svedbg/trz | 税率标注验证日期徽章的做法，强化了本插件"不写无日期政策数字"的纪律 |
| tax-return-assistant | drummingazz（claude-universal-skills） | 开源 | https://github.com/drummingazz/claude-universal-skills | "引用当年官方口径前先核验"的工作习惯 |
| 专项附加扣除确认办事指引 | 国家税务总局微信公众号 / 中国税务报（2025-12-01 报道） | 公开报道 | — | 专项附加扣除七项框架名称与"每年 12 月确认次年信息"的公开流程（仅借鉴框架名称，不复制原文） |
| 年度个税汇算实操攻略 | 央广网（2026-03-20 报道） | 公开报道 | https://news.cnr.cn/native/gd/kx/20260320/t20260320_527556911.shtml | 年度汇算"哪些人需要办/哪些人不用办"的公开判定框架与官方办理渠道（仅借鉴框架，不复制原文；具体数字引用时均标注来源与日期） |

## 声明

1. **借鉴思路，实现与文案均为原创**：以上项目的具体文案、规则原文、代码实现均未被复制。
   本插件的 skill 方法论文案、审计规则、命令流程均为独立撰写；政策框架名称来自公开办事指南的通用概念。
2. **许可合规**：上述开源项目均为 MIT / CC BY / 开源许可，允许在保留声明的前提下进行思路借鉴与二次创作。
   本文件即为保留声明的一部分。
3. **政策时效**：公开报道中的政策口径会随时间变化，本插件不记忆具体政策数字；
   凡引用均标注来源与核对日期，不确定的写"请以当地最新政策为准"。
4. **商标与归属**：各项目名称与作者署名归其各自所有者所有。

## 本插件自身的许可

本插件原创部分采用 MIT 许可（见 `LICENSE` 文件），版权所有：刘洪光（https://github.com/lhg-skills）。
