# Making AI-Assisted Rubric Bias Visible

Data, rubrics, prompts, and reproducible analysis code for:

> *Making AI-Assisted Rubric Bias Visible: Human-in-the-Loop Refinement of Video-Based OSTE Feedback Assessment: Development and Evaluation Study*

## Repository contents

- `data/`: anonymized item-level AI scores for the second revised and strict third rubrics (6,400 rows per version)
- `rubrics/`: complete Japanese and English rubric files for both versions
- `prompts/`: verbatim scoring and pipeline prompts, user-message structure, output format, and inference settings
- `analysis/`: validation and reproduction script
- `results/`: source data for manuscript Tables 2-3 and Figures 2-3
- `figures/`: the three manuscript figures

## Data structure

Each score file contains 64 anonymized videos (`V001`-`V064`), five stochastic AI runs (`R1`-`R5`), and 20 rubric items (`U1`-`U20`): 64 x 5 x 20 = 6,400 item scores per rubric version.

The `imputed` field identifies scores set to the neutral value 3 when the model returned `X`/not assessable or omitted an item. No reasons, evidence quotations, transcripts, images, audio, or video are included.

## Reproduce the results

Python 3.10 or later is recommended.

```bash
python analysis/reproduce_results.py --validate-only
python -m pip install -r requirements-analysis.txt
python analysis/reproduce_results.py
```

The second command writes the table/figure source CSV files under `results/` and regenerated Figures 2-3 under `generated/figures/`.

## Inference conditions

Both rubric versions were scored with Gemini 2.5 Flash through OpenRouter (`google/gemini-2.5-flash`) using identical text-based context and the same scoring prompt template. No video was uploaded during these comparison runs. The strict third-rubric runs were performed on April 24, 2026; the second-rubric runs on July 8, 2026. Provider-default temperature/top-p were used, without seed control. See `prompts/llm_prompts_and_inference_settings.md` for complete details.

## Privacy and exclusions

The original OSTE videos, extracted audio, transcripts, model-generated reasons/evidence, participant images, diarization outputs, and other potentially identifying multimodal files are not deposited because they contain personal information. Only anonymized item-level scores and non-identifying research materials are included.

## Ethics

The study received central review and approval from the Kyushu University Institutional Review Board (approval number 26103).

## License and citation

Code is released under the MIT License. Data and documentation are released under CC BY 4.0; see `LICENSE-DATA`.

Citation metadata and the Zenodo DOI will be added when the archival release is created.
