# OceanGraph-R1 Five-Domain Dataset Plan

This project version targets a high-quality multi-hop ocean science QA dataset.
Each sample should keep long answers for audit,
short answers for EM/F1 reward, evidence spans for verification, evidence graphs
for reasoning supervision, and retrieval traces for quality analysis.

## Five Dataset Domains

| # | Domain | Default Input Directory | Recommended Share | Main Question Types |
|---|---|---|---:|---|
| 1 | Physical Oceanography and Climate Dynamics | `data/ocean_physical_climate` | 22% | causal, temporal, spatial, comparison |
| 2 | Ocean Carbon Cycle and Marine Biogeochemistry | `data/ocean_carbon_biogeochemistry` | 24% | bridge, causal, mechanism, numeric |
| 3 | Ocean Remote Sensing and Observing Systems | `data/ocean_remote_sensing_observing` | 18% | variable-to-instrument, comparison, retrieval |
| 4 | Marine Ecology, Ecosystems, and Fisheries | `data/ocean_marine_ecology_fisheries` | 20% | ecosystem response, bridge, causal |
| 5 | Coastal Hazards and Human Impacts | `data/ocean_coastal_hazards_human` | 16% | risk chain, spatial, policy evidence |

## Domain Details

### 1. Physical Oceanography and Climate Dynamics

Coverage:
- currents, overturning, stratification, mixed layer, eddies
- sea level, ocean heat content, air-sea fluxes
- ENSO, marine heatwaves, monsoon/ocean coupling, polar amplification

Good sources:
- NOAA climate/ocean explainers and technical reports
- IPCC ocean and cryosphere chapters
- Argo and ocean heat content documentation
- regional circulation and marine heatwave papers

### 2. Ocean Carbon Cycle and Marine Biogeochemistry

Coverage:
- biological pump, solubility pump, overturning carbon storage
- ocean acidification, alkalinity, pH, carbonate chemistry
- nutrients, dissolved oxygen, hypoxia, remineralization

Good sources:
- NOAA ocean acidification and deoxygenation material
- NASA/NOAA carbon cycle reports
- Biogeochemical Argo documentation
- peer-reviewed biological pump and carbon sequestration papers

### 3. Ocean Remote Sensing and Observing Systems

Coverage:
- SST, SSH, ocean color, chlorophyll, SSS, winds, waves
- Argo floats, buoys, drifters, gliders, moorings, satellite sensors
- validation, uncertainty, variable-to-instrument mapping

Good sources:
- NASA Earthdata and Ocean Color documentation
- NOAA CoastWatch product guides
- GOOS Essential Ocean Variables pages
- Argo, drifter, glider, and buoy technical documents

### 4. Marine Ecology, Ecosystems, and Fisheries

Coverage:
- primary productivity, phytoplankton blooms, harmful algal blooms
- coral bleaching, food webs, fisheries habitat
- ecosystem indicators and biological response to physical/chemical drivers

Good sources:
- NOAA fisheries ecosystem reports
- coral bleaching and marine heatwave reports
- regional ecosystem status reports
- peer-reviewed plankton, habitat, and food-web papers

### 5. Coastal Hazards and Human Impacts

Coverage:
- storm surge, coastal flooding, shoreline change
- eutrophication, hypoxia, harmful algal blooms
- pollution, marine debris, coastal management and resilience

Good sources:
- NOAA storm surge and coastal hazard reports
- harmful algal bloom and hypoxia reports
- coastal pollution and marine debris reports
- regional coastal resilience or management documents

## Quick Start

Set an API key first. For DeepSeek through the OpenAI-compatible backend:

```bash
export OPENAI_API_KEY="your-api-key"
export HF_ENDPOINT="https://hf-mirror.com"  # optional, useful in China
```

Put source documents into one of the default input directories, then run:

```bash
python scripts/run_01_physical_ocean_climate.py
python scripts/run_02_carbon_biogeochemistry.py
python scripts/run_03_remote_sensing_observing.py
python scripts/run_04_marine_ecology_fisheries.py
python scripts/run_05_coastal_hazards_human.py
```

Each script writes OceanGraph output to:
- `output/oceangraph_<domain>/`

## Common Overrides

Generate a small smoke-test set:

```bash
python scripts/run_02_carbon_biogeochemistry.py --num-qa-pairs 20 --relaxed
```

Use a custom input directory:

```bash
python scripts/run_03_remote_sensing_observing.py --input /data/ocean_remote_docs
```

Use OpenAI instead of DeepSeek:

```bash
python scripts/run_01_physical_ocean_climate.py \
  --api-url https://api.openai.com/v1/chat/completions \
  --llm-model gpt-4o-mini \
  --vlm-model gpt-4o
```

Use local Ollama:

```bash
python scripts/run_05_coastal_hazards_human.py \
  --backend ollama \
  --llm-model llama3.1:8b \
  --vlm-model llava:13b
```

## Recommended Paper-Scale Run

For a first paper-quality dataset, target roughly 20k-50k accepted QA pairs:

| Domain | Suggested Accepted QA Target |
|---|---:|
| Physical Oceanography and Climate Dynamics | 5k-10k |
| Ocean Carbon Cycle and Marine Biogeochemistry | 6k-12k |
| Ocean Remote Sensing and Observing Systems | 4k-8k |
| Marine Ecology, Ecosystems, and Fisheries | 5k-10k |
| Coastal Hazards and Human Impacts | 3k-7k |

The automatic export builds deterministic train/dev/test splits from connected
supporting-source components, so one source document cannot cross split
boundaries. Keep all generated `supporting_facts`, `evidence_spans`,
`evidence_graph`, and `search_trajectory` fields for evidence auditing,
difficulty analysis, and downstream model studies.
Before training, require `training/manifest.json` to report
`split_viable: true`, no unresolved supporting chunks, and no source leakage.
