# 单元数据约定与审计范围

这些字段供 `scripts/audit_unit.py` 使用，是结构审计接口，不是一键命题或PDF引擎。正文、选项和译解仍需按方法实际审查。脚本报告 `structural_ok` 仅表示机械检查通过。

## 所有模式的共同字段

```json
{
  "unit_id": "E1_A_R1",
  "source_id": "source-unique-id",
  "mode": "reading_a",
  "paragraphs": [{"id": "p1", "text": "卷中英文正文", "zh": "对应中文"}]
}
```

`mode`为 `cloze`、`reading_a`、`matching`、`sorting`、`headings`、`insertion`、`translation_e1` 或 `translation_e2`。`paragraphs`存正确回填/恢复顺序后的完整英文，按ID逐段配中文。中文缺失会报警告，不认证翻译质量。

规范正文固定为 `"\n\n".join(p["text"] for p in paragraphs)`，不自动裁剪空格、不改变Unicode。可选 `adapted_text` 必须与它完全一致。所有 `start`/`end` 为该字符串的Python字符位置，0起始，含start、不含end；不是UTF-8字节或JavaScript UTF-16位置。

另在底稿保留版本、来源卡、许可、段落定位、删改、证据、四项比较、译解和检查记录等字段；脚本不验证这些额外字段。source_id非空不表示来源真实性已核。

## 四选一

选项统一为 `{"A":"...","B":"...","C":"...","D":"..."}`，`correct`存字母，禁止四项文本重复。选项重排须同步所有答案和解析。

- `reading_a`：`question_start`可取21/26/31/36，`items`恰五项，分别有 `number`、`stem`、`options`、`correct`。
- `cloze`：`gaps`恰20项、顺序1—20，每项有 `number`、`start`、`end`、`answer`、`options`、`correct`。answer等于正文精确切片及正确选项文本，包含多词答案时完整保存。

完形从字符范围生成 `{{1}}` 等留空稿，报告回填词数、印出词数、各答案词数与19个相邻空之间印出词数。小于3词仅为局部检查提示，不是官方下限；即使间距较大，也须核线索及同短语双空。

## 英语一翻译

`spans`恰五项46—50，每项保存 `number`、`start`、`end`、`text`、`reference_translation`。text须与精确切片一致，五处顺序正确且不重叠。脚本报告五处词数及合计，不自动判定可译边界或难度。

## 英语二翻译

`number`为46，`reference_translation`为整篇连续中文；不设置五处 `spans`。paragraphs仍配段落中文用于对照，全文译文与段落译文是否同义须人工核对。

## Part B共同字段

`candidates`各有唯一大写字母 `label`。`answers`为五项41—45，每项有 `number`、`label`。默认不复用；只有matching可通过显式 `allow_reuse: true` 表示题干允许复用。

当前审计接口支持匹配、小标题和补句五位置七项A—G。其他合理配置需先扩展接口，不能为满足程序而改变题型。排序候选数可变，但须覆盖五个作答位置与所有给定位置。

- `matching` / `headings`：七个候选各有 `text`；`targets`恰五项41—45，每项有 `number`及 `description`（人物/对象或该节标识）。映射是否语义成立需完整5×7审查。
- `insertion`：七个候选各有 `text`；`gaps`恰五项41—45，各有 `number`、`start`、`end`。对应正确候选文本必须与该范围精确一致。报告留空、正确片段、回填、全部候选和总阅读负荷词数。两个多余候选是题目材料，不冒充原刊事实。
- `sorting`：候选各有 `label`、`paragraph_id`，覆盖每一真实段落一次。`paragraphs`仍按正确逻辑序存放；`answer_order`保存所有字母的全序。`fixed_positions`保存 `position`（1起始）与 `label`；五个answers还各有 `position`。给定与作答位置恰覆盖全序一次，且还原后与paragraphs顺序一致。七段两给定只是常见配置，非永久要求。

## 计数与限制

核心英文词元涵盖拉丁字母和重音，词内直/弯撇号保留，连字符拆分，数字另计；标题、广告、题干、选项不会自动清理，调用前须明确输入边界。`count_words.py FILE`可用于净正文或有界单元，但不得把片段计数冒充整篇原刊。

脚本不能证明选项唯一、译文自然、来源真实、原意忠实或PDF排版合格。需要改正文时，更新字符位置、答案、译文和来源删改记录后重跑；机械通过后继续实际语义与视觉核验。
