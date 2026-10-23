# run_joern.py
import subprocess
import json
from pathlib import Path

def extract_cfg_dfg(src_file: Path, out_file: Path):
    script = f"""
    importCode("{src_file}")
    cfg = cpg.cfgE.map(e => (e.src.lineNumber, e.dst.lineNumber)).l
    dfg = cpg.ddgE.map(e => (e.src.lineNumber, e.dst.lineNumber)).l
    println(cfg)
    println(dfg)
    """

    result = subprocess.run(
        ["joern", "--script", script],
        capture_output=True,
        text=True,
        check=True
    )

    lines = result.stdout.strip().splitlines()
    cfg = eval(lines[0]) if len(lines) > 0 else []
    dfg = eval(lines[1]) if len(lines) > 1 else []

    out_file.parent.mkdir(parents=True, exist_ok=True)
    json.dump(
        {"cfg": cfg, "dfg": dfg},
        out_file.open("w", encoding="utf-8"),
        indent=2
    )
