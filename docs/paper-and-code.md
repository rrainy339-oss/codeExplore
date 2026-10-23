# 论文与代码对照

[返回 README](../README.md)

来源：用户提供的 `acm_ccs__V4 .pdf`，共 13 页，题名为 *CodeExplorer: Structure-Aware Hierarchical Modeling for Line-Level Vulnerability Localization*。以下页码按 PDF 的页面顺序计数。稿件中的会议信息和 DOI 是占位符，本文不据此推断发表状态。

## 方法主线

论文将漏洞定位描述为稀疏监督下的结构推理：被标注的漏洞行可能只体现问题的最终表现，根因、值传播和控制条件则分布在其他位置。因此，模型结合四类信息：

1. **局部语义**：每行单独通过 CodeBERT，取 `[CLS]` 向量。
2. **显式依赖**：以代码行为节点，以 CFG、DFG 为两类边，通过 GGNN 传播消息。
3. **全局交互**：行级 Transformer 连接远距离或图中未明确表示的语义关系。
4. **多粒度监督**：行级漏洞、文件级风险和 CWE 类别共同约束共享表示。

图 2（第 4 页）展示总体架构，图 3（第 6 页）展示注意力池化及三任务预测。

## 模块及公式对应

| 论文位置 | 方法 | 当前代码 | 实现范围 |
| --- | --- | --- | --- |
| §3.2，式 (1)-(3)，第 3 页 | 每行 token 与 `[CLS]` 表示 | [`CodeBERTEncoder`](../model/codebert_encoder.py) | 行维度展平后送入 `RobertaModel`，输出恢复为 `(B,L,D)` |
| §3.2，式 (4)-(6)，第 3-4 页 | 按边类型聚合、GRU 更新 | [`GGNN`](../model/ggnn.py) | 每种关系有独立线性变换，重复 `steps` 次 |
| §3.3，式 (7)-(9)，第 4 页 | 行级全局 Transformer | [`LineTransformer`](../model/line_transformer.py) | 有 padding mask；未实现论文文字描述的显式位置编码 |
| §3.4，式 (10)-(11)，第 5 页 | 行级漏洞分类 | [`LineClassifier`](../model/classification_heads.py) | 当前为两层 MLP 加 Sigmoid，论文式 (11) 写为单层线性分类 |
| §3.4，式 (12)-(14)，第 5 页 | 注意力池化与文件分类 | [`AttentionPooling` / `FileClassifier`](../model/classification_heads.py) | 对有效行做 softmax 加权求和，输出文件漏洞概率 |
| §3.4，式 (15)，第 5 页 | CWE 多标签分类 | [`CWEClassifier`](../model/classification_heads.py) | Sigmoid 输出；仍缺 CWE ID 到训练类别的映射 |
| §3.4，式 (16)，第 5 页 | 联合训练目标 | [`MultiTaskLoss`](../model/multitask_loss.py) | 三项 BCE 加权；行级额外应用正例权重与 mask |

原代码注释中的部分公式编号对应旧稿，例如 Transformer 注释写作 Eq.(6)、总损失写作 Eq.(13)。阅读本次 PDF 时应以上表为准。

## 实验协议

论文 §4.2（第 5-6 页）报告：

- 使用 Juliet 合成数据训练，依据 `bad` 函数内的 flaw 标记构建行级标签，并过滤有歧义的样本。
- 采用函数级哈希去重和基于 AST 的相似性过滤。现有脚本未实现这两个步骤。
- 训练/验证/测试比例为 80%/10%/10%，随机种子 42。
- PyTorch、NVIDIA V100、CodeBERT、Joern、Adam；学习率 `2e-5`、batch size `16`、3 层 GNN、4 层 Transformer；依据验证性能早停。
- Juliet 训练的模型直接在 Big-Vul 上测试，不进行微调。Big-Vul 的 Top-k 定位目标由修复补丁中删除或修改的行构成；这是代理目标，不是完整人工行级真值。

稿件未提供完整软件版本、Joern 版本、全部超参数和可下载的训练权重，不能仅凭本文档恢复一个已锁定的复现实验环境。

## 报告结果

下表均转录自论文，未通过当前仓库重跑。除 MCC 外，数值单位均为百分比。

### Juliet 行级定位：Table 2，第 7 页

| 方法 | Precision | Recall | F1 | Top-10 Recall |
| --- | --- | --- | --- | --- |
| CodeBERT (Attr.) | 58.4 | 62.1 | 60.2 | 65.3 |
| GraphCodeBERT | 74.2 | 71.5 | 72.8 | 76.9 |
| LineVul | 76.5 | 74.8 | 75.6 | 79.2 |
| LineVD | 77.2 | 75.6 | 76.4 | 80.6 |
| MatsVD | 78.4 | 76.9 | 77.6 | 82.1 |
| **CodeExplorer** | **79.8** | **78.3** | **79.0** | **83.4** |

### Juliet 文件检测：Table 3，第 7 页

| 方法 | Accuracy | F1 | MCC |
| --- | --- | --- | --- |
| DeepWukong | 84.0 | 82.9 | 0.680 |
| GraphCodeBERT | 85.2 | 84.4 | 0.704 |
| LineVul | 86.1 | 85.3 | 0.721 |
| **CodeExplorer** | **87.4** | **86.8** | **0.749** |

### 消融摘录：Tables 4-6，第 8-9 页

| 对照设置 | 行级 F1 | Top-10 Recall | 来源 |
| --- | --- | --- | --- |
| 不使用结构（无 GNN） | 74.8 | 78.1 | Table 4 |
| 仅 CFG | 76.0 | 80.0 | Table 4 |
| 仅 DFG | 77.4 | 81.6 | Table 4 |
| 局部 GNN，无全局上下文 | 76.2 | 78.5 | Table 5 |
| BiLSTM 上下文 | 76.5 | 80.1 | Table 5 |
| 仅行级监督 | 76.5 | 79.1 | Table 6 |
| 行级 + 文件级监督 | 77.8 | 81.4 | Table 6 |
| 行级 + CWE 监督 | 77.4 | 80.8 | Table 6 |
| **完整模型** | **79.0** | **83.4** | Tables 4-6 |

当前消融开关只部分覆盖这些设置，不能直接执行全部表格实验。CFG-only、DFG-only、BiLSTM 对照和各监督组合仍需独立实现或配置。

### Juliet → Big-Vul：Table 8，第 11 页

| 方法 | Accuracy | 文件 F1 | Top-5 Recall | Top-10 Recall |
| --- | --- | --- | --- | --- |
| CodeBERT (Attr.) | 51.4 | 48.7 | 32.5 | 40.8 |
| GraphCodeBERT | 56.8 | 53.2 | 38.1 | 45.6 |
| LineVul | 58.2 | 54.5 | 39.4 | 47.2 |
| LineVD | 59.1 | 55.6 | 40.7 | 48.3 |
| MatsVD | 60.4 | 56.7 | 41.8 | 49.5 |
| DeepWukong | 55.3 | 51.9 | 不适用 | 不适用 |
| **CodeExplorer** | **62.5** | **59.8** | **43.6** | **51.7** |

## 对齐实现时应注意

| 差异 | 当前情况 | 影响 |
| --- | --- | --- |
| 默认 batch size | 配置为 8，论文为 16 | 实验设置不同 |
| CWE 任务 | `lambda_cwe=0`，`use_multitask` 未控制预测头或损失 | 默认并非完整三任务设置 |
| 关闭多任务的消融 | `no_multitask` 仅设置布尔值 | 文件损失权重仍为 1，不能代表仅行级监督 |
| 位置编码 | 行级 Transformer 未显式添加 | 与论文 §3.3 描述不完全一致 |
| 早停 | 定义了 patience，训练循环未使用 | 训练行为与论文描述不同 |
| 训练指标 | 当前返回行级 P/R/F1/AUC、文件 AUC/ACC 和 CWE macro-F1 | 尚缺论文 Top-5/10、文件 F1/MCC、CWE micro-F1 |
| 数据处理 | 仅扫描 `.c`，仅输出找到漏洞的文件，无去重 | 不能直接构成论文中的完整数据协议 |

这些属于已有研究实现的缺口。本次整理只调整目录、必要导入和预处理路径接口，未以文档替代这些实现工作。
