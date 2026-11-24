# odyssey-plan · 奥德赛计划技能

把"我以后到底干什么"拆成三个并排的五年方案，四维打分，再用一周原型的成本去验证——而不是靠想。

这是一个 **WorkBuddy Skill**（技能包），也是一套可独立使用的方法论 + 命令行工具。核心实现只有三个文件：一份 SKILL.md、两个零依赖的 Python 脚本。

## 它解决什么

大部分职业规划的失败不是"想错了"，而是：

- 只规划了一条路 → 一旦被证伪就没有备份
- 三条路其实是同一个路换了说法 → 比较不出任何东西
- 分数是自己拍的，没有标尺 → 打完全忘了为什么这么打
- 结论停在"我要努力"→ 没有任何一个动作能在下周发生

这个技能用固定流程把这四个坑逐一堵上：三个强制互斥的版本、四维加权评分、重力问题隔离、一周内可完成的原型。

## 安装

```bash
cp -r odyssey-plan ~/.workbuddy/skills/       # 用户级，所有项目可用
# 或
cp -r odyssey-plan <项目>/.workbuddy/skills/   # 项目级，团队共享
```

装好后直接对 WorkBuddy 说「帮我做一次奥德赛计划」或「我在纠结要不要转行」即可触发。不需要手动跑脚本——脚本由技能在需要时调用。

## 单独使用（不依赖 WorkBuddy）

```bash
# 1) 复制示例，改成自己的内容
cp assets/sample-plan.json my-plan.json

# 2) 打分与排序，同时落 JSON 和 Markdown
python3 scripts/odyssey_score.py my-plan.json --json result.json --markdown score.md

# 3) 生成单文件 HTML 报告（可直接发给别人或打印）
python3 scripts/odyssey_report.py result.json -o odyssey-report.html
```

只依赖 Python 3.8+ 标准库，无第三方包，无网络请求。

`odyssey_score.py` 的输出示例：

```
| 排名 | 版本 | 方案 | 资源 | 喜爱度 | 自信度 | 一致性 | 加权总分 | 结论 |
| 1 | B | 企业培训师 | 3.0 | 4.0 | 3.0 | 4.0 | 3.55 | 值得原型 |
| 2 | C | 社区书店与读书会 | 2.0 | 5.0 | 3.0 | 4.0 | 3.45 | 先补短板 |
| 3 | A | 区域总监线 | 5.0 | 2.0 | 4.0 | 2.0 | 3.15 | 暂缓 |
```

## 方法骨架

| 环节 | 做法 |
|---|---|
| 现状 | 四仪表打分（健康/工作/娱乐/爱，0–100）＋ 重力清单 |
| 标尺 | 工作观 + 人生观，各 100–150 字，作为"一致性"的唯一依据 |
| 三版本 | A 现状延展 · B 赛道消失 · C 无所顾忌（钱和面子都不算） |
| 四维 | 资源 ×0.25 ／ 喜爱度 ×0.35 ／ 自信度 ×0.20 ／ 一致性 ×0.20 |
| 判定 | ≥4.0 推进 ｜ 3.2–4.0 做原型 ｜ 短板 ≤2 先补 ｜ <3.2 暂缓 ｜ 任一维 1 分红线 |
| 收口 | 每条路一个一周内可启动的原型（对话 / 体验 / 沉浸） |

细节见 `references/`：`method.md`（内核与七个误区）、`interview-guide.md`（提问脚本）、`scoring-rubric.md`（1–5 分锚点）、`data-schema.md`（JSON 字段）、`output-templates.md`（三种交付骨架）。

## 目录

```
odyssey-plan/
├── SKILL.md                     # 技能入口：五条硬规则 + 七步工作流
├── README.md
├── LICENSE
├── .gitignore
├── references/
│   ├── method.md                # 三版本定义、四维、重力问题、原型、失败免疫
│   ├── interview-guide.md       # 分阶段提问脚本与五种卡住的应对
│   ├── scoring-rubric.md        # 1–5 分锚点、加权、阈值、四种打分偏差
│   ├── data-schema.md           # 输入/输出 JSON 契约
│   └── output-templates.md      # Markdown / 一页纸 / PPT 骨架
├── scripts/
│   ├── odyssey_score.py         # 加权打分、排序、短板预警、结构信号
│   └── odyssey_report.py        # 单文件 HTML 报告（雷达图 + 时间轴）
├── assets/
│   ├── sample-plan.json         # 可直接改用的示例输入
│   └── odyssey-worksheet.md     # 可打印的一页纸工作表
└── examples/
    ├── sample-result.json       # 跑完的完整结果
    ├── score.md                  # 生成的评分表
    └── odyssey-report.html       # 生成的报告（浏览器直接打开看效果）
```

## 为什么评分是这样设计的

喜爱度权重最高（0.35），因为它**无法长期靠意志力伪造**。资源可以攒，自信可以练，一致性可以谈；不喜欢，撑不过三年。资源高而喜爱度低的组合会被单独标为"沉没成本陷阱"。

判定不给"哪条最好"，只给"下一步做什么"。凡是产出"三条路都不错"的规划都是失败的。

## 出处与边界

方法源自 Bill Burnett 与 Dave Evans 在斯坦福 d.school 的人生设计课及其著作 *Designing Your Life*。本仓库只实现其流程骨架与评分机制，不包含、不复制原书文本；书中的案例、练习与叙述版权归原作者与出版方。

这个工具做的是**结构化**，不做**诊断**。它不处理心理危机、不替代职业咨询、不对重大财务决策负责。如果访谈中出现明显的情绪问题，先停下打分。

## License

MIT，见 `LICENSE`。欢迎提 issue 和 PR：最有价值的贡献是**新的打分偏差案例**和**不合格原型的真实样本**。
