# 数据格式与预处理

[返回 README](../README.md)

## 目录与命令

`data/` 是代码包；原始数据、CSV、Joern 导出和缓存放在本地 `datasets/` 下，例如：

```text
datasets/juliet/
├── testcases/                   # 自行准备的 Juliet 源码
├── metadata/
│   ├── metadata.csv
│   ├── metadata_train.csv
│   ├── metadata_val.csv
│   └── metadata_test.csv
└── joern/
    └── <source_path_md5>/
        ├── cfg.json
        └── dfg.json
```

从仓库根目录运行：

```bash
python -m data.build_metadata --source-root datasets/juliet/testcases --output-csv datasets/juliet/metadata/metadata.csv --project-name Juliet
python -m data.split_metadata --metadata datasets/juliet/metadata/metadata.csv --output-dir datasets/juliet/metadata --train-ratio 0.8 --val-ratio 0.1 --test-ratio 0.1 --seed 42
```

两步使用同一份 CSV 路径。切分器保留表中全部列，按行随机切分；不会自动执行项目隔离、函数去重、AST 相似性过滤或标签分层。相同种子可固定同一输入顺序下的划分，不能替代防止样本泄漏的处理。

## CSV 字段

| 字段 | 当前表示 | 说明 |
| --- | --- | --- |
| `file_path` | 字符串 | 构建器保存源码的绝对路径；换机器后需重建或重映射 |
| `line_labels` | 空格分隔的 `0`/`1` | 对应 `splitlines()` 后的物理行，包含空行、注释等位置 |
| `file_label` | `0`/`1` | 文件是否有被标记的漏洞行；当前构建器只输出 `1` |
| `cwe_label` | 整数 | 从文件名 `CWE<number>` 提取，未匹配时为 `-1` |
| `project_name` | 字符串 | 默认 `Juliet`；仅保存名称，未实现项目级划分 |

示意记录如下，路径与标签仅用于说明格式：

```csv
file_path,line_labels,file_label,cwe_label,project_name
/absolute/path/CWE121_example.c,0 0 1 0,1,121,Juliet
```

`cwe_label=121` 是 CWE 编号，不能直接用作 9 维预测头的类别下标；需建立并持久保存 CWE 词表，再转换为与预测头维度一致的 multi-hot 向量。

## 当前标注规则及边界

[`build_metadata.py`](../data/build_metadata.py) 只遍历 `.c` 文件，通过正则寻找 `bad(...)`，在其后遇到 `FLAW:` / `POTENTIAL FLAW:` 注释时，启发式标记后续非空代码行。未找到正例的文件被跳过。

这是现有的轻量标注实现，存在以下限制：

- “非空代码行”不一定等同于 C 语法意义上的可执行语句；函数调用、宏、括号和复杂注释可能影响识别。
- 不扫描 `.cpp`，也不主动构建 `good` 函数或无漏洞文件的负样本。
- 没有论文所述函数哈希去重、AST 过滤和歧义样本验证。
- 仅用该 CSV 训练文件级二分类会缺少负类，不能据此报告论文的完整文件级检测结果。

本次保留标注算法，仅将输入/输出路径改为参数。

## JulietDataset 与图 JSON

[`JulietDataset`](../data/juliet_dataset.py) 是可单独导入的 `torch.utils.data.Dataset` 类，**不是完整训练 dataloader**。它读取 CSV 中的 `file_path`、`line_labels` 和 `file_label`，跳过不存在的源码路径；当前不读取 CWE 标签或项目列。

每份源码的图目录名为：`hashlib.md5(str(src.resolve()).encode()).hexdigest()`。这是绝对路径字符串的哈希，图导出与读取时必须使用一致的路径；迁移源码位置或更换路径表示后需重建目录映射。

`cfg.json` 和 `dfg.json` 分别使用以下结构；文件中的行号从 **1** 开始：

```json
{
  "edges": [
    {"srcLine": 2, "dstLine": 7},
    {"srcLine": 7, "dstLine": 9}
  ]
}
```

[`load_joern_edges()`](../graph/joern_utils.py) 跳过缺少源/目标行号的边，并将行号减 1。它不验证越界行号；图裁剪和校验仍需在批处理前完成。

### 当前图相关文件的关系

| 文件 | 输入 / 输出 | 当前限制 |
| --- | --- | --- |
| `graph/joern_utils.py` | 读取单个 `{"edges": [...]}` JSON | 与 JulietDataset 的预导出图目录配合 |
| `graph/run_joern.py` | `extract_cfg_dfg(src_file, out_file)` 写出 `{"cfg": ..., "dfg": ...}` | 无 CLI；输出格式不能直接作为上述两个 JSON 使用 |
| `graph/graph_builder.py` | 抽取依赖并生成 PyG `Data`，关系 0=控制流、1=数据流 | 独立路径，未由现有 Dataset 调用 |

两个 Joern 抽取实现都尚未形成已验证的批量导出流程：当前将脚本文本传入 `--script`，并用 `eval()` 解析标准输出；需要依据实际 Joern 版本改为可靠的脚本调用和结构化 JSON 解析。`graph_builder.py` 还会在异常时退化为空图，排查时不能仅凭“返回了 Data 对象”判断抽图成功。

### 单个样本输出

设 `L` 为截断后的有效行数，`T` 为每行 token 上限：

| 字段 | 当前类型 / 形状 | 说明 |
| --- | --- | --- |
| `input_ids` | 整数张量 `(L,T)` | 逐行 tokenize，行内 padding |
| `attention_mask` | 整数张量 `(L,T)` | 行内 token 掩码 |
| `line_labels` | 整数张量 `(L,)` | 训练 BCE 前需转浮点 |
| `file_label` | 整数标量 | 注意是单数，与入口要求的 `file_labels` 不同 |
| `cfg_edges`、`dfg_edges` | 一般为 `(E,2)` 的整数张量 | 空列表当前生成 `(0,)`，需要归一化 |
| `file_path` | 字符串 | 原源码路径 |

类默认 `max_tokens=512`、`max_lines=512`，与全局配置的 128/400 不一致。样本只在行内补齐，行数可变；空文件或零行样本需处理 `torch.stack([])` 的情况。缓存默认在 `.cache/juliet/`，缓存键未纳入源码内容和标签版本，修改数据后应重建缓存。

## 训练入口要求的批次

以下是依据 `main.py` 与损失函数推导的**待实现接口**，不是现有 Dataset 已经返回的格式。设 `B` 为 batch size，`L` 为批内补齐后的行数，`C` 为 CWE 类别数：

| 字段 | 约定形状 / 类型 | 消费方 |
| --- | --- | --- |
| `input_ids` | `(B,L,T)`，整数 | CodeBERT |
| `attention_mask` | `(B,L,T)`，整数 | CodeBERT |
| `line_mask` | `(B,L)`，布尔，有效行为 `True` | 编码器、Transformer、池化、损失 |
| `line_labels` | `(B,L)`，浮点 0/1 | 行级 BCE |
| `file_labels` | `(B,)`，浮点 0/1 | 文件级 BCE |
| `cwe_labels` | `(B,C)`，浮点 multi-hot | CWE BCE |
| `graph` | PyG 图 / Batch | GGNN，需要 `edge_index` 和 `edge_type` |

`main.py` 会把 `(B,L,D)` 展平为 `(B*L,D)` 注入图节点，因此批处理必须保证节点顺序、padding 行以及边索引偏移与之对齐，避免不同样本之间意外连边。仅对变长样本使用默认 DataLoader collate 不满足这个约定。

Big-Vul 数据读取、补丁行到源码行的映射、代理定位标签和跨数据集评测尚未包含在仓库中。
