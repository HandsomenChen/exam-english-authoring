# 考研英语真实来源命题 · exam-english-authoring

一个用于制作考研英语一、二练习的 Codex skill：从真实英文来源选材、忠实删改，到完形、阅读A、四类新题型、两类翻译，以及试题/答案PDF的排版与核验。不含作文。

## 方法与范围

先研究真题的来源与命题方法，再选新文章。主题、结构和证据优先，热点辅助；原刊不受成品词数限制。正确项和干扰项公平比较，新题型做全局检查。答案按篇连续安排英中对照、解析和出处。

来自2010—2026两卷真题的有限研究和反馈修订，研究分母与局限见 [校准说明](references/calibration.md)。不声称已获官方认证、实测同难度或保证押中。

## 安装

下载本仓库，将整个 `exam-english-authoring` 文件夹放进 Codex 的用户技能目录（通常为 `~/.codex/skills/`），保持 `SKILL.md` 位于该文件夹根部。已有同名skill时先比较，避免覆盖自己的修改。重新打开会话后使用 `$exam-english-authoring`。

也可通过 Codex 的 skill-installer 从本GitHub仓库安装；依实际工具支持指定仓库根目录。

## 调用示例

```text
使用 $exam-english-authoring，为2027考研制作一篇英语一阅读A训练。
先从有真题题源证据的出版物找近两年的新文章，约400—450词、五题。
给独立学生PDF和按篇英中对照、答案解析与出处PDF。
已有来源无法取得时，说明具体网址及缺失范围。
```

```text
使用 $exam-english-authoring，制作英语一、二各两套训练卷，不含作文。
英二采用2024参考版式；每页页眉页脚署名“小红书：gpt学英语”。
答案按篇整合英中对照、解析和出处，并核对最终全部PDF页面及打包版本。
```

年份、卷数、署名、时效偏好和版式均可配置；默认值不代表官方标准。

## 文件结构

- `SKILL.md`：短入口和模式路由。
- `references/`：共用方法、各题型、整卷流程、版式与数据约定。
- `assets/`：工作卡、任务模板与版式参数。
- `scripts/`：无第三方依赖的计词及单元结构审计。
- `tests/`：机械检查的正常与异常用例。
- `agents/openai.yaml`：显示名称与调用提示。

## 辅助检查

Python 3.10及以上，仅使用标准库：

```bash
python3 scripts/count_words.py article.txt
python3 scripts/audit_unit.py unit.json --output audit.json
python3 -m unittest discover -s tests -v
```

底稿字段见 [数据约定](references/data-contract.md)。检查程序核对计数、回填、字符范围、编号和候选映射；语义竞争、来源真实性、译文与PDF目视检查仍须实际完成。本仓库提供方法、参数与审计工具，没有一键PDF生成引擎。

## 许可与材料

本仓库自编说明、模板与程序采用 [MIT](LICENSE)。不附第三方文章全文、真题扫描件、字体、私人会话或用量日志；第三方原文的权利与使用范围需按具体来源判断，MIT不覆盖它们。

验证范围见 [VALIDATION.md](VALIDATION.md)。
