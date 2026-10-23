import torch
from torch.utils.data import Dataset
from pathlib import Path
import csv
import hashlib

from graph.joern_utils import load_joern_edges


class JulietDataset(Dataset):

    def __init__(
        self,
        metadata_path,
        tokenizer,
        joern_root,
        cache_dir=".cache/juliet",
        max_tokens=512,
        max_lines=512,
    ):
        self.metadata_path = Path(metadata_path)
        self.tokenizer = tokenizer
        self.joern_root = Path(joern_root)

        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.max_tokens = max_tokens
        self.max_lines = max_lines

        self.samples = self._load_metadata()

    def _load_metadata(self):
        samples = []
        with self.metadata_path.open(encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                src = Path(row["file_path"])
                if src.exists():
                    samples.append({
                        "file_path": src,
                        "line_labels": list(map(int, row["line_labels"].split())),
                        "file_label": int(row["file_label"]),
                    })
        return samples

    def __len__(self):
        return len(self.samples)

    # ======================
    # cache utils
    # ======================
    def _cache_key(self, src):
        key = f"{src.resolve()}_{self.max_tokens}_{self.max_lines}"
        return hashlib.md5(key.encode()).hexdigest()

    def _cache_path(self, src):
        return self.cache_dir / f"{self._cache_key(src)}.pt"

    # ======================
    # Joern
    # ======================
    def _load_cfg_dfg(self, src: Path):
        """
        假设你已经提前跑好 Joern，结构如下：
        joern_root/
          └── file_hash/
              ├── cfg.json
              └── dfg.json
        """
        h = hashlib.md5(str(src.resolve()).encode()).hexdigest()
        graph_dir = self.joern_root / h

        cfg = load_joern_edges(graph_dir / "cfg.json")
        dfg = load_joern_edges(graph_dir / "dfg.json")

        return cfg, dfg

    # ======================
    # tokenizer
    # ======================
    def _encode(self, lines):
        ids, masks = [], []

        for line in lines[: self.max_lines]:
            t = self.tokenizer(
                line,
                truncation=True,
                padding="max_length",
                max_length=self.max_tokens,
                return_tensors="pt",
            )
            ids.append(t["input_ids"][0])
            masks.append(t["attention_mask"][0])

        return torch.stack(ids), torch.stack(masks)

    # ======================
    # build cache
    # ======================
    def _build_cache(self, sample):
        src = sample["file_path"]
        lines = src.read_text(encoding="utf-8", errors="ignore").splitlines()

        L = min(len(lines), len(sample["line_labels"]), self.max_lines)
        lines = lines[:L]
        labels = sample["line_labels"][:L]

        input_ids, attention_mask = self._encode(lines)
        cfg_edges, dfg_edges = self._load_cfg_dfg(src)

        data = {
            "input_ids": input_ids,
            "attention_mask": attention_mask,
            "line_labels": torch.tensor(labels),
            "file_label": torch.tensor(sample["file_label"]),
            "cfg_edges": torch.tensor(cfg_edges, dtype=torch.long),
            "dfg_edges": torch.tensor(dfg_edges, dtype=torch.long),
            "file_path": str(src),
        }

        torch.save(data, self._cache_path(src))
        return data

    def __getitem__(self, idx):
        sample = self.samples[idx]
        cache_path = self._cache_path(sample["file_path"])

        if cache_path.exists():
            return torch.load(cache_path)

        return self._build_cache(sample)
