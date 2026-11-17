"""Fake programs and pipeline integration checks. Never calls an author CLI."""

import argparse
import collections
import json
from pathlib import Path

from bench import config as C
from bench.common import read_csv, write_json, write_text
from bench.measure import Harness, machine
from bench import selftest_langs

HEAT_RS = r'''
use std::{env, fs};
fn main() {
    let text = fs::read_to_string(env::args().nth(1).unwrap()).unwrap();
    let mut lines = text.lines();
    let dims: Vec<usize> = lines.next().unwrap().split_whitespace().map(|x| x.parse().unwrap()).collect();
    let (h,w,s) = (dims[0],dims[1],dims[2]);
    let cells: Vec<u8> = lines.flat_map(|line| line.bytes()).collect();
    let mut values = vec![0i64; h*w];
    for i in 0..h*w {
        if cells[i].is_ascii_digit() { values[i] = (cells[i]-b'0') as i64 * 1000; }
    }
    for _ in 0..s {
        let mut next = values.clone();
        for r in 0..h { for c in 0..w {
            let i = r*w+c;
            if cells[i] != b'.' { continue; }
            let mut total = 4*values[i];
            let neighbours = [if r>0 {Some(i-w)} else {None}, if r+1<h {Some(i+w)} else {None},
                              if c>0 {Some(i-1)} else {None}, if c+1<w {Some(i+1)} else {None}];
            for neighbour in neighbours {
                total += match neighbour {Some(j) if cells[j] != b'#' => values[j], _ => values[i]};
            }
            next[i] = total/8;
        }}
        values = next;
    }
    let (mut total,mut checksum,mut maximum,mut winner) = (0i64,0i64,-1i64,0usize);
    for i in 0..h*w { if cells[i] == b'.' {
        total += values[i]; checksum += values[i]*(i as i64+1);
        if values[i]>maximum { maximum=values[i]; winner=i; }
    }}
    println!("sum {}\nmax {} {} {}\nchecksum {}",total,maximum,winner/w,winner%w,checksum);
}
'''

WALKERS_RS = r'''
use std::{env,fs,thread};
#[derive(Default)]
struct Answer { spread:i64, bumps:i64, returns:i64, winner:usize, far:i64 }
fn main() {
    let args: Vec<String> = env::args().collect();
    let text = fs::read_to_string(&args[1]).unwrap();
    let nums: Vec<u64> = text.split_whitespace().map(|x| x.parse().unwrap()).collect();
    let (walkers,length,bound,seed) = (nums[0] as usize,nums[1],nums[2] as i64,nums[3]);
    let workers:usize = args[2].parse().unwrap();
    let parts = thread::scope(|scope| {
        let handles: Vec<_> = (0..workers).map(|worker| scope.spawn(move || {
            let mut ans = Answer { far:-1, ..Default::default() };
            for j in (worker..walkers).step_by(workers) {
                let mut state = seed.wrapping_add(j as u64);
                let (mut x,mut y) = (0i64,0i64);
                for _ in 0..length {
                    state = state.wrapping_add(0x9E3779B97F4A7C15);
                    let mut z = state;
                    z = (z^(z>>30)).wrapping_mul(0xBF58476D1CE4E5B9);
                    z = (z^(z>>27)).wrapping_mul(0x94D049BB133111EB);
                    let d = (z^(z>>31))>>62;
                    let (mut nx,mut ny) = (x,y);
                    match d { 0=>nx+=1, 1=>nx-=1, 2=>ny+=1, _=>ny-=1 }
                    if nx.abs()>bound || ny.abs()>bound { ans.bumps+=1; }
                    else { x=nx;y=ny;if x==0 && y==0 { ans.returns+=1; } }
                }
                ans.spread+=x*x+y*y;
                let distance=x.abs()+y.abs();
                if distance>ans.far || (distance==ans.far && j<ans.winner) { ans.far=distance;ans.winner=j; }
            }
            ans
        })).collect();
        handles.into_iter().map(|h| h.join().unwrap()).collect::<Vec<_>>()
    });
    let mut answer = Answer {far:-1,..Default::default()};
    for part in parts {
        answer.spread+=part.spread;answer.bumps+=part.bumps;answer.returns+=part.returns;
        if part.far>answer.far || (part.far==answer.far && part.winner<answer.winner) {
            answer.far=part.far;answer.winner=part.winner;
        }
    }
    println!("spread {}\nbumps {}\nreturns {}\nfarthest {} {}",answer.spread,answer.bumps,answer.returns,answer.winner,answer.far);
}
'''


def setup():
    body = (C.BENCH / "reference.py").read_text(encoding="utf-8").split("\ndef batch():")[0]
    for task in C.TASKS:
        folder = C.WORK / "selftest_programs/selftest" / task
        main = f'\nif __name__ == "__main__":\n    output = solve({task!r}, sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 1)\n'
        write_text(folder / "plain.py", body + main + '    print(output, end="")\n')
        bug = ""
        if task == "wordpairs":
            bug = '    output = output.replace("words ", "words -", 1)\n'
        elif task == "ledger":
            bug = '    output = output.replace("counted ", "COUNTED ", 1)\n'
        write_text(folder / "fast.py", body + main + bug + '    print(output, end="")\n')
        if task in ("heat", "walkers", "align"):
            write_text(folder / "rust/Cargo.toml", (C.BENCH / "template/rust/Cargo.toml").read_text())
            write_text(folder / "rust/src/main.rs", HEAT_RS if task == "heat" else WALKERS_RS if task == "walkers" else "fn main() { let broken = ; }\n")


def report(harness):
    correct = harness.rows("correctness")
    correct = [r for r in correct if r["input_sha256"] == harness.entry(r["task"], r["input"])["sha256"]]
    builds = harness.rows("builds")
    scaling = harness.rows("scaling")
    sweep = harness.rows("sweep")
    timed = harness.rows("runs")
    counts = dict(collections.Counter(row["status"] for row in correct))
    assert counts.get("wrong", 0), counts
    assert counts.get("unreadable", 0), counts
    assert any(r["status"] == "build_failed" and r["task"] == "align" for r in builds)
    for task in C.TASKS:
        assert any(r["task"] == task and r["variant"] == "plain" and r["input"] == "full" and r["status"] == "correct" for r in correct)
    for task in ("heat", "walkers"):
        assert any(r["task"] == task and r["variant"] == "rust" and r["input"] == "full" and r["status"] == "correct" for r in correct)
    rust_16 = [r for r in scaling if r["variant"] == "rust" and int(r["workers"]) == 16 and int(r["repeat"]) >= 0]
    assert rust_16 and all(r["status"] == "correct" for r in rust_16)
    assert max(float(r["cpu_wall_ratio"]) for r in rust_16) > 1
    plain_16 = [r for r in scaling if r["variant"] == "plain" and int(r["workers"]) == 16]
    assert plain_16 and all(float(r["cpu_wall_ratio"]) > 1 for r in plain_16)
    assert sweep and all(r["status"] == "correct" for r in sweep)
    measured = [r for r in correct + timed + scaling if r["status"] == "correct" and r["peak_job_commit"]]
    assert all(100_000 < int(r["peak_job_commit"]) < 32 * 1024**3 for r in measured)
    expected_affinity = ",".join(map(str, harness.cpu["p_cores"]))
    assert all(r["affinity"] == expected_affinity for r in measured if r["task"] != "walkers")
    assert all(r["affinity"] == "all" for r in measured if r["task"] == "walkers")
    result = dict(correctness_statuses=counts, builds=[{k: r[k] for k in ("task", "status", "clean_seconds", "crates_kept")} for r in builds],
                  timed_statuses=dict(collections.Counter(r["status"] for r in timed)),
                  scaling_statuses=dict(collections.Counter(r["status"] for r in scaling)),
                  sweep_statuses=dict(collections.Counter(r["status"] for r in sweep)),
                  rust_16_cpu_wall_ratios=[float(r["cpu_wall_ratio"]) for r in rust_16],
                  plain_16_cpu_wall_ratios=[float(r["cpu_wall_ratio"]) for r in plain_16],
                  row_counts={name: len(harness.rows(name)) for name in ("baseline", "builds", "loc", "correctness", "runs", "sweep", "scaling")},
                  current_correctness_rows=len(correct),
                  peak_commit_range=[min(int(r["peak_job_commit"]) for r in measured), max(int(r["peak_job_commit"]) for r in measured)],
                  p_core_affinity=expected_affinity, assertions="passed")
    write_json(harness.results / "summary.json", result)
    print(json.dumps(result, indent=2))


def languages():
    folder = C.WORK.resolve() / "selftest_programs" / "languages" / "heat"
    for lang, name, code in (("cpp", "main.cpp", selftest_langs.CPP), ("java", "src/Main.java", selftest_langs.JAVA),
                             ("csharp", "Program.cs", selftest_langs.CSHARP), ("go", "main.go", selftest_langs.GO),
                             ("js", "main.js", selftest_langs.JS)):
        write_text(folder / lang / name, code)
        for extra in {"csharp": ["solution.csproj"], "go": ["go.mod"]}.get(lang, []):
            write_text(folder / lang / extra, (C.BENCH / "template" / lang / extra).read_text())
    broken = C.WORK.resolve() / "selftest_programs" / "broken" / "heat" / "cpp/main.cpp"
    write_text(broken, "int main() { broken syntax }\n")
    harness = Harness(selftest=True, tasks=("heat",), authors=("languages", "broken"), repeats=2)
    harness.results = C.WORK.resolve() / "selftest_langs_results"
    harness.build_root = C.WORK.resolve() / "selftest_langs_build"
    harness.run_root = C.WORK.resolve() / "selftest_langs_runs"
    harness.build(); harness.loc()
    for lang in C.LANG_VARIANTS:
        for name in (*C.TINY["heat"], "s2", "s3", "t1"):
            harness.run_one("correctness", "languages", "heat", lang, name, 1, 0, C.CORRECT_TIMEOUT)
        for repeat in range(2):
            harness.run_one("runs", "languages", "heat", lang, "t1", 1, repeat, C.MEASURE_TIMEOUT)
    builds = [r for r in harness.rows("builds") if r["author"] in ("languages", "broken")]
    rows = [r for r in harness.rows("runs") if r["author"] == "languages" and r["task"] == "heat" and r["input"] == "t1"]
    checks = [r for r in harness.rows("correctness") if r["author"] == "languages" and r["task"] == "heat"]
    for lang in C.LANG_VARIANTS:
        assert any(r["variant"] == lang and r["status"] == "ok" for r in builds), lang
        assert len([r for r in checks if r["variant"] == lang and r["status"] == "correct"]) == len(C.TINY["heat"]) + 3, lang
        measured = [r for r in rows if r["variant"] == lang and r["status"] == "correct"]
        assert len(measured) == 2 and all(r["cpu_wall_ratio"] and int(r["peak_working_set"]) > 0 for r in measured), lang
    assert any(r["author"] == "broken" and r["status"] == "build_failed" for r in builds)
    print(json.dumps(dict(builds=builds, runs=rows), indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["setup", "run", "report", "languages"], default="run", nargs="?")
    args = parser.parse_args()
    if args.command == "languages":
        languages()
        return
    if args.command == "setup":
        setup()
        return
    harness = Harness(selftest=True, repeats=C.SELFTEST_REPEATS)
    if args.command == "run":
        setup()
        machine(harness.results / "machine.json")
        for command in ("baseline", "build", "loc", "correct", "bench", "sweep", "scaling"):
            getattr(harness, command)()
    report(harness)


if __name__ == "__main__":
    main()
