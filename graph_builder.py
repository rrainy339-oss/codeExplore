"""
graph_builder.py
=================================================
CFG / DFG extraction using Joern and construction
of line-level program graphs for GGNN.

Each node corresponds to ONE LINE.
Edges are control-flow or data-flow relations.

Paper equations:
m_i^k = sum_j W_r h_j^{k-1}
h_i^k = GRU(h_i^{k-1}, m_i^k)
"""

import os
import subprocess
import tempfile
import json
import torch
from torch_geometric.data import Data


EDGE_TYPE = {
    "control": 0,
    "data": 1
}


def run_joern(file_path: str):
    """
    Run Joern on a single file and export CFG/DFG edges.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        cpg_bin = os.path.join(tmpdir, "cpg.bin")

        subprocess.run(
            ["joern-parse", file_path, "--out", cpg_bin],
            check=True,
            stdout=subprocess.DEVNULL
        )

        script = """
        importCode("%s")
        cfgEdges = cpg.cfgE.map(e => (e.src.lineNumber, e.dst.lineNumber)).l
        dfgEdges = cpg.ddgE.map(e => (e.src.lineNumber, e.dst.lineNumber)).l
        println(cfgEdges)
        println(dfgEdges)
        """ % file_path

        result = subprocess.run(
            ["joern", "--script", script],
            capture_output=True,
            text=True
        )

        return parse_joern_output(result.stdout)


def parse_joern_output(output: str):
    """
    Parse Joern stdout into CFG / DFG edge lists.
    """
    lines = output.strip().splitlines()
    cfg_edges = eval(lines[0]) if lines else []
    dfg_edges = eval(lines[1]) if len(lines) > 1 else []
    return cfg_edges, dfg_edges


def build_program_graph(file_path: str, max_lines: int):
    """
    Build PyG graph:
    - Nodes: code lines
    - Edge index: [2, E]
    - Edge type: relation id
    """
    try:
        cfg_edges, dfg_edges = run_joern(file_path)
    except Exception:
        cfg_edges, dfg_edges = [], []

    edge_index = []
    edge_type = []

    for src, dst in cfg_edges:
        if src is None or dst is None:
            continue
        if src <= max_lines and dst <= max_lines:
            edge_index.append([src - 1, dst - 1])
            edge_type.append(EDGE_TYPE["control"])

    for src, dst in dfg_edges:
        if src is None or dst is None:
            continue
        if src <= max_lines and dst <= max_lines:
            edge_index.append([src - 1, dst - 1])
            edge_type.append(EDGE_TYPE["data"])

    if len(edge_index) == 0:
        edge_index = torch.empty((2, 0), dtype=torch.long)
        edge_type = torch.empty((0,), dtype=torch.long)
    else:
        edge_index = torch.tensor(edge_index, dtype=torch.long).t().contiguous()
        edge_type = torch.tensor(edge_type, dtype=torch.long)

    # Node features will be injected later (CodeBERT CLS)
    x = torch.zeros((max_lines, 768), dtype=torch.float)

    return Data(
        x=x,
        edge_index=edge_index,
        edge_type=edge_type
    )
