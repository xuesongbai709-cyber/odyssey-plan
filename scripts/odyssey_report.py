#!/usr/bin/env python3
"""把奥德赛计划结果渲染成单文件 HTML 报告（雷达图 + 仪表盘 + 时间轴，可直接分享或打印）。

用法:
    python3 odyssey_score.py plan.json --json result.json
    python3 odyssey_report.py result.json -o odyssey-report.html

参数既可以是 odyssey_score.py 产出的 result.json，也可以是原始的 plan.json
（脚本会现场补算分数）。仅依赖 Python 3.8+ 标准库。
"""

from __future__ import annotations

import argparse
import html
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import odyssey_score as core  # noqa: E402

ACCENTS = {
    "A": "#4C6E8F",
    "B": "#A6542F",
    "C": "#4A7A5C",
}
ACCENT_FALLBACK = ["#4C6E8F", "#A6542F", "#4A7A5C", "#6B5B95"]

DIM_ORDER = [("resources", "资源"), ("likeability", "喜爱度"),
             ("confidence", "自信度"), ("coherence", "一致性")]

CSS = """
:root {
  --ink: #1d1e22;
  --sub: #6a6a72;
  --line: #e3e2dd;
  --paper: #f6f5f2;
  --card: #ffffff;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  padding: 48px 24px 72px;
  background: var(--paper);
  color: var(--ink);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC",
               "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
  font-size: 15px;
  line-height: 1.75;
  -webkit-font-smoothing: antialiased;
}
.wrap { max-width: 880px; margin: 0 auto; }
header.top { border-bottom: 2px solid var(--ink); padding-bottom: 20px; margin-bottom: 40px; }
.kicker { font-size: 12px; letter-spacing: .18em; text-transform: uppercase; color: var(--sub); }
h1 { font-family: "Songti SC", Georgia, "Times New Roman", serif;
     font-size: 34px; font-weight: 600; margin: 10px 0 8px; letter-spacing: -.01em; }
.meta { font-size: 13px; color: var(--sub); }
h2 { font-family: "Songti SC", Georgia, serif; font-size: 20px; font-weight: 600;
     margin: 44px 0 16px; padding-bottom: 8px; border-bottom: 1px solid var(--line); }
h3 { font-size: 15px; font-weight: 600; margin: 0 0 4px; }
p { margin: 0 0 12px; }
.quote { background: #fff; border-left: 3px solid var(--line); padding: 14px 18px;
         color: #35363c; margin: 0 0 10px; }
.quote .lab { display: block; font-size: 11px; letter-spacing: .12em; color: var(--sub);
              text-transform: uppercase; margin-bottom: 4px; }
.dash { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; }
.dash .item { background: var(--card); border: 1px solid var(--line); border-radius: 8px; padding: 12px 14px; }
.dash .num { font-size: 24px; font-weight: 600; line-height: 1.2; }
.dash .lbl { font-size: 12px; color: var(--sub); }
.bar { height: 4px; background: #ededea; border-radius: 2px; margin-top: 8px; overflow: hidden; }
.bar > i { display: block; height: 100%; background: #8d8b84; border-radius: 2px; }
.gravity { margin: 0; padding-left: 18px; color: #44454b; }
.gravity li { margin-bottom: 4px; }
.card { background: var(--card); border: 1px solid var(--line); border-radius: 12px;
        padding: 22px 24px; margin-bottom: 18px; }
.card-head { display: flex; align-items: baseline; justify-content: space-between; gap: 12px; }
.tag { display: inline-block; font-size: 11px; font-weight: 700; letter-spacing: .06em;
       color: #fff; padding: 2px 8px; border-radius: 4px; vertical-align: 2px; margin-right: 8px; }
.total { font-family: Georgia, serif; font-size: 26px; font-weight: 600; }
.verdict { font-size: 12px; color: var(--sub); margin-left: 8px; }
.headline { color: #3c3d43; font-size: 14px; margin: 6px 0 16px; }
.split { display: grid; grid-template-columns: 240px 1fr; gap: 20px; align-items: center; }
.scores { display: flex; flex-direction: column; gap: 9px; }
.srow { display: grid; grid-template-columns: 56px 1fr 28px; gap: 10px; align-items: center; font-size: 13px; }
.srow .track { height: 6px; background: #eeedea; border-radius: 3px; overflow: hidden; }
.srow .track > i { display: block; height: 100%; border-radius: 3px; }
.srow .v { text-align: right; font-variant-numeric: tabular-nums; color: var(--sub); }
.reason { font-size: 12px; color: var(--sub); margin-top: 2px; }
.scores .reason { margin: -4px 0 2px 66px; }
.tl { list-style: none; margin: 4px 0 0; padding: 0; }
.tl li { display: grid; grid-template-columns: 46px 1fr; gap: 12px;
         padding-bottom: 12px; font-size: 13.5px; }
.tl li .y { font-size: 11px; color: var(--sub); padding-top: 3px; white-space: nowrap; }
.mini { font-size: 12px; color: var(--sub); letter-spacing: .1em; text-transform: uppercase;
        margin: 16px 0 4px; }
.proto { font-size: 13.5px; margin: 0 0 6px; padding-left: 14px; position: relative; }
.proto:before { content: ""; position: absolute; left: 0; top: 9px; width: 5px; height: 5px;
                border-radius: 50%; background: var(--ink); opacity: .35; }
.flag { font-size: 13px; color: #8a4526; margin: 0 0 4px; }
.flag:before { content: "→ "; }
.next { background: #1d1e22; color: #f4f3ef; border-radius: 12px; padding: 22px 24px; }
.next h2 { color: #fff; border-color: rgba(255,255,255,.18); margin-top: 0; }
.next .order { font-family: Georgia, serif; font-size: 22px; margin-bottom: 12px; }
.next li { color: #d9d8d3; font-size: 13.5px; }
.next .action { margin-top: 14px; font-size: 14px; color: #fff; }
.warn { font-size: 12.5px; color: var(--sub); margin-top: 10px; }
footer { margin-top: 48px; font-size: 12px; color: var(--sub); border-top: 1px solid var(--line); padding-top: 14px; }
@media (max-width: 680px) {
  body { padding: 28px 16px 48px; }
  .split { grid-template-columns: 1fr; }
  .dash { grid-template-columns: repeat(2, 1fr); }
  h1 { font-size: 26px; }
}
@media print {
  body { background: #fff; padding: 0; font-size: 11.5pt; }
  .card, .dash .item { break-inside: avoid; }
  .next { background: #fff; color: var(--ink); border: 1px solid var(--ink); }
  .next h2 { color: var(--ink); }
  .next li, .next .action { color: var(--ink); }
}
"""


def esc(value):
    return html.escape(str(value if value is not None else ""), quote=True)


def radar_svg(scores, accent):
    cx, cy, r = 118.0, 100.0, 66.0
    angles = {"resources": -90.0, "likeability": 0.0, "confidence": 90.0, "coherence": 180.0}

    def point(key, value):
        import math

        rad = math.radians(angles[key])
        dist = r * (float(value) / 5.0)
        return cx + dist * math.cos(rad), cy + dist * math.sin(rad)

    parts = [
        '<svg viewBox="0 0 240 212" width="100%" height="200" role="img" '
        'aria-label="四维雷达图">'
    ]
    for ring in range(1, 6):
        pts = " ".join(
            f"{x:.1f},{y:.1f}" for x, y in (point(k, ring) for k, _ in DIM_ORDER)
        )
        opacity = "0.55" if ring < 5 else "0.9"
        parts.append(
            f'<polygon points="{pts}" fill="none" stroke="#dcdbd5" '
            f'stroke-width="0.8" opacity="{opacity}"/>'
        )
    for key, _ in DIM_ORDER:
        x, y = point(key, 5)
        parts.append(
            f'<line x1="{cx}" y1="{cy}" x2="{x:.1f}" y2="{y:.1f}" '
            f'stroke="#dcdbd5" stroke-width="0.8"/>'
        )
    pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in (point(k, scores[k]) for k, _ in DIM_ORDER))
    parts.append(
        f'<polygon points="{pts}" fill="{accent}" fill-opacity="0.16" '
        f'stroke="{accent}" stroke-width="1.8" stroke-linejoin="round"/>'
    )
    for key, _ in DIM_ORDER:
        x, y = point(key, scores[key])
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2.6" fill="{accent}"/>')
    labels = [
        ("资源", cx, cy - r - 10, "middle"),
        ("喜爱度", cx + r + 8, cy + 4, "start"),
        ("自信度", cx, cy + r + 20, "middle"),
        ("一致性", cx - r - 8, cy + 4, "end"),
    ]
    for text, x, y, anchor in labels:
        parts.append(
            f'<text x="{x:.0f}" y="{y:.0f}" text-anchor="{anchor}" font-size="10.5" '
            f'fill="#6a6a72" font-family="-apple-system, PingFang SC, sans-serif">{text}</text>'
        )
    parts.append("</svg>")
    return "".join(parts)


def dash_block(dashboard):
    if not dashboard:
        return '<p class="meta">未填写现状四仪表。</p>'
    items = []
    for key, label in core.DASH_KEYS:
        value = dashboard.get(key, 0)
        try:
            value = int(round(float(value)))
        except (TypeError, ValueError):
            value = 0
        value = max(0, min(100, value))
        items.append(
            '<div class="item">'
            f'<div class="num">{value}</div>'
            f'<div class="lbl">{esc(label)}</div>'
            f'<div class="bar"><i style="width:{value}%"></i></div>'
            "</div>"
        )
    return '<div class="dash">' + "".join(items) + "</div>"


def scores_block(plan, accent):
    rows = []
    for key, label in DIM_ORDER:
        value = plan["scores"][key]
        pct = max(0.0, min(100.0, float(value) / 5 * 100))
        reason = (plan.get("reasons") or {}).get(key, "")
        rows.append(
            '<div class="srow">'
            f'<div>{esc(label)}</div>'
            f'<div class="track"><i style="width:{pct:.0f}%;background:{accent}"></i></div>'
            f'<div class="v">{value:g}</div>'
            "</div>"
            + (f'<div class="reason">{esc(reason)}</div>' if reason else "")
        )
    return '<div class="scores">' + "".join(rows) + "</div>"


def card_block(plan, index):
    accent = ACCENTS.get(plan["id"], ACCENT_FALLBACK[index % len(ACCENT_FALLBACK)])
    timeline = ""
    if plan.get("timeline"):
        nodes = "".join(
            f'<li><span class="y">第 {esc(node.get("year", ""))} 年</span>'
            f'<span>{esc(node.get("text", ""))}</span></li>'
            for node in plan["timeline"]
        )
        timeline = '<div class="mini">五年轨线</div><ul class="tl">' + nodes + "</ul>"

    doubts = ""
    if plan.get("doubts"):
        doubts = '<div class="mini">还没想清</div><p class="reason">' + \
                 "；".join(esc(d) for d in plan["doubts"]) + "</p>"

    protos = ""
    if plan.get("prototypes"):
        items = []
        for proto in plan["prototypes"]:
            bits = []
            if proto.get("who"):
                bits.append(f"找谁：{proto['who']}")
            if proto.get("when"):
                bits.append(f"何时：{proto['when']}")
            if proto.get("learn"):
                bits.append(f"要拿到：{proto['learn']}")
            tail = "　·　".join(esc(b) for b in bits)
            items.append(
                '<p class="proto">'
                f'<b>{esc(proto.get("type", "原型"))}</b>　{esc(proto.get("action", ""))}'
                + (f'<br><span class="reason">{tail}</span>' if tail else "")
                + "</p>"
            )
        protos = '<div class="mini">原型实验</div>' + "".join(items)

    flags = ""
    if plan.get("flags"):
        flags = '<div class="mini">提示</div>' + "".join(
            f'<p class="flag">{esc(f)}</p>' for f in plan["flags"]
        )

    headline = f'<p class="headline">{esc(plan.get("headline"))}</p>' if plan.get("headline") else ""

    return (
        '<section class="card">'
        '<div class="card-head">'
        f'<h3><span class="tag" style="background:{accent}">{esc(plan["id"])}</span>{esc(plan["title"])}</h3>'
        f'<div><span class="total">{plan["total"]}</span>'
        f'<span class="verdict">{esc(plan["verdict"]["label"])}</span></div>'
        "</div>"
        + headline
        + '<div class="split">'
        + f'<div>{radar_svg(plan["scores"], accent)}</div>'
        + scores_block(plan, accent)
        + "</div>"
        + timeline
        + doubts
        + protos
        + flags
        + "</section>"
    )


def build_html(result):
    meta = result["meta"]
    summary = result["summary"]
    plans = sorted(result["plans"], key=lambda p: p["rank"])

    gravity = ""
    if result.get("gravity"):
        gravity = (
            "<h2>重力清单（不解决，只当围墙）</h2><ul class=\"gravity\">"
            + "".join(f"<li>{esc(g)}</li>" for g in result["gravity"])
            + "</ul>"
        )

    views = ""
    if result.get("workview") or result.get("lifeview"):
        views = "<h2>判断标尺</h2>"
        if result.get("workview"):
            views += (
                '<div class="quote"><span class="lab">工作观</span>'
                + esc(result["workview"]) + "</div>"
            )
        if result.get("lifeview"):
            views += (
                '<div class="quote"><span class="lab">人生观</span>'
                + esc(result["lifeview"]) + "</div>"
            )

    warnings = ""
    if summary.get("warnings"):
        warnings = '<div class="warn">数据自查：' + esc("；".join(summary["warnings"])) + "</div>"

    signals = "".join(f"<li>{esc(s)}</li>" for s in summary["signals"]) or "<li>三条路的分数与短板结构没有出现异常信号</li>"

    order = summary["order"]
    by_id = {p["id"]: p for p in result["plans"]}
    order_text = " → ".join(
        f"{pid} {by_id[pid]['title']}" if pid in by_id else pid for pid in order
    )

    title = f"奥德赛计划 · {meta['name']}"
    return (
        "<!DOCTYPE html>\n<html lang=\"zh-CN\">\n<head>\n"
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"<title>{esc(title)}</title>\n<style>{CSS}</style>\n</head>\n<body>\n"
        '<div class="wrap">\n'
        '<header class="top">'
        '<div class="kicker">Odyssey Plan / 五年三版本对照</div>'
        f"<h1>{esc(meta['name'])} 的奥德赛计划</h1>"
        f'<div class="meta">{esc(meta["date"])}　·　模式 {esc(meta["mode"])}　·　'
        f"三个版本、四个维度、一个先做</div>"
        "</header>\n"
        "<h2>现状四仪表</h2>\n" + dash_block(result.get("dashboard")) + "\n"
        + gravity
        + views
        + "<h2>三个五年版本</h2>\n"
        + "".join(card_block(p, i) for i, p in enumerate(plans))
        + '<section class="next"><h2>结论</h2>'
        f'<div class="order">{esc(order_text)}</div>'
        f"<ul>{signals}</ul>"
        f'<div class="action"><b>下一步</b>　{esc(summary["next_action"])}</div>'
        + warnings
        + "</section>\n"
        '<footer>方法源自斯坦福人生设计课（Designing Your Life）的奥德赛计划，'
        "此处只实现其流程与评分骨架，未引用原书文本。分数由本人给出，本报告不含判断。"
        "</footer>\n</div>\n</body>\n</html>\n"
    )


def main(argv=None):
    parser = argparse.ArgumentParser(description="生成奥德赛计划 HTML 报告")
    parser.add_argument("input", help="result.json 或 plan.json 路径")
    parser.add_argument("-o", "--output", default="odyssey-report.html", help="输出 HTML 路径")
    args = parser.parse_args(argv)

    try:
        with open(args.input, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except FileNotFoundError:
        print(f"错误：找不到文件 {args.input}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as exc:
        print(f"错误：{args.input} 不是合法 JSON：{exc}", file=sys.stderr)
        return 2

    if isinstance(data.get("plans"), list) and data["plans"] and "total" not in data["plans"][0]:
        try:
            data = core.score_all(json.loads(json.dumps(data, ensure_ascii=False)))
        except core.PlanError as exc:
            print(f"错误：{exc}", file=sys.stderr)
            return 2
    if "summary" not in data:
        print("错误：输入缺少 summary 字段，请先跑 odyssey_score.py", file=sys.stderr)
        return 2

    out = build_html(data)
    out_dir = os.path.dirname(os.path.abspath(args.output))
    os.makedirs(out_dir, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as fh:
        fh.write(out)
    print(f"已生成：{os.path.abspath(args.output)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
