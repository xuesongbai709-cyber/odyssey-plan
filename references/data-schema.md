# 数据契约

两个脚本共用一份 JSON。**手工填**时复制 `assets/sample-plan.json` 改名再改内容即可。

## 输入：`plan.json`

```json
{
  "name": "李维",
  "date": "2026-11-25",
  "mode": "interview",
  "dashboard": { "health": 62, "work": 55, "play": 30, "love": 70 },
  "gravity": ["38 岁转行太晚", "家里希望我留在体制内"],
  "workview": "工作是换取自主权的手段，同时得做出点别人用得上的东西。",
  "lifeview": "好生活是每天醒来不抗拒，有几段不必表演的关系。",
  "plans": [
    {
      "id": "A",
      "title": "区域总监线",
      "headline": "把现在这条销售管理路走到底，五年做到区域负责人。",
      "scores": { "resources": 5, "likeability": 2, "confidence": 4, "coherence": 2 },
      "reasons": {
        "resources": "客户和团队都在手上，公司内部路径清晰",
        "likeability": "会议和报表占了八成时间，过程无感",
        "confidence": "已经带过两个团队",
        "coherence": "和'做出别人用得上的东西'关系不大"
      },
      "timeline": [
        { "year": 1, "text": "接下一个省的盘子，补数字化工具的短板" },
        { "year": 3, "text": "带 40 人以上团队，跑通两个新区域" },
        { "year": 5, "text": "区域负责人，日程以会议和出差为主" }
      ],
      "doubts": ["第 5 年的日程我能不能忍", "离开一线之后我还会不会做判断"],
      "prototypes": [
        { "type": "对话", "action": "找两个现任区域负责人聊真实的一周", "who": "前同事张、行业群里的王", "when": "本周三前约到", "learn": "这岗位到底还剩多少一线判断" }
      ]
    }
  ]
}
```

### 字段说明

| 字段 | 必填 | 类型 | 说明 |
|---|---|---|---|
| `name` | 否 | string | 出现在报告抬头，缺省为"我" |
| `date` | 否 | string | `YYYY-MM-DD`，缺省取当天 |
| `mode` | 否 | string | `interview` / `sprint` / `workshop`，仅作标注 |
| `dashboard` | 否 | object | 四项各 0–100：`health` `work` `play` `love`；缺项按 0 处理并在报告里标注 |
| `gravity` | 否 | string[] | 重力清单，只展示不评估 |
| `workview` / `lifeview` | 否 | string | 判断一致性的唯一依据；缺失时报告会提示"未校准" |
| `plans` | **是** | array | 建议恰好 3 条；多于 4 条脚本会警告 |
| `plans[].id` | 否 | string | `A` / `B` / `C`，缺省按顺序补 |
| `plans[].title` | **是** | string | 3–6 字方案名 |
| `plans[].headline` | 否 | string | 一句话论点 |
| `plans[].scores` | **是** | object | 四维 1–5 分，整数或一位小数；超范围直接报错 |
| `plans[].reasons` | 否 | object | 四维各一句理由，强烈建议填 |
| `plans[].timeline` | 否 | array | `{year, text}`，year 为数字或字符串（如 `"3"`、`"1-2"`） |
| `plans[].doubts` | 否 | string[] | 这条路上他自己不确定的点 |
| `plans[].prototypes` | 否 | array | `{type, action, who, when, learn}`；`type` 取 `对话`/`体验`/`沉浸` |

## 输出：`result.json`

在输入原样基础上追加计算字段，供 `odyssey_report.py` 消费，也方便二次加工。

```json
{
  "meta": { "name": "李维", "date": "2026-11-25", "mode": "interview" },
  "dashboard": { ... },
  "gravity": [ ... ],
  "workview": "...",
  "lifeview": "...",
  "plans": [
    {
      "id": "A", "title": "区域总监线", "headline": "...",
      "scores": { ... },
      "total": 3.15,
      "rank": 2,
      "min_dim": "likeability",
      "verdict": { "code": "hold", "label": "暂缓", "advice": "..." },
      "flags": ["喜爱度低于 3，过程本身不成立"]
    }
  ],
  "summary": {
    "order": ["C", "B", "A"],
    "spread": 0.72,
    "common_weak": ["coherence"],
    "signals": ["C 版喜爱度最高而资源最低，结构健康：先找移植方案"],
    "next_action": "..."
  }
}
```

`verdict.code` 取值：`push`（可全力推进）、`prototype`（值得原型）、`shore-up`（先补短板）、`hold`（暂缓）、`redline`（红线）。
