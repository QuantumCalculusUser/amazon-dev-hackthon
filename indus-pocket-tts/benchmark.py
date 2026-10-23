#!/usr/bin/env python3
"""Reproduce the indus-pocket-tts latency table.

    python benchmark.py            # full precision, one stream
    python benchmark.py --int8     # compressed weights
    python benchmark.py --streams 4

Method: 20 Hindi/Hinglish call-centre lines (bench_prompts.json); each stream is its own process
with PyTorch pinned to one CPU thread; the model and voice are loaded and warmed up before timing.
"First audio" is measured from submitting the text, normalisation included, to the first audio chunk.
"""
import argparse, json, multiprocessing as mp, os, platform, resource, statistics, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))


def run_stream(args):
    int8, threads, n_lines = args
    sys.path.insert(0, HERE)
    import speak
    model, voice = speak.load(int8=int8, threads=threads)
    for _ in speak.stream(model, voice, "नमस्ते जी, आपका स्वागत है।"):   # warm-up, not timed
        pass
    prompts = json.load(open(os.path.join(HERE, "bench_prompts.json"), encoding="utf-8"))[:n_lines]
    rows, cpu = [], 0.0
    for p in prompts:
        c0, t0, first, samples = time.process_time(), time.perf_counter(), None, 0
        for chunk in speak.stream(model, voice, p["text"]):
            if first is None:
                first = time.perf_counter() - t0
            samples += chunk.numel()
        rows.append({"ttfb_ms": first * 1000, "synth_s": time.perf_counter() - t0, "audio_s": samples / speak.SAMPLE_RATE})
        cpu += time.process_time() - c0
    return rows, cpu, resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024


def cpu_name() -> str:
    try:
        for line in open("/proc/cpuinfo"):
            if line.startswith("model name"):
                return line.split(":", 1)[1].strip()
    except OSError:
        pass
    return platform.processor() or platform.machine()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--int8", action="store_true")
    ap.add_argument("--threads", type=int, default=1, help="threads per stream (default 1)")
    ap.add_argument("--streams", type=int, default=1, help="parallel streams, one process each")
    ap.add_argument("--lines", type=int, default=20)
    a = ap.parse_args()
    job = (a.int8, a.threads, a.lines)
    if a.streams == 1:
        results = [run_stream(job)]
    else:
        with mp.get_context("spawn").Pool(a.streams) as pool:
            results = pool.map(run_stream, [job] * a.streams)
    rows = [r for res in results for r in res[0]]
    ttfb = sorted(r["ttfb_ms"] for r in rows)
    pct = lambda q: ttfb[min(len(ttfb) - 1, int(q * len(ttfb)))]
    audio = sum(r["audio_s"] for r in rows)
    print(f"indus-pocket-tts | {'int8' if a.int8 else 'full precision'} | {a.streams} stream(s) x {a.threads} thread(s) | {cpu_name()}")
    print(f"  first audio  p50 {pct(0.5):.0f} ms   p90 {pct(0.9):.0f} ms   (n={len(rows)})")
    print(f"  speed        {audio / sum(r['synth_s'] for r in rows):.2f}x real-time per stream")
    print(f"  CPU          {sum(res[1] for res in results) / audio:.2f} core-seconds per second of audio")
    print(f"  memory       {max(res[2] for res in results) / 1024:.2f} GiB peak per stream")


if __name__ == "__main__":
    main()
