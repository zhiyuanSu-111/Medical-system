import argparse
import json
import math
import random
from collections import defaultdict
from dataclasses import dataclass
from heapq import heappop, heappush
from pathlib import Path

import matplotlib.pyplot as plt


FLOOR_ORDER = ["1F", "2F", "3F", "4F"]


@dataclass
class CaseResult:
    scenario: str
    start_id: str
    end_id: str
    success: bool
    cost: float
    steps: int
    vertical_violation: bool
    room_ratio: float
    corridor_ratio: float
    floor_switches: int
    expected_min_switches: int
    quality_pass: bool


def load_graph(nodes_path: Path, edges_path: Path):
    nodes_arr = json.loads(nodes_path.read_text(encoding="utf-8"))
    edges_arr = json.loads(edges_path.read_text(encoding="utf-8"))
    nodes = {n["id"]: n for n in nodes_arr if n.get("id")}
    adj = defaultdict(list)
    for e in edges_arr:
        a = e.get("from")
        b = e.get("to")
        if not a or not b or a not in nodes or b not in nodes:
            continue
        w = float(e.get("weight", 1))
        kind = e.get("kind", "walk")
        adj[a].append((b, w, kind))
        adj[b].append((a, w, kind))
    return nodes, adj


def dijkstra(nodes, adj, start_id, end_id):
    if start_id not in nodes or end_id not in nodes:
        return [], math.inf
    dist = {start_id: 0.0}
    prev = {}
    pq = [(0.0, start_id)]
    seen = set()
    while pq:
        d, cur = heappop(pq)
        if cur in seen:
            continue
        seen.add(cur)
        if cur == end_id:
            break
        for to, w, _ in adj.get(cur, []):
            nd = d + max(w, 1)
            if nd < dist.get(to, math.inf):
                dist[to] = nd
                prev[to] = cur
                heappush(pq, (nd, to))
    if end_id not in dist:
        return [], math.inf
    path = [end_id]
    while path[-1] != start_id:
        path.append(prev[path[-1]])
    path.reverse()
    return path, dist[end_id]


def edge_kind(adj, a, b):
    for to, _, kind in adj.get(a, []):
        if to == b:
            return kind
    return "walk"


def is_corridor_like(node):
    t = node.get("type")
    if t in {"hub", "turn", "entrance"}:
        return True
    name = str(node.get("name", ""))
    return any(k in name for k in ["走廊", "导诊", "大厅", "入口", "收费", "通道", "连廊", "候诊", "前台"])


def calc_case_metrics(nodes, adj, path):
    if not path:
        return False, 0.0, 0.0
    per_floor_vertical = defaultdict(set)
    room_cnt = 0
    corridor_cnt = 0
    for nid in path:
        n = nodes[nid]
        if n.get("type") in {"lift", "stairs"}:
            per_floor_vertical[n.get("floor", "")].add(nid)
        if n.get("type") == "room":
            room_cnt += 1
        if is_corridor_like(n):
            corridor_cnt += 1
    vertical_violation = any(len(v) > 1 for v in per_floor_vertical.values())
    total = len(path)
    room_ratio = room_cnt / total if total else 0.0
    corridor_ratio = corridor_cnt / total if total else 0.0
    return vertical_violation, room_ratio, corridor_ratio


def floor_switch_count(nodes, path):
    if len(path) < 2:
        return 0
    cnt = 0
    for i in range(len(path) - 1):
        a = nodes.get(path[i], {})
        b = nodes.get(path[i + 1], {})
        if a.get("floor") and b.get("floor") and a.get("floor") != b.get("floor"):
            cnt += 1
    return cnt


def floor_gap(a_floor, b_floor):
    try:
        ai = FLOOR_ORDER.index(a_floor)
        bi = FLOOR_ORDER.index(b_floor)
        return abs(ai - bi)
    except ValueError:
        return 0


def pick_cases(nodes, rng: random.Random, total=80):
    candidate_nodes = [n for n in nodes.values() if n.get("type") in {"room", "hub", "entrance"}]
    by_floor = defaultdict(list)
    for n in candidate_nodes:
        by_floor[n.get("floor", "")].append(n)

    cases = []
    # 同层场景
    for floor in FLOOR_ORDER:
        pool = by_floor.get(floor, [])
        if len(pool) < 2:
            continue
        for _ in range(max(1, total // 16)):
            a, b = rng.sample(pool, 2)
            cases.append(("同层导航", a["id"], b["id"]))

    # 相邻楼层
    for i in range(len(FLOOR_ORDER) - 1):
        f1, f2 = FLOOR_ORDER[i], FLOOR_ORDER[i + 1]
        if not by_floor.get(f1) or not by_floor.get(f2):
            continue
        for _ in range(max(1, total // 12)):
            a = rng.choice(by_floor[f1])
            b = rng.choice(by_floor[f2])
            cases.append(("相邻跨层", a["id"], b["id"]))

    # 非相邻楼层
    far_pairs = [("1F", "3F"), ("1F", "4F"), ("2F", "4F")]
    for f1, f2 in far_pairs:
        if not by_floor.get(f1) or not by_floor.get(f2):
            continue
        for _ in range(max(1, total // 12)):
            a = rng.choice(by_floor[f1])
            b = rng.choice(by_floor[f2])
            cases.append(("远距跨层", a["id"], b["id"]))

    # 截断到 total
    rng.shuffle(cases)
    return cases[:total]


def run_tests(nodes, adj, cases):
    results = []
    for scenario, start_id, end_id in cases:
        path, cost = dijkstra(nodes, adj, start_id, end_id)
        if not path:
            results.append(
                CaseResult(scenario, start_id, end_id, False, math.inf, 0, False, 0.0, 0.0, 0, 0, False)
            )
            continue
        vertical_violation, room_ratio, corridor_ratio = calc_case_metrics(nodes, adj, path)
        switches = floor_switch_count(nodes, path)
        start_floor = nodes.get(start_id, {}).get("floor", "")
        end_floor = nodes.get(end_id, {}).get("floor", "")
        min_switch = floor_gap(start_floor, end_floor)
        # 质量通过：不违反单层单垂直节点、尽量走公共区域、不过多折返跨层
        quality_pass = (
            (not vertical_violation)
            and corridor_ratio >= 0.18
            and room_ratio <= 0.55
            and switches <= (min_switch + 1)
        )
        results.append(
            CaseResult(
                scenario=scenario,
                start_id=start_id,
                end_id=end_id,
                success=True,
                cost=cost,
                steps=len(path),
                vertical_violation=vertical_violation,
                room_ratio=room_ratio,
                corridor_ratio=corridor_ratio,
                floor_switches=switches,
                expected_min_switches=min_switch,
                quality_pass=quality_pass,
            )
        )
    return results


def plot_report(nodes, results, out_dir: Path):
    scenarios = ["同层导航", "相邻跨层", "远距跨层"]
    succ = {s: 0 for s in scenarios}
    total = {s: 0 for s in scenarios}
    avg_cost = {s: 0.0 for s in scenarios}
    avg_steps = {s: 0.0 for s in scenarios}
    vio = {s: 0 for s in scenarios}
    quality = {s: 0 for s in scenarios}
    room_ratio = {s: 0.0 for s in scenarios}
    corridor_ratio = {s: 0.0 for s in scenarios}

    for r in results:
        total[r.scenario] += 1
        if r.success:
            succ[r.scenario] += 1
            avg_cost[r.scenario] += r.cost
            avg_steps[r.scenario] += r.steps
            room_ratio[r.scenario] += r.room_ratio
            corridor_ratio[r.scenario] += r.corridor_ratio
            vio[r.scenario] += 1 if r.vertical_violation else 0
            quality[r.scenario] += 1 if r.quality_pass else 0

    for s in scenarios:
        if succ[s] > 0:
            avg_cost[s] /= succ[s]
            avg_steps[s] /= succ[s]
            room_ratio[s] /= succ[s]
            corridor_ratio[s] /= succ[s]

    x = list(range(len(scenarios)))
    success_rate = [(succ[s] / total[s] * 100) if total[s] else 0 for s in scenarios]
    quality_rate = [(quality[s] / succ[s] * 100) if succ[s] else 0 for s in scenarios]
    vertical_vio_rate = [(vio[s] / succ[s] * 100) if succ[s] else 0 for s in scenarios]

    plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "Arial Unicode MS", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False
    out_dir.mkdir(parents=True, exist_ok=True)
    outputs = []

    fig1, ax1 = plt.subplots(figsize=(9, 6))
    ax1.bar([i - 0.18 for i in x], success_rate, width=0.35, color="#3b82f6", label="可达成功率")
    ax1.bar([i + 0.18 for i in x], quality_rate, width=0.35, color="#f59e0b", label="路径质量通过率")
    ax1.set_title("院内导航测试图1：各场景路径规划成功率")
    ax1.set_xticks(x, scenarios)
    ax1.set_ylim(0, 105)
    ax1.set_ylabel("成功率(%)")
    ax1.legend(loc="best")
    fig1.tight_layout()
    out1 = out_dir / "navigation_test_report_1_success_rate.png"
    fig1.savefig(out1, dpi=220)
    plt.close(fig1)
    outputs.append(out1)

    fig2, ax2 = plt.subplots(figsize=(9, 6))
    ax2.bar(x, [avg_cost[s] for s in scenarios], color=["#2563eb", "#059669", "#7c3aed"])
    ax2.set_title("院内导航测试图2：各场景平均路径代价")
    ax2.set_xticks(x, scenarios)
    ax2.set_ylabel("平均代价(像素权重)")
    fig2.tight_layout()
    out2 = out_dir / "navigation_test_report_2_avg_cost.png"
    fig2.savefig(out2, dpi=220)
    plt.close(fig2)
    outputs.append(out2)

    fig3, ax3 = plt.subplots(figsize=(9, 6))
    ax3.bar(x, [avg_steps[s] for s in scenarios], color=["#60a5fa", "#34d399", "#a78bfa"])
    ax3.set_title("院内导航测试图3：各场景平均路径节点数")
    ax3.set_xticks(x, scenarios)
    ax3.set_ylabel("节点数")
    fig3.tight_layout()
    out3 = out_dir / "navigation_test_report_3_avg_steps.png"
    fig3.savefig(out3, dpi=220)
    plt.close(fig3)
    outputs.append(out3)

    fig4, ax4 = plt.subplots(figsize=(9, 6))
    ax4.plot(scenarios, [corridor_ratio[s] * 100 for s in scenarios], marker="o", label="走廊/公共节点占比")
    ax4.plot(scenarios, [room_ratio[s] * 100 for s in scenarios], marker="o", label="科室节点占比")
    ax4.plot(scenarios, vertical_vio_rate, marker="o", label="同层多垂直节点违规率")
    ax4.set_title("院内导航测试图4：路径结构指标")
    ax4.set_ylabel("占比(%)")
    ax4.set_ylim(0, 100)
    ax4.grid(alpha=0.25)
    ax4.legend(loc="best")
    fig4.tight_layout()
    out4 = out_dir / "navigation_test_report_4_structure_metrics.png"
    fig4.savefig(out4, dpi=220)
    plt.close(fig4)
    outputs.append(out4)

    return outputs


def write_csv(nodes, results, out_csv: Path):
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    header = [
        "scenario",
        "start_name",
        "start_floor",
        "end_name",
        "end_floor",
        "success",
        "cost",
        "steps",
        "vertical_violation",
        "room_ratio",
        "corridor_ratio",
        "floor_switches",
        "expected_min_switches",
        "quality_pass",
    ]
    lines = [",".join(header)]
    for r in results:
        s = nodes.get(r.start_id, {})
        e = nodes.get(r.end_id, {})
        lines.append(
            ",".join(
                [
                    r.scenario,
                    str(s.get("name", r.start_id)).replace(",", "，"),
                    str(s.get("floor", "")),
                    str(e.get("name", r.end_id)).replace(",", "，"),
                    str(e.get("floor", "")),
                    "1" if r.success else "0",
                    f"{r.cost:.2f}" if math.isfinite(r.cost) else "",
                    str(r.steps),
                    "1" if r.vertical_violation else "0",
                    f"{r.room_ratio:.4f}",
                    f"{r.corridor_ratio:.4f}",
                    str(r.floor_switches),
                    str(r.expected_min_switches),
                    "1" if r.quality_pass else "0",
                ]
            )
        )
    out_csv.write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="院内导航自动化测试并导出论文图表")
    parser.add_argument("--nodes", default="src/data/indoor/nodes.json", help="节点 JSON 路径")
    parser.add_argument("--edges", default="src/data/indoor/edges.json", help="边 JSON 路径")
    parser.add_argument("--cases", type=int, default=90, help="测试用例数量")
    parser.add_argument("--seed", type=int, default=20260421, help="随机种子")
    parser.add_argument("--out-dir", default="test-output/navigation", help="输出目录")
    args = parser.parse_args()

    root = Path(".").resolve()
    nodes_path = root / args.nodes
    edges_path = root / args.edges
    out_dir = root / args.out_dir
    out_csv = out_dir / "navigation_test_cases.csv"

    nodes, adj = load_graph(nodes_path, edges_path)
    rng = random.Random(args.seed)
    cases = pick_cases(nodes, rng, total=max(12, args.cases))
    results = run_tests(nodes, adj, cases)
    write_csv(nodes, results, out_csv)
    image_outputs = plot_report(nodes, results, out_dir)

    total_cases = len(results)
    total_success = sum(1 for r in results if r.success)
    total_quality = sum(1 for r in results if r.quality_pass)
    print(f"[OK] 测试完成: {total_cases} 条")
    print(f"[OK] 成功率: {total_success / total_cases * 100:.2f}% ({total_success}/{total_cases})")
    print(f"[OK] 路径质量通过率: {total_quality / total_success * 100:.2f}% ({total_quality}/{total_success})")
    for idx, p in enumerate(image_outputs, start=1):
        print(f"[OK] 图表输出{idx}: {p}")
    print(f"[OK] 明细输出: {out_csv}")


if __name__ == "__main__":
    main()

