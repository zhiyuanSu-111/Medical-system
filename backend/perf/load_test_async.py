import argparse
import asyncio
import csv
import os
import random
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import aiohttp


try:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
except Exception:
    plt = None


def _percentile(sorted_values: List[float], p: float) -> float:
    """p in [0, 100]."""
    if not sorted_values:
        return float("nan")
    k = (len(sorted_values) - 1) * (p / 100.0)
    f = int(k)
    c = min(f + 1, len(sorted_values) - 1)
    if f == c:
        return sorted_values[f]
    return sorted_values[f] + (sorted_values[c] - sorted_values[f]) * (k - f)


@dataclass
class RequestSpec:
    name: str
    method: str
    path: str
    json_body: Optional[Dict[str, Any]] = None
    params: Optional[Dict[str, Any]] = None
    # If set, will be called for each request to generate json_body/params.
    factory: Optional[Any] = None


def _today_date() -> str:
    # 后端示例数据初始化未来7天号源，通常从“明天”开始存在
    return time.strftime("%Y-%m-%d", time.localtime(time.time() + 24 * 3600))


def _make_departments_spec() -> RequestSpec:
    return RequestSpec(name="departments", method="GET", path="/api/departments")


def _make_doctors_spec() -> RequestSpec:
    # 这里随机取几个 department_id，模拟真实用户在不同科室切换
    def factory() -> Dict[str, Any]:
        return {"department_id": str(random.choice([1, 2, 3, 4, 5, 27]))}

    return RequestSpec(
        name="doctors",
        method="GET",
        path="/api/doctors",
        factory=factory,
    )


def _make_slots_spec() -> RequestSpec:
    def factory() -> Dict[str, Any]:
        # 使用 database.py 初始化的示例 doctors（避免 appointment-slots 返回空）
        return {
            "doctor_id": str(random.choice([100101, 100201, 101301])),
            "date": _today_date(),
        }

    return RequestSpec(
        name="appointment_slots",
        method="GET",
        path="/api/appointment-slots",
        factory=factory,
    )


def _make_patient_create_spec() -> RequestSpec:
    def factory() -> Dict[str, Any]:
        rid = random.randint(10_000_000, 99_999_999)
        id_card = f"TEST{id(rid)}{rid}"[-18:]
        return {
            "name": f"压测用户{rid}",
            "phone": f"1{rid:0>10}"[-11:],
            "idCard": id_card,
        }

    return RequestSpec(
        name="patient_create",
        method="POST",
        path="/api/patients",
        factory=factory,
    )


def _make_ai_consultation_spec(message: str) -> RequestSpec:
    # 文本问诊：content-type 为 application/json
    return RequestSpec(
        name="ai_consultation",
        method="POST",
        path="/api/ai-consultation",
        json_body={"message": message},
    )


def _build_scenario(scenario: str, enable_ai: bool, ai_message: str) -> List[RequestSpec]:
    if scenario == "read_mix":
        return [
            _make_departments_spec(),
            _make_doctors_spec(),
            _make_slots_spec(),
        ]
    if scenario == "write_mix":
        return [
            _make_departments_spec(),
            _make_patient_create_spec(),
        ]
    if scenario == "appointment_mix":
        # 预约会修改数据库并扣减号源；建议并发不要太高，时长也不要过长
        def appointment_factory() -> Dict[str, Any]:
            rid = random.randint(10_000_000, 99_999_999)
            id_card = f"TEST{id(rid)}{rid}"[-18:]
            patient = {
                "patientName": f"压测患者{rid}",
                "patientPhone": f"1{rid:0>10}"[-11:],
                "patientIdCard": id_card,
            }
            # doctor 与 title 要匹配 app.py appointment 中的默认逻辑/提示词
            doc = random.choice(
                [
                    {
                        "doctorId": 100101,
                        "doctor": "周景明",
                        "doctorTitle": "主任医师",
                        "departmentId": 1,
                        "subDepartmentId": 1,
                        "specialtyId": None,
                        "specialty": "消化内科",
                    },
                    {
                        "doctorId": 100201,
                        "doctor": "马思远",
                        "doctorTitle": "副主任医师",
                        "departmentId": 2,
                        "subDepartmentId": 1,
                        "specialtyId": None,
                        "specialty": "肝胆胰外科",
                    },
                    {
                        "doctorId": 101301,
                        "doctor": "苏晚柠",
                        "doctorTitle": "主任医师",
                        "departmentId": 13,
                        "subDepartmentId": 1,
                        "specialtyId": 13001,
                        "specialty": "皮肤科门诊",
                    },
                ]
            )
            time_slot = random.choice(["08:00-12:00", "14:00-18:00"])
            return {
                "doctor": doc["doctor"],
                "doctorId": doc["doctorId"],
                "doctorTitle": doc["doctorTitle"],
                "date": _today_date(),
                "timeSlot": time_slot,
                "departmentId": doc["departmentId"],
                "subDepartmentId": doc["subDepartmentId"],
                "specialtyId": doc["specialtyId"],
                **patient,
                "specialty": doc["specialty"],
                "department": "",
                "subDepartment": "",
            }

        return [
            RequestSpec(
                name="appointment",
                method="POST",
                path="/api/appointment",
                factory=appointment_factory,
            )
        ]
    if scenario == "ai_mix":
        if not enable_ai:
            raise RuntimeError("ai_mix requires enable_ai=true (or set --enable-ai).")
        return [
            _make_ai_consultation_spec(ai_message),
        ]
    raise ValueError(f"Unknown scenario: {scenario}")


async def _request_one(
    session: aiohttp.ClientSession,
    base_url: str,
    spec: RequestSpec,
    timeout_total_s: float,
) -> Tuple[float, bool]:
    """
    Returns: (latency_ms, ok)
    """
    url = base_url.rstrip("/") + spec.path

    payload_json = spec.json_body
    payload_params = spec.params
    if spec.factory is not None:
        generated = spec.factory()
        # GET: factory returns params, POST: factory returns json
        if spec.method.upper() == "GET":
            payload_params = generated
        else:
            payload_json = generated

    start = time.perf_counter()
    try:
        if spec.method.upper() == "GET":
            async with session.get(url, params=payload_params, timeout=timeout_total_s) as resp:
                await resp.read()
                ok = 200 <= resp.status < 300
        else:
            async with session.post(url, json=payload_json, params=payload_params, timeout=timeout_total_s) as resp:
                await resp.read()
                ok = 200 <= resp.status < 300
        latency_ms = (time.perf_counter() - start) * 1000.0
        return latency_ms, ok
    except Exception:
        latency_ms = (time.perf_counter() - start) * 1000.0
        return latency_ms, False


async def run_concurrency_level(
    *,
    session: aiohttp.ClientSession,
    base_url: str,
    specs: List[RequestSpec],
    concurrency: int,
    duration_s: int,
    timeout_total_s: float,
    warmup_s: int = 0,
) -> Dict[str, Any]:
    """
    Use N async workers, each worker loops until duration end.
    """
    end_ts = time.perf_counter() + duration_s
    warmup_end = time.perf_counter() + warmup_s

    latencies: List[float] = []
    ok_count = 0
    total_count = 0
    err_count = 0

    # Round-robin across specs to keep mix stable.
    # For thesis, "稳定性"主要体现在曲线形状而不是严格的随机比例。
    spec_idx = 0
    spec_lock = asyncio.Lock()

    async def worker(worker_id: int) -> None:
        nonlocal ok_count, total_count, err_count, spec_idx
        while time.perf_counter() < end_ts:
            async with spec_lock:
                spec = specs[spec_idx % len(specs)]
                spec_idx += 1

            latency_ms, ok = await _request_one(
                session=session,
                base_url=base_url,
                spec=spec,
                timeout_total_s=timeout_total_s,
            )
            total_count += 1
            if ok:
                ok_count += 1
                if time.perf_counter() >= warmup_end:
                    latencies.append(latency_ms)
            else:
                err_count += 1
                if time.perf_counter() >= warmup_end:
                    latencies.append(latency_ms)

    tasks = [asyncio.create_task(worker(i)) for i in range(concurrency)]
    await asyncio.gather(*tasks, return_exceptions=True)

    lat_sorted = sorted(latencies)
    p50 = _percentile(lat_sorted, 50)
    p90 = _percentile(lat_sorted, 90)
    p95 = _percentile(lat_sorted, 95)
    p99 = _percentile(lat_sorted, 99)

    qps = ok_count / max(duration_s, 1e-6)

    return {
        "concurrency": concurrency,
        "duration_s": duration_s,
        "total_requests": total_count,
        "ok_requests": ok_count,
        "error_requests": err_count,
        "error_rate": (err_count / total_count) if total_count else 0.0,
        "qps": qps,
        "latency_ms_mean": (sum(lat_sorted) / len(lat_sorted)) if lat_sorted else float("nan"),
        "latency_ms_p50": p50,
        "latency_ms_p90": p90,
        "latency_ms_p95": p95,
        "latency_ms_p99": p99,
    }


def _plot_concurrency(summary_csv_path: str, out_dir: str) -> None:
    if plt is None:
        return
    # 不依赖 pandas：直接用 csv 读
    rows: List[Dict[str, str]] = []
    with open(summary_csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)
    if not rows:
        return

    xs = [int(r["concurrency"]) for r in rows]
    qps = [float(r["qps"]) for r in rows]
    p50 = [float(r["latency_ms_p50"]) for r in rows]
    p95 = [float(r["latency_ms_p95"]) for r in rows]
    err_rate = [float(r["error_rate"]) for r in rows]

    os.makedirs(out_dir, exist_ok=True)

    plt.figure(figsize=(8, 4.5))
    plt.plot(xs, qps, marker="o", linewidth=2)
    plt.title("QPS vs Concurrency")
    plt.xlabel("Concurrency")
    plt.ylabel("QPS (OK / s)")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "qps_vs_concurrency.png"), dpi=160)
    plt.close()

    plt.figure(figsize=(8, 4.5))
    plt.plot(xs, p50, marker="o", linewidth=2, label="p50")
    plt.plot(xs, p95, marker="o", linewidth=2, label="p95")
    plt.title("Latency vs Concurrency")
    plt.xlabel("Concurrency")
    plt.ylabel("Latency (ms)")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "latency_vs_concurrency.png"), dpi=160)
    plt.close()

    plt.figure(figsize=(8, 4.5))
    plt.plot(xs, err_rate, marker="o", linewidth=2, color="crimson")
    plt.title("Error Rate vs Concurrency")
    plt.xlabel("Concurrency")
    plt.ylabel("Error Rate")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "error_rate_vs_concurrency.png"), dpi=160)
    plt.close()


def _write_summary_csv(summary_rows: List[Dict[str, Any]], out_csv_path: str) -> None:
    os.makedirs(os.path.dirname(out_csv_path), exist_ok=True)
    fieldnames = [
        "concurrency",
        "duration_s",
        "total_requests",
        "ok_requests",
        "error_requests",
        "error_rate",
        "qps",
        "latency_ms_mean",
        "latency_ms_p50",
        "latency_ms_p90",
        "latency_ms_p95",
        "latency_ms_p99",
    ]
    with open(out_csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in summary_rows:
            writer.writerow({k: row.get(k, "") for k in fieldnames})


async def main_async() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:5000", help="Backend base url")
    parser.add_argument("--scenario", default="read_mix", choices=["read_mix", "write_mix", "appointment_mix", "ai_mix"])
    parser.add_argument("--concurrency-list", default="1,5,10,20,40", help="e.g. 1,5,10,20")
    parser.add_argument("--duration", type=int, default=15, help="Per concurrency duration (seconds)")
    parser.add_argument("--timeout-total", type=float, default=10.0, help="Per request timeout (seconds)")
    parser.add_argument("--warmup", type=int, default=2, help="Warmup seconds (excluded from percentiles)")
    parser.add_argument("--enable-ai", action="store_true", help="Enable AI endpoint testing (may require valid API key)")
    parser.add_argument("--ai-message", default="我需要一些健康建议：我最近总是头晕、乏力。", help="AI message for testing")
    parser.add_argument("--output-dir", default=None, help="Output directory for CSV/PNG")
    args = parser.parse_args()

    concurrency_list = [int(x.strip()) for x in args.concurrency_list.split(",") if x.strip()]

    enable_ai = args.enable_ai
    specs = _build_scenario(args.scenario, enable_ai=enable_ai, ai_message=args.ai_message)

    out_dir = args.output_dir
    if not out_dir:
        stamp = time.strftime("%Y%m%d_%H%M%S", time.localtime())
        out_dir = os.path.join(os.path.dirname(__file__), "results", f"{args.scenario}_{stamp}")
    os.makedirs(out_dir, exist_ok=True)
    summary_csv_path = os.path.join(out_dir, "concurrency_summary.csv")

    timeout = aiohttp.ClientTimeout(total=None, sock_connect=5, sock_read=args.timeout_total)
    headers = {"User-Agent": "medical-perf-test"}

    async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
        summary_rows: List[Dict[str, Any]] = []
        for c in concurrency_list:
            row = await run_concurrency_level(
                session=session,
                base_url=args.base_url,
                specs=specs,
                concurrency=c,
                duration_s=args.duration,
                timeout_total_s=args.timeout_total,
                warmup_s=args.warmup,
            )
            summary_rows.append(row)
            _write_summary_csv(summary_rows, summary_csv_path)
            # 控制台输出用于人工确认曲线是否明显异常
            print(
                f"[{args.scenario}] concurrency={c} "
                f"qps={row['qps']:.3f} p95={row['latency_ms_p95']:.1f}ms "
                f"err_rate={row['error_rate']:.3%} ok={row['ok_requests']} total={row['total_requests']}"
            )

    _plot_concurrency(summary_csv_path, out_dir)
    print(f"Done. Results saved to: {out_dir}")


def main() -> None:
    asyncio.run(main_async())


if __name__ == "__main__":
    main()

