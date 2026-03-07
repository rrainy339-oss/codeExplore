import re
import csv
from pathlib import Path
from typing import List, Tuple

# =======================
# Regex Patterns
# =======================
BAD_FUNC_PATTERN = re.compile(r"bad\s*\(", re.IGNORECASE)
# 保留FLAW注释正则，兼容冒号前有空格的情况
FLAW_COMMENT_PATTERN = re.compile(r"(flaw\s*:|potential flaw\s*:)", re.IGNORECASE)
CWE_PATTERN = re.compile(r"CWE(\d+)")
COMMENT_PREFIXES = ("/*", "*", "//")

# =======================
# Utils
# =======================
def extract_cwe_label(filename: str) -> int:
    """
    Extract CWE ID from Juliet filename.
    Example: CWE114_Process_Control__w32_02.c → 114
    """
    m = CWE_PATTERN.search(filename)
    return int(m.group(1)) if m else -1

# =======================
# Core Labeling Logic
# =======================
def label_file(src: Path) -> Tuple[List[int], int]:
    """
    Line-level labeling for one .c/.cpp file.
    """
    lines = src.read_text(encoding="utf-8", errors="ignore").splitlines()  # 加encoding=utf-8，避免乱码
    n_lines = len(lines)
    labels = [0] * n_lines

    in_bad_func = False
    brace_depth = 0
    in_block_comment = False
    pending_flaw = False
    has_flaw = False

    for i, line in enumerate(lines):
        stripped = line.strip()

        # =======================
        # Enter bad() function（修复后正则）
        # =======================
        if BAD_FUNC_PATTERN.search(line):
            in_bad_func = True
            brace_depth = 0
            pending_flaw = False
            in_block_comment = False
            continue

        if in_bad_func:
            # =======================
            # Multi-line block comment（修复后）
            # =======================
            if "/*" in stripped:
                in_block_comment = True
            if "*/" in stripped:
                in_block_comment = False
            # 跳过注释行，但先检测FLAW
            if in_block_comment or stripped.startswith(COMMENT_PREFIXES):
                if FLAW_COMMENT_PATTERN.search(stripped):
                    pending_flaw = True
                continue

            # =======================
            # Update brace depth（修复后）
            # =======================
            brace_depth += line.count("{")
            brace_depth -= line.count("}")

            # =======================
            # Detect FLAW comment（非注释行也可能有行内注释）
            # =======================
            if FLAW_COMMENT_PATTERN.search(stripped):
                pending_flaw = True
                continue

            # =======================
            # Label the first executable line after FLAW comment
            # =======================
            if pending_flaw:
                if stripped:  # 非空行就是可执行代码行
                    labels[i] = 1
                    has_flaw = True
                    pending_flaw = False

            # =======================
            # Exit bad() function
            # =======================
            if brace_depth <= 0:
                in_bad_func = False
                pending_flaw = False
                in_block_comment = False

    return labels, int(has_flaw)
# =======================
# Metadata Builder
# =======================
def build_metadata(
    source_root: Path,
    output_csv: Path,
    project_name: str = "Juliet"
):
    """
    Traverse Juliet source tree and build metadata.csv
    """
    rows = []
    total = ok = skipped = 0

    for c_file in source_root.rglob("*.c"):
        total += 1
        labels, file_label = label_file(c_file)

        if file_label == 0:
            skipped += 1
            continue

        cwe_label = extract_cwe_label(c_file.name)

        rows.append({
            "file_path": str(c_file.resolve()),
            "line_labels": " ".join(map(str, labels)),
            "file_label": file_label,
            "cwe_label": cwe_label,
            "project_name": project_name
        })
        ok += 1

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with output_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "file_path",
                "line_labels",
                "file_label",
                "cwe_label",
                "project_name"
            ]
        )
        writer.writeheader()
        writer.writerows(rows)

    print("====== Juliet → CodeExplorer metadata ======")
    print(f"total files : {total}")
    print(f"with flaw   : {ok}")
    print(f"skipped     : {skipped}")
    print(f"saved to    : {output_csv}")
    print("===========================================")

# =======================
# Entry
# =======================
if __name__ == "__main__":
    JULIET_SRC = Path(r"juliet-dynamic-master\testcases")  # Juliet 数据集路径
    OUTPUT_CSV = Path(r"metadata\metadata_juliet.csv")

    build_metadata(
        source_root=JULIET_SRC,
        output_csv=OUTPUT_CSV,
        project_name="Juliet"
    )
