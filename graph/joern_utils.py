# joern_utils.py
import json
from pathlib import Path


def load_joern_edges(graph_json: Path):
    """
    返回: List[(src_line, dst_line)]
    """
    edges = []

    data = json.loads(graph_json.read_text(encoding="utf-8"))

    for edge in data.get("edges", []):
        src = edge.get("srcLine")
        dst = edge.get("dstLine")
        if src is None or dst is None:
            continue
        edges.append((src - 1, dst - 1))  # 转 0-based

    return edges
