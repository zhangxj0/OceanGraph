# OceanGraph-R1 复现指南

本文档用于复现当前已验证的纯文本多跳问答数据生成流程。推荐路由为：

- `Qwen3.7-Plus`：语料分析、检索规划、问答生成与失败样本修正。
- `DeepSeek-V4-Pro`：答案验证、合并式多跳必要性验证与可选质量评估；候选模型选择默认关闭。
- `BAAI/bge-m3`：本地文本向量嵌入与评估向量。
- `BAAI/bge-large-en-v1.5`：本地文本重排。

整个数据生成流程为纯文本模式，不会向模型 API 发送图片。代码中部分历史函数名仍包含 `VLM`，但在
`pipeline.modality: text` 下只传递文本内容，预检和运行日志中的 `Has image` 应为 `False`。

## 1. 已验证环境

完整流程于 2026-07-15 在以下环境验证：

- Ubuntu 22.04，Python `3.12.3`
- NVIDIA RTX 4090 24 GB，驱动 `550.54.14`
- Torch `2.7.0a0+7c8ec84dab.nv25.3`
- Transformers `4.49.0`
- Sentence Transformers `3.4.1`
- FAISS CPU `1.10.0`

`requirements.txt` 记录了服务器实际可运行环境的确切版本。TXT/Markdown 小规模复现建议使用
16 GB 以上显存；单元测试可在 CPU 环境运行。

## 2. 获取代码并安装

```bash
git clone https://github.com/zhangxj0/OceanGraph.git
cd OceanGraph
git checkout v3.0.0
```

在已包含指定 NVIDIA Torch 构建的 Paratera 镜像中安装：

```bash
python -m pip install -r requirements.txt
python -m pip install -e . --no-deps
```

`torch==2.7.0a0+7c8ec84dab.nv25.3` 是 Paratera NVIDIA PyTorch 镜像提供的定制构建，通常不能从
PyPI 重新下载。迁移时应优先复用同一镜像；若使用其他 CUDA 镜像，请先安装与其匹配的 PyTorch，
再按照 `requirements.txt` 安装其余包，并记录实际 Torch/CUDA 版本。

安装后执行本地回归检查：

```bash
python -m compileall -q src scripts tests run_oceangraph.py
python -m pytest -q
python run_oceangraph.py --help
```

测试数量会随回归覆盖增加；以命令退出码为准，所有测试均应通过。

## 3. 配置模型路由

复制推荐配置，生成的 `config.yaml` 已被 Git 忽略：

```bash
cp configs/oceangraph.yaml.example config.yaml
```

只通过环境变量提供密钥，禁止将密钥写入 YAML、脚本、日志或 Git：

```bash
export OPENAI_API_KEY="YOUR_PARATERA_KEY"
```

PowerShell：

```powershell
Copy-Item configs/oceangraph.yaml.example config.yaml
$env:OPENAI_API_KEY = "YOUR_PARATERA_KEY"
```

推荐配置固定了以下关键行为：

- `generation` 与 `correction` 路由到 Qwen。
- `selection` 与 `verification` 路由到 DeepSeek，但推荐配置默认关闭冗余的候选模型选择。
- 两个 profile 通过 Paratera 的 OpenAI 兼容端点调用，共用环境变量
  `OPENAI_API_KEY`，YAML 中不保存密钥。
- 两个 profile 的 `max_output_tokens` 均为 4096，并显式关闭 thinking；
  HTTP 200 但正文为空的响应会触发重试，不会写入缓存。
- `default`、`corpus` 与 `retrieval` 路由到 Qwen，避免意外访问 OpenAI 默认地址。
- `pipeline.modality: text` 禁止图片进入模型调用。
- `evaluation.run_evaluation: false` 默认不启动额外评估，先保证数据生成完成。
- `multihop_verification_mode: balanced` 将逐块判断合并为一次调用，并优先检查生成记录声明的证据块。
- `counterfactual_verification: false` 默认不执行逐块 leave-one-out 消融；正式发布前可对抽样子集启用严格审计。

### 推荐审查档位

大规模生成使用以下配置：

```yaml
qa_generation:
  strict_multihop_verification: true
  min_supporting_chunks: 2
  model_selection: false
  multihop_verification_mode: balanced
  max_verification_chunks: 4
  max_unknown_verdicts: 1
  counterfactual_verification: false
```

该档位仍拒绝任何被审查证据块可单独完整回答的捷径样本，但允许无关背景块为
`CANNOT_ANSWER`，并允许一次无法解析的逐块判断。每个进入最终审查的候选固定使用两次
DeepSeek 请求：一次完整 QA 正确性检查和一次合并式多跳检查。旧默认对 `N` 个上下文块需要
`2 + 2N` 次请求；`N=4` 时由 10 次降为 2 次。

只在小规模质量审计或论文报告抽样时使用严格档位：

```yaml
qa_generation:
  model_selection: true
  multihop_verification_mode: strict
  max_unknown_verdicts: 0
  counterfactual_verification: true
```

命令行也可显式启用严格审计：

```bash
python run_oceangraph.py \
  --config config.yaml \
  --multihop-verification-mode strict \
  --model-selection \
  --counterfactual-verification
```

## 4. 准备最小语料

建议准备至少 3 个相互关联的 TXT 或 Markdown 文档，每个目标问题应需要至少两个不同文本块。

```bash
mkdir -p data/repro_ocean
cp /path/to/ocean/files/*.txt data/repro_ocean/
cp /path/to/ocean/files/*.md data/repro_ocean/
```

首次联网运行会下载 BGE-M3 和 BGE-large。也可以提前缓存：

```bash
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('BAAI/bge-m3'); SentenceTransformer('BAAI/bge-large-en-v1.5')"
```

模型缓存完成后，隔离服务器运行时增加 `--offline-models`，避免 Hugging Face 网络探测。

## 5. 先运行预检

必须显式传入配置文件，确保 Qwen/DeepSeek 路由生效：

```bash
python run_oceangraph.py --config config.yaml --backend openai --preflight
```

预检应确认：

- generation 模型为 `Qwen3.7-Plus`；
- verification 模型为 `DeepSeek-V4-Pro`；
- 两个 API 均可调用；
- BGE-M3 与文本重排模型可加载；
- 纯文本模式生效。

预检失败时命令退出码为非零。`preflight.check_timeout_seconds` 默认将每个昂贵检查的等待时间限制为
180 秒；当 `evaluation.run_evaluation: false` 时，不加载仅供评估使用的 embedding。模型连通性探测
会写入输出目录的追加式 LLM cache；相同模型路由可在默认 3600 秒 TTL 内复用，超过 TTL 后重新检查
当前密钥和服务连通性。

若 DeepSeek 返回 HTTP `402 Insufficient Balance`，应先充值或更换有余额的密钥。此错误属于服务端
账户状态，不是 OceanGraph 代码故障。

### 归一化海洋语料配置

对于 `data/normalized` 下的 NOAA、NASA 和 Argo Markdown，仓库提供了
`configs/normalized_corpus.yaml.example`。该配置使用 8000 字符窗口、800
字符重叠、全量文件处理和离线 BGE 模型。输入发现支持递归，因此 ZIP 解压后
出现双层 `normalized/normalized` 时无需修改源码。

```bash
python run_oceangraph.py \
  --config configs/normalized_corpus.yaml.example \
  --backend openai \
  --input data/normalized \
  --output output/normalized_dataset \
  --num-qa-pairs 80 \
  --max-depth 2 \
  --max-workers 4 \
  --offline-models
```

## 6. 生成两条完整样本

第一次建议只生成两条，并把并发设为 1，便于定位 API 限流或余额问题：

```bash
python run_oceangraph.py \
  --config config.yaml \
  --backend openai \
  --input data/repro_ocean \
  --output output/repro_qwen_deepseek \
  --num-qa-pairs 2 \
  --max-workers 1 \
  --embedding-model bge_m3 \
  --reranker-model text_embedding \
  --max-depth 2 \
  --min-supporting-chunks 2 \
  --deduplication \
  --offline-models
```

若本地尚无模型缓存，首次运行去掉 `--offline-models`。生成和严格验证成功后，再按需增加
`--num-qa-pairs` 与 `--max-workers`。

v3.0.0 的语义指纹不会把目标数量、worker 数或输出路径作为数据身份；因此可直接复用上述
输出目录从 2 条继续扩展到正式规模。预检成功前不会固化新的运行清单。

## 7. 验收生成结果

重点检查 `output/repro_qwen_deepseek/`：

- `qa_multihop_pass.json` 与 `qa_multihop_pass.jsonl`：通过严格验证的样本。
- `qa_multihop_fail.json` 与 `qa_multihop_fail.jsonl`：拒绝样本及原因。
- `qa_deduplicated.json`：去重后的最终数据。
- `chunks.json`：检索语料块。
- `chunks_with_complete_context.json`：补全上下文后的语料块。
- `oceangraph_run_config.json`：本次运行参数快照，不包含 API 密钥。
- `training/train.jsonl`、`training/dev.jsonl`、`training/test.jsonl`：按源文档连通组划分的训练数据。
- `training/manifest.json`：划分数量与 `source_leakage_detected` 审计结果。

正式训练前确认 `training/manifest.json` 中 `source_leakage_detected` 为 `false` 且
`split_viable` 为 `true`。共享任一 supporting source document 的 QA 会被固定分配到同一 split，
避免同源内容同时进入训练集和测试集；小规模试跑产生空 dev/test 时只用于管线验收，不能直接训练。

一条合格样本至少满足：

1. `multihop_necessity_result.passes` 为 `true`。
2. `balanced` 模式下 `supporting_chunks` 至少包含两个不同文本块；`strict` 反事实模式下检查 `necessary_chunks`。
3. 不存在能够单独回答问题的 `shortcut_chunks`。
4. `supporting_facts`、`evidence_spans`、`reasoning_path` 与 `sub_questions` 均存在。
5. 最终答案中没有“等等”“重新计算”等可见自我修正草稿。
6. 输出、配置和日志中均不包含 API 密钥。

推荐配置下还应看到：

- `multihop_necessity_result.method == "consolidated_single_pass"`；
- `multihop_necessity_result.verification_api_calls == 1`；
- `multihop_necessity_result.checked_chunk_count <= 4`。

## 8. 可选完整评估

确认 DeepSeek 余额充足后，可在生成命令末尾增加 `--evaluation`。评估会继续使用 DeepSeek 验证
路由作为裁判，并使用本地 BGE-M3 计算向量指标，不调用 Gemini、RAGAS 或 LangChain。

若样本已生成，但评估因 402 或网络中断失败，无需重新生成数据。可单独续跑：

```bash
OCEANGRAPH_CONFIG=config.yaml python -m oceangraph.evaluation.metrics \
  output/repro_qwen_deepseek/qa_deduplicated.json \
  --corpus output/repro_qwen_deepseek/chunks.json \
  --output-dir output/repro_qwen_deepseek/evaluation \
  --no-multimodal
```

PowerShell：

```powershell
$env:OCEANGRAPH_CONFIG = "config.yaml"
python -m oceangraph.evaluation.metrics `
  output/repro_qwen_deepseek/qa_deduplicated.json `
  --corpus output/repro_qwen_deepseek/chunks.json `
  --output-dir output/repro_qwen_deepseek/evaluation `
  --no-multimodal
```

评估结果写入 `evaluation/subset_evaluation_report.json`。

## 9. 导出 Search-R1 格式

Search-R1/RL 训练本身尚未包含在当前已验证范围内；项目只提供数据转换入口：

```bash
python scripts/oceangraph_to_search_r1.py \
  --qa-file output/repro_qwen_deepseek/qa_deduplicated.json \
  --chunks-file output/repro_qwen_deepseek/chunks.json \
  --output-dir output/repro_qwen_deepseek/search_r1 \
  --short-answer-mode heuristic \
  --no-parquet
```

检查 `conversion_summary.json` 中 `converted > 0`，并确认生成 `train.jsonl`、`corpus.jsonl` 和
`oceangraph_2wiki_like.jsonl`。

## 10. 已验证结果与限制

- 本地与服务器都应运行完整 `pytest -q`；不要使用历史测试数量作为版本验收条件。
- 两条样本的生成、自动修正、DeepSeek 严格多跳验证和去重流程已跑通。
- 一次完整两样本评估成功；后续最新复测在最终评估阶段因 DeepSeek 账户余额不足返回 402，但此前
  的生成与严格验证均已成功，且评估可按第 8 节独立续跑。
- 远程模型即使温度为 `0.0` 也不保证逐 token 完全一致，因此复现标准是 schema、证据必要性、
  严格多跳通过率和输出文件完整性，而不是文本逐字一致。
- FAISS CPU 的 AVX2 提示或 GPU FAISS 回退提示通常不影响正确性；当前验证环境使用
  `faiss-cpu==1.10.0`。

为每次正式实验记录 Git commit、语料校验和、模型 ID、API endpoint、随机种子、接受/拒绝数量、
token 用量和评估报告，才能进行可审计的横向比较。
