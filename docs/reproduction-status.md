# 复现状态与待办

[返回 README](../README.md)

本次范围是整理仓库、同步必要导入、提供预处理参数和补充文档。模型计算、原有标签算法、Joern 算法和指标公式均保留，不代表已完成论文复现。

## 可用范围

| 内容 | 状态 |
| --- | --- |
| 分类目录、包文件、导入路径、文档链接 | 已整理 |
| Juliet 元数据构建与随机划分 | 有 CLI，可进行小规模流程核验；标签质量仍需单独审核 |
| CodeBERT、GGNN、Transformer、分类头和损失 | 有组件实现，未完成端到端训练验证 |
| `JulietDataset` | 有单样本读取与缓存实现，缺训练 collate 和图批处理 |
| 训练/评测入口 | 有框架，存在下表阻塞项 |
| Joern 抽图与 Big-Vul 迁移 | 抽图接口未验证；Big-Vul 加载及补丁映射缺失 |
| 论文结果 | 仅从稿件转录，没有重跑 |

## 训练与数据阻塞项

| 优先顺序 | 位置 | 当前问题 | 下一步 |
| --- | --- | --- | --- |
| 1 | [`main.py`](../main.py) / `data/` | 引用了不存在的 `data.linevul_loader.build_dataloader` | 实现读取 split CSV、CWE 映射、行 padding、图批处理和 `build_dataloader` |
| 2 | [`config.py`](../config.py) / `main.py` | `Config(**vars(args))` 接收了未声明的 `mode`、`model_path`；`cfg.project_split` 也未声明 | 明确运行参数与模型配置的边界，统一传参 |
| 3 | [`data/juliet_dataset.py`](../data/juliet_dataset.py) | 缺少 `line_mask`、`cwe_labels`、批次 `graph`；`file_label` 命名与入口不同 | 按[数据接口](data-format.md)组装 batch，转换标签 dtype |
| 4 | [`training/train.py`](../training/train.py) / [`training/evaluate.py`](../training/evaluate.py) | 仅对 Tensor 调用 `.to(device)`，PyG 图对象未迁移 | 将图及其边索引迁移到相同设备，检查批内节点对应关系 |
| 5 | [`graph/graph_builder.py`](../graph/graph_builder.py) / [`graph/run_joern.py`](../graph/run_joern.py) | Joern 调用、输出解析和两种图格式未打通 | 固定工具版本、结构化导出、验证行号并记录抽图失败 |
| 6 | [`data/build_metadata.py`](../data/build_metadata.py) / [`data/split_metadata.py`](../data/split_metadata.py) | 只有被标记的漏洞文件，缺负样本、去重和 AST 过滤 | 对齐论文数据协议后再切分，记录样本统计与泄漏检查 |

以上为静态检查发现的原有问题。缺失 dataloader 是实质性缺口，不能通过修改目录名来解决。

## 训练行为与实验设置

- `Config` 定义了 `use_multitask` 和 `no_multitask`，但入口始终创建并计算三个预测头，损失也始终计算三项 BCE。即使 `lambda_cwe=0`，仍需要形状正确的 CWE 标签。关闭多任务的布尔值没有关闭文件级损失。
- `gradient_clip` 配置未被使用，训练代码固定裁剪为 `1.0`；`early_stop_patience` 也未驱动训练停止。
- `LineTransformer` 未添加论文提及的显式位置编码。
- 数据集默认行数/token 上限与全局配置不同；全局 batch size 8 与论文的 16 不同。
- 评测入口没有强制要求 `--model_path`，权重加载也未指定设备映射；需在明确训练环境后完善。

这些改动会影响实验行为，应在完成数据与配置接口后单独实现、验证并记录，而不是混入文件迁移。

## 评测指标缺口

[`training/evaluate.py`](../training/evaluate.py) 当前返回：行级 Precision、Recall、F1、AUC，文件级 AUC、Accuracy，以及 CWE macro-F1。

| 指标 / 协议 | 当前情况 |
| --- | --- |
| 论文 Top-5 / Top-10 Recall | 未实现并接入；需明确逐样本排序、padding 过滤和命中目标 |
| 文件级 F1 / MCC | 未汇总 |
| CWE micro-F1 | 未汇总 |
| Big-Vul 补丁代理目标 | 未提供构建及评测实现 |
| `recall_at_20_percent` | 实际返回前 20% 行是否命中任一正例的 0/1，不能等同行级 recall 比例 |
| `effort_at_20_percent` | 实际返回前 20% 行覆盖的正例比例，名称与常见 effort 含义不一致 |
| 排序辅助函数 | 在 `evaluate.py` 中被导入，但未调用或写入结果 |

在对齐定义前，不应使用现有两个“20%”函数替代论文的 Top-k 结果。还需明确单类样本、无漏洞文件和空预测的聚合规则。

## 本次验证记录

验证环境为 Python 3.12.5。以下检查已通过：

- 16 个迁移文件全部保留；未调整的模型、训练、图和工具源码保持一致，原 Poetry 配置及锁文件未改写。
- 23 个 Python 文件通过语法编译；标注和 CSV 构建函数的 AST 与整理前一致。
- 57 处 Markdown 本地链接目标存在，代码围栏成对。
- 两个预处理模块的 `--help` 正常；不存在的输入路径、比例和不为 1、零比例均返回命令行错误。
- 合成夹具中 20 个带标记文件生成了预期字段和行标签，无标记文件被跳过。
- 默认比例输出 16/2/2 条记录，三个集合互斥且完整覆盖输入；相同种子运行两次，输出逐字节一致。
- 静态本地导入检查仅发现已有且已记录的缺失模块 `data.linevul_loader`。

合成夹具用于验证路径接口和数据流，不等价于真实 Juliet 标注准确率验证。完整模型训练、CodeBERT 权重下载、Joern 运行、GPU 训练、真实数据集评测和论文数值复现不在本次已验证范围内。
