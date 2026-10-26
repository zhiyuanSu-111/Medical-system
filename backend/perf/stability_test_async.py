import argparse
import asyncio
import csv
import os
import time
from typing import Any, Dict, List, Tuple

import aiohttp

try:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
except Exception:
    plt = None

from load_test_async import _build_scenario, _request_one


async def main_async() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:5000")
    parser.add_argument("--scenario", default="read_mix", choices=["read_mix", "write_mix", "appointment_mix", "ai_mix"])
    parser.add_argument("--concurrency", type=int, default=20)
    parser.add_argument("--duration", type=int, default=120, help="Stability test duration (seconds)")
    parser.add_argument("--timeout-total", type=float, default=10.0)
    parser.add_argument("--warmup", type=int, default=2)
    parser.add_argument("--enable-ai", action="store_true")
    parser.add_argument("--ai-message", default="我需要一些健康建议：我最近总是头晕、乏力。")
    parser.add_argument("--output-dir", default=None)
    args = parser.parse_args()

    enable_ai = args.enable_ai
    specs = _build_scenario(args.scenario, enable_ai=enable_ai, ai_message=args.ai_message)

    out_dir = args.output_dir
    if not out_dir:
        stamp = time.strftime("%Y%m%d_%H%M%S", time.localtime())
        out_dir = os.path.join(os.path.dirname(__file__), "results", f"{args.scenario}_stability_{stamp}")
    os.makedirs(out_dir, exist_ok=True)

    records_path = os.path.join(out_dir, "stability_records.csv")
    summary_path = os.path.join(out_dir, "stability_summary.csv")

    timeout = aiohttp.ClientTimeout(total=None, sock_connect=5, sock_read=args.timeout_total)
    async with aiohttp.ClientSession(timeout=timeout, headers={"User-Agent": "medical-perf-test"}) as session:
        end_ts = time.perf_counter() + args.duration
        warmup_end = time.perf_counter() + args.warmup

        # 记录：time_since_start_s, latency_ms, ok
        records: List[Tuple[float, float, bool]] = []

        spec_idx = 0
        spec_lock = asyncio.Lock()

        async def worker(_: int) -> None:
            nonlocal spec_idx
            while time.perf_counter() < end_ts:
                async with spec_lock:
                    spec = specs[spec_idx % len(specs)]
                    spec_idx += 1
                latency_ms, ok = await _request_one(
                    session=session,
                    base_url=args.base_url,
                    spec=spec,
                    timeout_total_s=args.timeout_total,
                )
                now = time.perf_counter()
                if now >= warmup_end:
                    records.append((now - (end_ts - args.duration), latency_ms, ok))

        tasks = [asyncio.create_task(worker(i)) for i in range(args.concurrency)]
        await asyncio.gather(*tasks, return_exceptions=True)

    # 写 CSV
    with open(records_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["t_s", "latency_ms", "ok"])
        for r in records:
            w.writerow([f"{r[0]:.3f}", f"{r[1]:.3f}", int(r[2])])

    if records:
        lat = [r[1] for r in records]
        ok_rate = sum(1 for r in records if r[2]) / len(records)
        # 简单均值与分位用于论文简述；更细的分位建议直接用 load_test_async 的并发曲线。
        lat_mean = sum(lat) / len(lat)
        # p95
        lat_sorted = sorted(lat)
        idx = int(0.95 * (len(lat_sorted) - 1))
        lat_p95 = lat_sorted[idx]
    else:
        ok_rate = 0.0
        lat_mean = float("nan")
        lat_p95 = float("nan")

    with open(summary_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["ok_rate", "latency_ms_mean", "latency_ms_p95", "records_count"])
        w.writerow([ok_rate, lat_mean, lat_p95, len(records)])

    # 画图
    if plt is not None and records:
        xs = [r[0] for r in records]
        ys = [r[1] for r in records]
        plt.figure(figsize=(10, 4.5))
        plt.scatter(xs, ys, s=6, alpha=0.35)
        plt.title(f"Latency Over Time (c={args.concurrency}, duration={args.duration}s)")
        plt.xlabel("Time (s)")
        plt.ylabel("Latency (ms)")
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(os.path.join(out_dir, "latency_over_time.png"), dpi=160)
        plt.close()

        # 画滑动平均（简化稳定性展示）
        window = max(20, len(xs) // 30)
        avg = []
        for i in range(len(ys)):
            left = max(0, i - window)
            right = min(len(ys), i + window)
            avg.append(sum(ys[left:right]) / max(1, (right - left)))
        plt.figure(figsize=(10, 4.5))
        plt.plot(xs, avg, linewidth=2)
        plt.title("Smoothed Latency Trend")
        plt.xlabel("Time (s)")
        plt.ylabel("Latency (ms)")
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(os.path.join(out_dir, "latency_trend_smoothed.png"), dpi=160)
        plt.close()

    print(f"Done. Stability results saved to: {out_dir}")


def main() -> None:
    asyncio.run(main_async())


if __name__ == "__main__":
    main()

