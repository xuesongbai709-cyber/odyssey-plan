#!/usr/bin/env python3
"""奥德赛计划打分器：四维加权、排序、短板预警、结构信号。

用法:
    python3 odyssey_score.py plan.json
    python3 odyssey_score.py plan.json --json result.json --markdown score.md

仅依赖 Python 3.8+ 标准库。
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import sys

# (字段, 中文名, 权重) —— 权重和必须为 1.0
DIMS = [
    ("resources", "资源", 0.25),
    ("likeability", "喜爱度", 0.35),
    ("confidence", "自信度", 0.20),
    ("coherence", "一致性", 0.20),
]
DIM_KEYS = [d[0] for d in DIMS]
DIM_LABEL = {d[0]: d[1] for d in DIMS}
WEIGHT = {d[0]: d[2] for d in DIMS}
DASH_KEYS = [("health", "健康"), ("work", "工作"), ("play", "娱乐"), ("love", "爱")]


class PlanError(ValueError):
    pass


# ---------------------------------------------------------------- 载入与校验


def load_plan(path):
    if path == "-":
        raw = sys.stdin.read()
        source = "<stdin>"
    else:
        with open(path, "r", encoding="utf-8") as fh:
            raw = fh.read()
        source = path
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise PlanError(f"{source} 不是合法 JSON：{exc}") from exc
    if not isinstance(data, dict):
        raise PlanError(f"{source} 顶层必须是对象")
    return data


def _as_score(plan_id, key, value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise PlanError(f"{plan_id} 的 {DIM_LABEL[key]} 分数必须是数字，当前是 {value!r}")
    if not 1 <= float(value) <= 5:
        raise PlanError(f"{plan_id} 的 {DIM_LABEL[key]} 分数应在 1–5 之间，当前是 {value}")
    return round(float(value), 1)


def validate(data):
    """校验必填项。返回警告列表，致命问题抛 PlanError。"""
    warnings = []
    plans = data.get("plans")
    if not isinstance(plans, list) or not plans:
        raise PlanError("缺少 plans 数组，或数组为空")
    if len(plans) > 4:
        warnings.append(f"检测到 {len(plans)} 条方案，多于 4 条会让人瘫痪，建议合并到 3 条")
    if len(plans) == 1:
        warnings.append("只有 1 条方案：这不是奥德赛计划，是决心书。补足 A/B/C 三条再比较")
    if len(plans) == 2:
        warnings.append("只有 2 条方案：B 版的强制解锁作用会打折，建议补齐 C 版")

    seen = set()
    for idx, plan in enumerate(plans, 1):
        if not isinstance(plan, dict):
            raise PlanError(f"第 {idx} 条方案不是对象")
        pid = str(plan.get("id") or chr(64 + idx))
        plan["id"] = pid
        if pid in seen:
            raise PlanError(f"方案 id 重复：{pid}")
        seen.add(pid)
        if not str(plan.get("title") or "").strip():
            raise PlanError(f"方案 {pid} 缺少 title（3–6 字的方案名）")
        scores = plan.get("scores")
        if not isinstance(scores, dict):
            raise PlanError(f"方案 {pid} 缺少 scores 对象")
        missing = [k for k in DIM_KEYS if k not in scores]
        if missing:
            raise PlanError(
                f"方案 {pid} 缺少维度：{', '.join(DIM_LABEL[k] for k in missing)}"
            )
        plan["scores"] = {k: _as_score(pid, k, scores[k]) for k in DIM_KEYS}
        if not plan.get("reasons"):
            warnings.append(f"方案 {pid} 没有写理由，分数会失真")

    dash = data.get("dashboard")
    if isinstance(dash, dict):
        for key, label in DASH_KEYS:
            if key not in dash:
                warnings.append(f"四仪表缺少「{label}」，按 0 处理")
    if not str(data.get("workview") or "").strip() or not str(data.get("lifeview") or "").strip():
        warnings.append("工作观/人生观未填，一致性维度的分数缺少标尺，结论只能当草图看")
    return warnings


# ---------------------------------------------------------------- 计算


def weighted_total(scores):
    total = sum(scores[k] * WEIGHT[k] for k in DIM_KEYS)
    return round(total, 2)


def verdict_of(total, min_dim):
    if min_dim <= 1:
        return {
            "code": "redline",
            "label": "红线",
            "advice": "存在 1 分维度，该方案不得进入执行，必须先解决这一维",
        }
    if total >= 4.0 and min_dim >= 3:
        return {"code": "push", "label": "可全力推进",
                "advice": "分数过线，但先做完原型再谈执行；不要跳过验证直接辞职或投钱"}
    if total >= 3.2 and min_dim >= 3:
        return {"code": "prototype", "label": "值得原型",
                "advice": "不急着决定，用一周时间做原型拿真实信息，信息回来再复评"}
    if total >= 3.2 and min_dim <= 2:
        return {"code": "shore-up", "label": "先补短板",
                "advice": "总分够但短板明显：资源低就攒钱攒时间，自信低就先找一个走过这条路的人聊"}
    return {"code": "hold", "label": "暂缓",
            "advice": "今年不作为主线，转入观察池；不必否决，但要等条件变化或信息补齐"}


def _lowest(scores):
    return min(scores, key=lambda k: scores[k])


def plan_flags(plan):
    scores = plan["scores"]
    flags = []
    low = [DIM_LABEL[k] for k in DIM_KEYS if scores[k] <= 2]
    if low:
        flags.append(f"{'、'.join(low)}低于 3 分，是这条路的结构性短板")
    if scores["likeability"] <= 2:
        flags.append("喜爱度不足：过程本身不成立，靠意志力撑不过三年")
    if scores["resources"] >= 4 and scores["likeability"] <= 2:
        flags.append("资源高而喜爱度低：典型沉没成本陷阱，资源不等于热爱")
    if scores["confidence"] <= 2 and scores["likeability"] >= 4:
        flags.append("想做但不敢：优先找原型对话，而不是先补课")
    if scores["coherence"] <= 2 and plan.get("reasons"):
        flags.append("与自述的工作观/人生观冲突，需要显式处理这个矛盾")
    if not plan.get("prototypes"):
        flags.append("没有原型：这条方案目前只是文字，未进入可验证状态")
    if not plan.get("doubts"):
        flags.append("没有写下不确定点：说明还没想细，回到时间轴继续追")
    return flags


def score_all(data):
    warnings = validate(data)
    plans = data["plans"]
    for plan in plans:
        plan["total"] = weighted_total(plan["scores"])
        plan["min_dim"] = min(plan["scores"], key=lambda k: plan["scores"][k])
        plan["min_score"] = plan["scores"][plan["min_dim"]]
        plan["verdict"] = verdict_of(plan["total"], plan["min_score"])
        if plan["verdict"]["code"] == "redline":
            worst = _lowest(plan["scores"])
            plan["verdict"]["advice"] = (
                f"「{DIM_LABEL[worst]}」只有 1 分，该方案不得进入执行，必须先解决这一维"
            )
        plan["flags"] = plan_flags(plan)

    order = sorted(plans, key=lambda p: (-p["total"], -p["scores"]["likeability"]))
    rank = {p["id"]: i for i, p in enumerate(order, 1)}
    for plan in plans:
        plan["rank"] = rank[plan["id"]]

    totals = [p["total"] for p in plans]
    spread = round(max(totals) - min(totals), 2) if totals else 0.0
    common_weak = [
        k for k in DIM_KEYS if all(p["scores"][k] <= 2 for p in plans)
    ]

    signals = []
    if len(plans) >= 2 and spread < 0.3:
        signals.append(
            f"各方案总分最大差值仅 {spread}，在他心里基本等价：真正缺的不是选择，是信息或动机"
        )
    if common_weak:
        signals.append(
            f"{'、'.join(DIM_LABEL[k] for k in common_weak)}在所有方案里都低于 3 分："
            "问题在标尺不在方案，回去重谈工作观/人生观"
        )
    by_id = {p["id"]: p for p in plans}
    c = by_id.get("C")
    if c:
        top_like = c["scores"]["likeability"] == max(p["scores"]["likeability"] for p in plans)
        low_res = c["scores"]["resources"] == min(p["scores"]["resources"] for p in plans)
        if top_like and low_res:
            signals.append(
                "C 版喜爱度最高而资源最低，结构健康：说明渴望找到了，下一步是移植而不是转行"
            )
        if c["scores"]["likeability"] <= 3:
            signals.append("C 版喜爱度不高，说明第 6 轮没挖到底，建议重做")
        if c["scores"]["resources"] >= 4:
            signals.append("C 版资源分偏高，警惕它是伪装过的 A 版")

    ranked = [p for p in order if p["verdict"]["code"] not in ("redline", "hold")]
    if not ranked:
        next_action = "没有方案进入可推进区：本周不做选择，只做一件事——约一个人聊他真实的一周"
    else:
        lead = ranked[0]
        proto = (lead.get("prototypes") or [{}])[0]
        action = proto.get("action") or "为这条方案设计一个一周内可完成的原型"
        next_action = (
            f"先给「{lead['title']}」（{lead['total']} 分）做原型：{action}"
            if lead['verdict']['code'] in ("push", "prototype")
            else f"「{lead['title']}」先补短板，同时不要放弃原型：{action}"
        )

    return {
        "meta": {
            "name": data.get("name") or "我",
            "date": data.get("date") or _dt.date.today().isoformat(),
            "mode": data.get("mode") or "interview",
        },
        "dashboard": data.get("dashboard") or {},
        "gravity": data.get("gravity") or [],
        "workview": data.get("workview") or "",
        "lifeview": data.get("lifeview") or "",
        "plans": plans,
        "summary": {
            "order": [p["id"] for p in order],
            "spread": spread,
            "common_weak": common_weak,
            "signals": signals,
            "next_action": next_action,
            "warnings": warnings,
        },
    }


# ---------------------------------------------------------------- 渲染


def _stars(v):
    full = int(round(v))
    return "●" * full + "○" * (5 - full)


def render_markdown(result):
    meta, plans, summary = result["meta"], result["plans"], result["summary"]
    out = []
    out.append(f"# 奥德赛计划 · 评分结果\n")
    out.append(f"**{meta['name']}** ｜ {meta['date']} ｜ 模式：{meta['mode']}\n")

    dash = result["dashboard"]
    if dash:
        parts = [f"{label} {int(dash.get(key, 0))}" for key, label in DASH_KEYS]
        out.append("现状四仪表：" + " ｜ ".join(parts) + "\n")

    out.append("## 评分表\n")
    head = "| 排名 | 版本 | 方案 | " + " | ".join(DIM_LABEL[k] for k in DIM_KEYS) + " | 加权总分 | 结论 |"
    columns = 3 + len(DIM_KEYS) + 2
    sep = "|" + "---|" * columns
    out.append(head)
    out.append(sep)
    for plan in sorted(plans, key=lambda p: p["rank"]):
        cells = [str(plan["rank"]), plan["id"], plan["title"]]
        cells += [str(plan["scores"][k]) for k in DIM_KEYS]
        cells += [f"**{plan['total']}**", plan["verdict"]["label"]]
        out.append("| " + " | ".join(cells) + " |")
    out.append("")

    out.append("## 逐条细看\n")
    for plan in sorted(plans, key=lambda p: p["rank"]):
        out.append(f"### {plan['id']} · {plan['title']}　{plan['total']} 分　{plan['verdict']['label']}")
        if plan.get("headline"):
            out.append(f"> {plan['headline']}")
        out.append("")
        for k in DIM_KEYS:
            line = f"- {DIM_LABEL[k]}　{_stars(plan['scores'][k])} {plan['scores'][k]}"
            reason = (plan.get("reasons") or {}).get(k)
            if reason:
                line += f"　—— {reason}"
            out.append(line)
        if plan.get("timeline"):
            out.append("")
            out.append("五年轨线：")
            for node in plan["timeline"]:
                out.append(f"- 第 {node.get('year')} 年：{node.get('text', '')}")
        if plan.get("doubts"):
            out.append("")
            out.append("还没想清：" + "；".join(plan["doubts"]))
        if plan.get("prototypes"):
            out.append("")
            out.append("原型实验：")
            for proto in plan["prototypes"]:
                bits = [proto.get("type", "原型"), proto.get("action", "")]
                meta_bits = [f"{k}：{proto[k]}" for k in ("who", "when", "learn") if proto.get(k)]
                out.append(f"- {' / '.join(b for b in bits if b)}" + (f"（{'；'.join(meta_bits)}）" if meta_bits else ""))
        if plan["flags"]:
            out.append("")
            out.append("提示：")
            for flag in plan["flags"]:
                out.append(f"- {flag}")
        out.append("")

    out.append("## 结论\n")
    out.append(f"推荐顺序：{' → '.join(summary['order'])}\n")
    for sig in summary["signals"]:
        out.append(f"- {sig}")
    if not summary["signals"]:
        out.append("- 三条路的分数与短板结构没有出现异常信号")
    out.append("")
    out.append(f"**下一步**：{summary['next_action']}\n")
    if summary["warnings"]:
        out.append("## 数据自查\n")
        for warn in summary["warnings"]:
            out.append(f"- ⚠️ {warn}")
        out.append("")
    return "\n".join(out)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="奥德赛计划四维打分器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="示例：python3 odyssey_score.py plan.json --json result.json --markdown score.md",
    )
    parser.add_argument("plan", help="plan.json 路径，用 - 表示从 stdin 读")
    parser.add_argument("--json", dest="json_out", help="结果 JSON 输出路径")
    parser.add_argument("--markdown", dest="md_out", help="Markdown 评分表输出路径")
    parser.add_argument("--quiet", action="store_true", help="不向 stdout 打印 Markdown")
    args = parser.parse_args(argv)

    try:
        data = load_plan(args.plan)
        result = score_all(data)
    except PlanError as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 2
    except FileNotFoundError:
        print(f"错误：找不到文件 {args.plan}", file=sys.stderr)
        return 2

    md = render_markdown(result)
    if args.json_out:
        os.makedirs(os.path.dirname(os.path.abspath(args.json_out)), exist_ok=True)
        with open(args.json_out, "w", encoding="utf-8") as fh:
            json.dump(result, fh, ensure_ascii=False, indent=2)
    if args.md_out:
        with open(args.md_out, "w", encoding="utf-8") as fh:
            fh.write(md)
    if not args.quiet:
        print(md)
    return 0


if __name__ == "__main__":
    sys.exit(main())
