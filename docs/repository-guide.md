# 目录与文件迁移

[返回 README](../README.md)

## 分类原则

代码按“数据准备 → 程序图 → 模型 → 训练评测 → 通用工具”分类。`main.py` 继续负责模型组合和入口，`config.py` 继续集中管理参数；`model/` 和 `utils/` 的名称沿用原入口已有的导入约定。

各代码目录均添加 `__init__.py`，不在包导入时主动加载模型、下载权重或运行数据处理。从仓库根目录运行 `python -m data.build_metadata` 等模块命令。

## 逐文件迁移表

| 原位置 | 新位置 | 用途 |
| --- | --- | --- |
| `Build_JulietDataSet.py` | [`data/juliet_dataset.py`](../data/juliet_dataset.py) | 分词、标签读取、CFG/DFG 缓存 |
| `build_metadata.py` | [`data/build_metadata.py`](../data/build_metadata.py) | 生成 Juliet CSV 元数据 |
| `split_metadata.py` | [`data/split_metadata.py`](../data/split_metadata.py) | 按随机种子划分 CSV |
| `graph_builder.py` | [`graph/graph_builder.py`](../graph/graph_builder.py) | Joern 抽图与 PyG `Data` 构建 |
| `joern_utils.py` | [`graph/joern_utils.py`](../graph/joern_utils.py) | 读取预导出 JSON，行号转为从 0 开始 |
| `run_joern.py` | [`graph/run_joern.py`](../graph/run_joern.py) | Joern 导出辅助函数，非完整 CLI |
| `codebert_encoder.py` | [`model/codebert_encoder.py`](../model/codebert_encoder.py) | 每行 CodeBERT `[CLS]` 表示 |
| `ggnn.py` | [`model/ggnn.py`](../model/ggnn.py) | 控制流/数据流消息传递和 GRU 更新 |
| `line_transformer.py` | [`model/line_transformer.py`](../model/line_transformer.py) | 行间全局自注意力 |
| `classification_heads.py` | [`model/classification_heads.py`](../model/classification_heads.py) | 行、文件、CWE 分类与注意力池化 |
| `multitask_loss.py` | [`model/multitask_loss.py`](../model/multitask_loss.py) | 带行掩码的加权多任务 BCE |
| `train.py` | [`training/train.py`](../training/train.py) | 单轮训练与验证 |
| `evaluate.py` | [`training/evaluate.py`](../training/evaluate.py) | 测试集预测和指标汇总 |
| `logger.py` | [`utils/logger.py`](../utils/logger.py) | Loguru 文件与终端日志 |
| `metrics.py` | [`utils/metrics.py`](../utils/metrics.py) | 行级、文件级和 CWE 指标函数 |
| `visualization.py` | [`utils/visualization.py`](../utils/visualization.py) | 训练/验证损失曲线 |
| `main.py`、`config.py` | 根目录保留 | 入口、模型组合和全局配置 |
| `pyproject.toml`、`poetry.toml`、`poetry.lock` | 根目录保留 | 保留原 Poetry 配置以供核对，依赖尚不完整 |
| `README.md` | 根目录重写 | 项目、使用、论文和复现状态说明 |

共迁移 16 个原有 Python 文件，保留其功能划分与模型计算逻辑。旧位置不保留同名代理脚本；外部脚本如曾直接导入旧路径，需要按表更新。

## 同步的接口调整

- `main.py` 的训练和评测导入更新为 `training.train` 与 `training.evaluate`。
- `JulietDataset` 的图工具导入更新为 `graph.joern_utils`。
- 元数据构建新增 `--source-root`、`--output-csv`、`--project-name`，替换机器相关的固定路径。
- 元数据划分新增输入/输出路径、比例和随机种子参数，保留原 scikit-learn 两阶段随机划分算法。
- 新增源码直接依赖清单及 `.gitignore`；没有改写原始 Poetry 锁文件。

本次没有实现缺失的 `data.linevul_loader`，也没有修改模型层、损失、Joern 抽图或指标计算的算法。其已有问题列在[复现状态](reproduction-status.md)。

## 后续文件放置约定

| 内容 | 位置 |
| --- | --- |
| 新数据集读取器和标签处理 | `data/` |
| Joern 脚本、图格式适配 | `graph/` |
| 编码器、图层、预测头、损失函数 | `model/` |
| 训练策略和评测流程 | `training/` |
| 与模型无关的指标、日志和绘图 | `utils/` |
| 论文对照、数据规范和复现记录 | `docs/` |
| 本地数据和实验产物 | `datasets/`、`cache/`、`checkpoints/`、`logs/`，不提交 |
