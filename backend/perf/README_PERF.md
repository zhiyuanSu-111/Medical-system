# 后端性能测试（本科论文可用数据与图）

## 1. 安装依赖
在项目根目录执行：
```bash
cd backend
pip install -r perf/requirements-perf.txt
```

## 2. 启动后端
```bash
cd backend
python app.py
```
默认监听 `http://127.0.0.1:5000`。

## 3. 并发压测（输出 QPS/延迟/错误率折线图 + CSV）
生成 `backend/perf/results/...` 下的图与数据：
```bash
python perf/load_test_async.py --scenario read_mix --concurrency-list 1,5,10,20,40 --duration 15 --timeout-total 10
```

常用参数：
- `--scenario read_mix`：主要测试读链路（科室/医生/号源）
- `--scenario write_mix`：主要测试写链路（创建就诊人）
- `--scenario appointment_mix`：主要测试预约写链路（会扣减号源，建议并发较低、时长较短）
- `--scenario ai_mix --enable-ai`：测试 AI 接口（需要你配置 DashScope 有效 API Key）
- `--output-dir`：可指定输出目录

会生成：
- `concurrency_summary.csv`
- `qps_vs_concurrency.png`
- `latency_vs_concurrency.png`
- `error_rate_vs_concurrency.png`

## 4. 稳定性测试（长时间并发，输出延迟随时间变化）
```bash
python perf/stability_test_async.py --scenario read_mix --concurrency 20 --duration 120 --timeout-total 10
```
会生成：
- `stability_records.csv`
- `latency_over_time.png`
- `latency_trend_smoothed.png`

## 5. Dijkstra 算法规模基准（输出耗时曲线 + CSV）
```bash
python perf/benchmark_dijkstra.py --v-list 100,200,400,800,1200 --runs 5
```
会生成：
- `dijkstra_time_vs_v.csv`
- `dijkstra_time_vs_v.png`

