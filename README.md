# OceanGraph-R1 v4.0.0

海洋科学多跳问答数据生成框架。将文献正文转换为问题、简短标准答案、来源语料及训练集，供检索增强推理和 Search-R1 类训练流程使用。**本项目生成数据，不执行强化学习训练。**

v4.0.0 的重点是：**普通流水线和可断点续跑的批量程序，共用一份 `configs/llm.yaml`。** 生成模型、验证模型、接口地址和推理参数都可以通过配置切换。

版本：`4.0.0` · 更新：`2026-10-21` · Python：`>=3.9` · License：Apache-2.0

## 1. 两种运行方式

| 入口 | 适用情况 | 数据处理和核验 |
|---|---|---|
| `run_oceangraph.py` / `oceangraph` | PDF、HTML、TXT、Markdown，需检索、嵌入和上下文构建 | Corpus → Evidence → QA → Verifier；可选择严格或实用多跳模式 |
| `python -m oceangraph.batch.prepare` + `python -m oceangraph.batch.run` | 已整理好的海洋科学 Markdown，大批量生成短答案 QA | 本地正文筛选 → 生成 → 本地规则 → 模型核验 → SQLite → 训练导出 |

批量入口只使用 **OpenAI-compatible Chat Completions**，目前需要 Linux/macOS 的进程锁支持；可在 Windows 上配置和使用普通流水线，在 Linux 服务器上执行批量任务。批量正文筛选不需要 GPU、向量库或嵌入模型。

## 2. 安装

```bash
git clone --branch v4.0.0 https://github.com/zhangxj0/OceanGraph.git
cd OceanGraph
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

只使用批量文本入口时，可在干净环境安装其最小依赖，避免安装完整的嵌入/PDF 工具链：

```bash
python -m pip install requests pyyaml pydantic
python -m pip install -e . --no-deps
```

后续切换到普通检索流水线时需安装完整依赖。`--offline-models` 仅控制本地嵌入模型加载；远程生成/验证 API 仍需网络并产生相应费用。

## 3. 只改一个文件切换模型

编辑 `configs/llm.yaml` 中的 `models.profiles`：

- `generator`：文献分析、检索辅助和 QA 生成。
- `verifier`：候选筛选和最终验证。
- `models.stages`：将逻辑阶段映射到上述配置。两个角色可以使用不同模型、不同服务商，也可以共用一个模型。

仓库默认配置保留 **Paratera GLM-5.3 low 生成 / GLM-5.3 high 验证**，便于兼容此前流程。它属于同模型角色分离，不能称为异模型独立验证。

### 示例：GLM 生成 + DeepSeek 验证

将两个 profile 改为以下内容，其余阶段映射保持原样：

```yaml
models:
  profiles:
    generator:
      backend: OPENAI
      model: GLM-5.3
      base_url: https://llmapi.paratera.com/v1
      api_key_env: OPENAI_API_KEY
      supports_vision: false
      temperature: null
      structured_output: true
      max_output_tokens: 8192
      timeout: 180
      extra_body:
        thinking:
          type: enabled
        reasoning_effort: low

    verifier:
      backend: OPENAI
      model: deepseek-flash
      base_url: https://api.deepseek.com
      api_key_env: DEEPSEEK_API_KEY
      supports_vision: false
      temperature: null
      structured_output: true
      max_output_tokens: 8192
      timeout: 180
      extra_body:
        thinking:
          type: enabled
        reasoning_effort: high

  stages:
    default: generator
    corpus: generator
    retrieval: generator
    generation: generator
    selection: verifier
    verification: verifier
    correction: generator
```

也可以从 `configs/llm.glm-deepseek.yaml.example` 复制完整示例。截止 2026-10-20，DeepSeek 官方 `deepseek-flash` 对应 `DeepSeek-V4.1-Flash-1017`；这是可更新的服务别名。第三方平台的 ID、版本映射、参数支持和价格应以该平台为准，不能直接假定也叫 `deepseek-flash`。

| 字段 | 含义 |
|---|---|
| `model` | 当前服务商实际支持的模型 ID；不会自动改写大小写或型号 |
| `base_url` | API 基础地址，如 `https://example.com/v1`；自动补 `/chat/completions` |
| `url` | 兼容旧版的完整请求地址，如 `https://example.com/v1/chat/completions` |
| `api_key_env` | 保存密钥的环境变量名称；不填写密钥本身 |
| `extra_body` | 服务商专用参数，按原样放在请求 JSON 顶层 |
| `max_output_tokens` | 请求输出上限；批量入口另有 8192 的硬上限，取较小值 |
| `timeout` | 超时秒数；批量入口读取超时最多 180 秒，连接超时 20 秒 |

`url` 与 `base_url` **只选一个**。已有完整 URL 可以原样保留。`base_url` 不会猜测或补齐 `/v1`，请填写服务商文档指定的前缀。这里的 `backend: OPENAI` 表示接口协议，并不表示必须使用 OpenAI 的模型。

如果两个模型都走 Paratera：把两者地址设为同一个 Paratera 地址，`api_key_env` 可共用 `OPENAI_API_KEY`，分别填写该平台的模型 ID 即可。

切换到 Qwen 等模型时，同时调整 `extra_body`。例如，支持该参数的 Qwen 接口可使用 `enable_thinking: false`；不要直接沿用另一服务商的思考参数。GLM-5.3 需要开启推理，可选 low/high/max。配置检查能检查字段和密钥是否齐全，不能证明远程服务接受模型 ID 或全部参数。

### 配置密钥

```bash
# Linux / macOS：在执行任务的服务器 shell 中设置
export OPENAI_API_KEY="YOUR_PARATERA_KEY"
export DEEPSEEK_API_KEY="YOUR_DEEPSEEK_KEY"
```

```powershell
# Windows PowerShell
$env:OPENAI_API_KEY = "YOUR_PARATERA_KEY"
$env:DEEPSEEK_API_KEY = "YOUR_DEEPSEEK_KEY"
```

每个角色只读取自己指定的变量。缺少验证模型的密钥时，不会借用生成模型的密钥。v4 批量程序不从 Markdown 测试笔记中提取密钥。

### 生效时间与配置优先级

配置在进程启动时读取。编辑文件后，对**下一次启动/续跑**生效，正在运行的请求不会热切换。

- 普通流水线：`OCEANGRAPH_LLM_CONFIG` 优先于主配置的 `llm_config_file`。主配置示例已经指向 `configs/llm.yaml`。
- 批量入口：`--llm-config` > `OCEANGRAPH_LLM_CONFIG` > 当前目录的 `configs/llm.yaml`。
- 批量运行把实际生效的路由保存到 `run_config.json` 和追加式 `config_history/`，密钥值不写入其中。

## 4. 批量生成：先检查，再试跑，再扩大

以下命令从仓库根目录执行。`--check-config` 只读取配置与环境变量，不调用 API、不创建任务数据库：

```bash
python -m oceangraph.batch.run --llm-config configs/llm.yaml --check-config
```

### 第一步：准备正文，零模型调用

```bash
python -m oceangraph.batch.prepare \
  --input data/data1 \
  --pattern 'ocean_corpus_*.md' \
  --output output/my_20k
```

每个 Markdown 应有 YAML front matter，至少提供 `title`，建议提供 `doi` / `doi_or_report_id` 和 `source_url`，后接正文：

```markdown
---
title: Marine nutrient cycling in a coastal ecosystem
doi: 10.example/replace-with-real-doi
source_url: https://example.org/replace-with-real-source
---
## Abstract
真实文献正文……
## Results
真实结果……
## Discussion
真实讨论……
```

默认只匹配输入目录的 `*.md`；递归处理可设 `--pattern '**/*.md'`。筛选器要求足够长度的海洋正文，优先抽取摘要、结果和讨论，每篇最多 5 个正文窗口、约 10,500 字符；不是全文覆盖保证。标题、DOI、选取内容用于去重，候选按 8 个主题轮换。空目录会报错；已有 inventory/数据库的输出目录不会被覆盖。

可选 `--exclude exclusions.json`，格式为 `{"source_documents": ["文档相对路径去扩展名"], "questions": ["已有问题"]}`。准备阶段排除来源；运行阶段也传入 `--exclude` 才会导入问题排除列表。不会自动发现或排除你以前生成的 50 条。

### 第二步：20 篇先导批次

```bash
python -m oceangraph.batch.run \
  --output output/my_20k --target 20000 \
  --llm-config configs/llm.yaml --workers 4 --max-documents 20
```

`--max-documents 20` 是本次处理来源数的上限，最终 QA 条数由生成和验证结果决定。先查看 `qa_partial.jsonl`、`dataset_summary.json` 与训练导出，再继续：

```bash
python -m oceangraph.batch.run \
  --output output/my_20k --target 20000 \
  --llm-config configs/llm.yaml --workers 8
```

同一输出目录自动续跑；先导的已收录样例及全部请求用量继续累计。已有任务的 `--target` 不允许更改。来源不足、达到预算或收到 STOP 都可能导致少于目标数量，**目标 20,000 不表示一定能收满 20,000**。

### 停止与模型切换

```bash
touch output/my_20k/STOP
```

等待 `progress.json` 显示停止状态和进程退出，再编辑模型配置。主动恢复时移除自己创建的 STOP 文件，并运行同一续跑命令：

```bash
rm output/my_20k/STOP
python -m oceangraph.batch.run --output output/my_20k --target 20000
```

切换后只影响新请求。旧样本不会自动被新模型重新验证；每条新样本带有生成/验证路由信息。不要通过重建输出目录来伪装续跑或重置已有用量。

### 累计预算与质量限制

| 限制 | 当前批量默认硬上限 |
|---|---:|
| 请求次数 | 40,000，含重试、生成和验证 |
| 输入 token | 200,000,000 |
| 输出 token | 50,000,000 |
| 单次输出 | 8,192，或配置中的更小值 |
| 累计活动时间 | 24 小时，断点继续累计 |
| 并发 | 最多 8 |
| 每来源收录 | 最多 4 条 |
| 数值聚合题 | 不超过目标数量的 35% |

每次调用前保守预留预算；服务商返回可信 usage 后结算，失败/未知用量保留预留。实际服务商报告量可能与预估不同，这些是本地请求准入限制，不是人民币金额保证。绝对运行时间 watchdog 与进程锁保护任务。达到运行时间上限留下 `runtime_limit_reached`，续跑不会自动延长总时间。

来源首次耗尽仍不足目标时，只对已产出 1–3 条样例的来源额外生成一轮，传入已有问题避免复述。跨来源进行标准化精确去重，同来源再做字符串近似去重；不宣称语义重复已全部消除。

## 5. 输出和进度怎么看

| 文件 | 内容与更新时间 |
|---|---|
| `sources.jsonl` / `source_inventory.json` | 准备阶段的来源和筛选统计 |
| `run.sqlite` | 实时样例、来源状态、拒绝记录、请求及 token 台账 |
| `progress.json` | 约每 5 秒更新进度和状态 |
| `qa_partial.jsonl` | 每新增约 500 条以及阶段停止时更新的样例快照 |
| `qa_20000.jsonl` | 达到目标时导出的完整 QA；为兼容旧任务保留此文件名，即使目标不是 20,000 |
| `training/train.jsonl`、`dev.jsonl`、`test.jsonl` | 按来源分组的训练划分 |
| `training/corpus.jsonl` / `manifest.json` | 检索语料、数量和来源划分检查 |
| `search_r1/{train,dev,test}.jsonl` | prompt / reward_model 格式参考导出 |
| `run_config.json` / `config_history/` | 本次有效配置及历次启动配置 |

训练和 Search-R1 文件在先导结束、完整完成或显式导出时更新；运行中可能仍是先导快照。以 `progress.json` 和数据库中的实际计数判断进度，不凭文件名判断完成。

进程退出后，可不调用模型重新导出当前已收录数据：

```bash
python -m oceangraph.batch.run --output output/my_20k --target 20000 --export-only
```

显式导出也使用兼容文件名 `qa_20000.jsonl`，请以 `dataset_summary.json` 的 `accepted` 和 `completed` 判断是否完整。导出前会重检已知本地违规规则，可能剔除旧样例；已花费的 API 用量不退回。

请求的配置模型、端点和参数保存在 SQLite `call_routes`；样本 `model_provenance` 及训练 metadata 保存生成/验证配置。服务别名可能被供应商更新，配置记录不等同于权重快照证明。旧断点里无记录的样例标为 `legacy_unrecorded`，不补造模型来源。

Search-R1 JSONL 是接入参考，需要按具体训练代码转换成 Parquet、构建检索索引并核对 reward 格式；不是已经执行过的 RL 训练结果。

## 6. 普通流水线与多跳标准

```bash
cp configs/oceangraph.yaml.example config.yaml
python run_oceangraph.py \
  --config config.yaml --input data/ocean_texts \
  --output output/pipeline_demo --backend openai \
  --num-qa-pairs 20 --embedding-model bge_m3 \
  --reranker-model text_embedding
```

本地已缓存嵌入模型时可加 `--offline-models`。五个海洋领域：物理海洋与气候、碳与生物地球化学、遥感与观测、生态与渔业、海岸灾害与人类系统。

普通模板保留 `cost_efficient` 多片段核验。若采用本版本的实用多跳目标，在主配置设置：

```yaml
qa_generation:
  type: multihop
  verification_profile: practical_multihop
  strict_multihop_verification: false
  model_selection: false
  counterfactual_verification: false
```

批量入口固定使用实用多跳模式，不读取主配置中的核验策略：

- 问题组合相关事实，回答一个最终未知量，答案通常不超过 12 个英文词。
- 原文支持、独立可理解、单一目标、领域相关和多跳合理性都必须明确通过；批量入口额外核对实验条件及算术。
- 允许同一文献、同一段落内的相邻事实组合，不要求证据图、跨文献或逐跳不可替代性证明。
- 排除装饰性长前提加单事实查询、把全部计算输入直接写进问题、偏题及复合问题。
- 模型核验不等于人工金标准；样本明确标记 `necessity_verified: false`，应做分层人工抽检。

包版本为 4.0.0；既有 taxonomy 和四代理架构 schema 仍保留 3.0.0，避免把软件版本升级误当成数据定义改变。

## 7. 从旧服务器脚本迁移

旧 `tmp/.../run_batch.py` 是独立脚本，模型写在代码中。它不会因为你修改仓库配置而自动变成 v4 程序。

1. 让旧进程正常完成，或通过其 STOP 文件停止并确认退出。
2. 备份整个旧输出目录，包括 SQLite 的 WAL/SHM（最好在进程退出后备份）。
3. 在 v4 环境设置密钥；不要依赖旧测试笔记里的密钥回退。
4. 用 v4 的 `--check-config` 检查配置，然后把 `--output` 指向旧目录、保持原目标续跑。
5. 已有样例与预算保留；新请求增加路由记录。需要全量异模型补验时，应单独制定补验任务，本入口不会自动补验。

发布分支不会替换正在执行的旧脚本，也不会自动启动新的收费任务。

## 8. 开发验证与版本记录

```bash
python -m pip install pytest build twine
python -m pytest -q
python -m build
python -m twine check dist/*
```

测试使用本地规则、固定样例和模拟 HTTP 返回，不要求真实模型密钥。模型能力说明与接口参数可查 [GLM 文档](https://docs.z.ai/guides/llm/glm-5.3)、[DeepSeek 更新日志](https://api-docs.deepseek.com/updates/)；第三方转发平台需要另外核对兼容性。

更多历史架构与复现实验见 [OCEANGRAPH_FRAMEWORK.md](OCEANGRAPH_FRAMEWORK.md)、[REPRODUCIBILITY.md](REPRODUCIBILITY.md)。这些文件记录旧版本流程；v4 的配置与批量入口以本 README 为准。版本变化见 [CHANGELOG.md](CHANGELOG.md)。
