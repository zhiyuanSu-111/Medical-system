import argparse
import csv
import os
import random
import time
from typing import Dict, List, Tuple

try:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
except Exception:
    plt = None


def build_graph_chain_plus_random(v: int, extra_edges: int, seed: int = 42) -> Dict[int, List[int]]:
    """
    Build an undirected unweighted graph:
    - Always include a chain 0-1-2-...-v-1 to guarantee connectivity.
    - Add `extra_edges` random undirected edges.
    """
    random.seed(seed)
    adj: Dict[int, List[int]] = {i: [] for i in range(v)}
    # chain edges (weight=1)
    for i in range(v - 1):
        adj[i].append(i + 1)
        adj[i + 1].append(i)

    # random edges
    # Avoid self loops and duplicate edges roughly using a set of encoded pairs.
    seen = set()
    for i in range(v):
        for j in adj[i]:
            a, b = (i, j) if i < j else (j, i)
            seen.add((a, b))
    attempts = 0
    while extra_edges > 0 and attempts < extra_edges * 10:
        a = random.randrange(0, v)
        b = random.randrange(0, v)
        if a == b:
            attempts += 1
            continue
        x, y = (a, b) if a < b else (b, a)
        if (x, y) in seen:
            attempts += 1
            continue
        seen.add((x, y))
        adj[a].append(b)
        adj[b].append(a)
        extra_edges -= 1
    return adj


def dijkstra_like_js(v: int, edges: Dict[int, List[int]], from_id: int, to_id: int) -> List[int]:
    """
    Replica of `Navigation.vue` calculateRoute:
    - dist/prev dictionaries
    - pq implemented as array + sort on every push
    - unweighted edges => each step cost = 1
    """
    dist = {i: float("inf") for i in range(v)}
    prev = {i: None for i in range(v)}
    visited = set()
    pq: List[Tuple[int, float]] = []

    def push(node: int, d: float) -> None:
        pq.append((node, d))
        pq.sort(key=lambda x: x[1])

    dist[from_id] = 0
    push(from_id, 0)

    while pq:
        node, _ = pq.pop(0)
        if node in visited:
            continue
        visited.add(node)
        if node == to_id:
            break

        neighbors = edges.get(node, [])
        for n in neighbors:
            alt = dist[node] + 1
            if alt < dist[n]:
                dist[n] = alt
                prev[n] = node
                push(n, alt)

    if dist[to_id] == float("inf"):
        return []
    # reconstruct path
    path: List[int] = []
    u = to_id
    while u is not None:
        path.insert(0, u)
        u = prev[u]
    return path


def run_one(v: int, extra_edges: int, runs: int, seed: int) -> float:
    edges = build_graph_chain_plus_random(v, extra_edges=extra_edges, seed=seed)
    from_id, to_id = 0, v - 1
    times: List[float] = []
    for _ in range(runs):
        t0 = time.perf_counter()
        _ = dijkstra_like_js(v, edges, from_id, to_id)
        times.append(time.perf_counter() - t0)
    return sum(times) / len(times)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--v-list", default="100,200,400,800,1200", help="Graph size list")
    parser.add_argument("--extra-edges-factor", type=float, default=0.2, help="extra_edges = v * factor")
    parser.add_argument("--runs", type=int, default=5, help="Average runs per v")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output-dir", default=None)
    parser.add_argument("--profile-v", type=int, default=0, help="If >0, run cProfile on this v and save txt.")
    args = parser.parse_args()

    v_list = [int(x.strip()) for x in args.v_list.split(",") if x.strip()]

    out_dir = args.output_dir
    if not out_dir:
        stamp = time.strftime("%Y%m%d_%H%M%S", time.localtime())
        out_dir = os.path.join(os.path.dirname(__file__), "results", f"dijkstra_benchmark_{stamp}")
    os.makedirs(out_dir, exist_ok=True)

    csv_path = os.path.join(out_dir, "dijkstra_time_vs_v.csv")
    rows: List[Tuple[int, int, float]] = []

    # optional cProfile
    if args.profile_v and args.profile_v in v_list:
        import cProfile
        import pstats

        v = args.profile_v
        extra_edges = int(v * args.extra_edges_factor)
        edges = build_graph_chain_plus_random(v, extra_edges=extra_edges, seed=args.seed)
        from_id, to_id = 0, v - 1
        profiler = cProfile.Profile()
        profiler.enable()
        _ = dijkstra_like_js(v, edges, from_id, to_id)
        profiler.disable()
        profile_path = os.path.join(out_dir, "cprofile_dijkstra.txt")
        with open(profile_path, "w", encoding="utf-8") as f:
            ps = pstats.Stats(profiler, stream=f).sort_stats("cumtime")
            ps.print_stats(30)

    for v in v_list:
        extra_edges = int(v * args.extra_edges_factor)
        avg_s = run_one(v, extra_edges, runs=args.runs, seed=args.seed)
        rows.append((v, extra_edges, avg_s))
        print(f"[dijkstra] V={v} extra_edges={extra_edges} avg={avg_s*1000:.2f}ms")

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["V", "extra_edges", "avg_time_s"])
        for r in rows:
            w.writerow([r[0], r[1], f"{r[2]:.8f}"])

    if plt is not None and rows:
        xs = [r[0] for r in rows]
        ys = [r[2] * 1000.0 for r in rows]
        plt.figure(figsize=(8, 4.5))
        plt.plot(xs, ys, marker="o", linewidth=2)
        plt.title("Dijkstra-like Execution Time vs Graph Size (unweighted)")
        plt.xlabel("V (number of nodes)")
        plt.ylabel("Avg Time (ms)")
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(os.path.join(out_dir, "dijkstra_time_vs_v.png"), dpi=160)
        plt.close()

    print(f"Done. Results saved to: {out_dir}")


if __name__ == "__main__":
    main()

