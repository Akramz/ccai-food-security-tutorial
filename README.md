# Agricultural Monitoring with Fields of The World (FTW)

A hands-on tutorial for the **CCAI Virtual Summer School** (*AI for Agriculture and Food
Security* module). It walks through a satellite-imagery workflow that delineates agricultural
**field boundaries** from Sentinel-2 imagery using the [Fields of The World (FTW)](https://fieldsofthe.world/)
model, then uses those boundaries for two climate-relevant tasks — **crop-type mapping with
few labels** and **forest-loss monitoring** — while foregrounding limitations and responsible
use.

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Akramz/ccai-food-security-tutorial/blob/main/1.0-agriculture-monitoring-with-ftw.ipynb)

## Run it

**Colab (recommended):** click the badge above. The first setup cell clones this repo (for
`utils.py`, the pinned `requirements.txt`, `s2-grid.json`, and the cached CDL sample) and
installs dependencies. The notebook defaults to **fast mode** and runs well under two hours.

**Locally** (Python 3.11–3.12):

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
jupyter lab 1.0-agriculture-monitoring-with-ftw.ipynb
```

## Contents

```text
.
├── 1.0-agriculture-monitoring-with-ftw.ipynb  # the tutorial
├── utils.py                 # helper functions (boundary run, MOSAIKS/RCF, CDL, GLAD)
├── requirements.txt         # pinned runtime dependencies
├── s2-grid.json             # Sentinel-2 MGRS grid for ROI / tile selection
├── samples/                 # cached artifacts for fast mode (small CDL clip + generator)
└── deliverables/            # datasheet, model card, and quiz questions
```

## Deliverables

- [`deliverables/datasheet.md`](deliverables/datasheet.md) — datasheet for the FTW dataset (Gebru et al. format).
- [`deliverables/model_card.md`](deliverables/model_card.md) — model card for the FTW field-boundary model (Mitchell et al. format).
- [`deliverables/quiz.md`](deliverables/quiz.md) — comprehension quiz tied to the learning objectives.

## References

- Fields of The World (dataset & `ftw-tools`): <https://github.com/fieldsoftheworld>
- FTW benchmark paper (Kerner et al., 2025): <https://arxiv.org/abs/2409.16252>

## Authors & contact

See the notebook's *Authors and contact information* section. Questions or feedback: the CCAI
Community Platform, or `tutorials@climatechange.ai`.

## License

MIT — see [LICENSE](LICENSE).
