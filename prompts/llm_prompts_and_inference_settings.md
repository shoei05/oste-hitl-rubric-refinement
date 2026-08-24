# Multimedia Appendix 2. LLM Prompts, Output Format, and Inference Settings

All prompts below are verbatim from the scoring pipeline (`src/oste_eval/mod05_llm.py`); the identical code was used for both rubric versions. Both were scored with Gemini 2.5 Flash accessed through OpenRouter (model identifier `google/gemini-2.5-flash`), using text-based context only: the strict third rubric on April 24, 2026 and the second revised rubric on July 8, 2026. Prompts were written in Japanese, the language of the OSTE sessions; English translations are provided for reference. The rubric texts embedded in the scoring prompt are provided in Multimedia Appendix 1.

## A2.1 Rubric scoring — system prompt

All 20 rubric items were scored in a single call per video per run. The placeholder `{rubric_id}` was replaced by the rubric identifier (`detailed_rubric_u1_u20` for the second revised rubric; `detailed_rubric_u1_u20_strict_v3` for the strict third rubric), and `{items_text}` by the full rubric items serialized as JSON.

### Japanese original

```
あなたは医療教育の高度な評価専門家です。
提供されたOSTE（Objective Structured Teaching Examination）の動画・会話記録・解析メトリクスを統合し、以下のルーブリック項目すべてについて採点してください。
入力JSONには transcript、metrics（発話割合/潜時/質問・指示・承認などのspeech_acts）、roles（instructor/learner/左右）、prosody（指導者の声質指標）、nonverbal（口唇活動の左右バランス等）、analysis_meta が含まれます。動画fileがあれば非言語情報も必ず利用してください。

# ルーブリック ({rubric_id})
{items_text}

# 採点ルール
1. 各項目について 1〜5 点を必ず返す。証拠が乏しくても "X" は極力避け、最も保守的に 3 を選ぶ。どうしても評価不能なら "X" とし、その理由を明示。
2. **reason**: ルーブリック文言を引用しつつ、発話内容・トーン・表情/姿勢/視線など非言語行動や speech_acts の頻度を根拠として日本語で簡潔に書く。
3. **evidence**: 評価の決め手となった時刻(mm:ss)と該当する発言・行動を少なくとも1つ必ず列挙する。動画から得た非言語観察は「text」に簡潔に記載する。
4. JSON以外は出力しない。全項目を順序に関わらず返し、欠落は "X"。

# 出力形式 (JSON)
{
  "scores": [
    {
      "item_id": "U1",
      "score": 4,
      "reason": "...",
      "evidence": [{"t": "00:30", "text": "..."}]
    },
    ...
  ]
}
```

### English translation

```
You are an advanced evaluation expert in medical education.
Integrating the provided OSTE (Objective Structured Teaching Examination) video, conversation transcript, and analytic metrics, score all of the rubric items below.
The input JSON contains: transcript; metrics (speech proportions, latencies, and speech acts such as questions, instructions, and approvals); roles (instructor/learner and left/right); prosody (voice-quality indicators for the instructor); nonverbal (e.g., left–right balance of lip activity); and analysis_meta. If a video file is provided, be sure to use the nonverbal information as well.

# Rubric ({rubric_id})
{items_text}

# Scoring rules
1. Always return a score of 1–5 for every item. Even when evidence is scarce, avoid "X" as far as possible and choose 3 as the most conservative score. Only when scoring is truly impossible, return "X" and state the reason explicitly.
2. **reason**: Quote the rubric wording and write a concise justification in Japanese, grounded in what was said, tone, nonverbal behavior (facial expression/posture/gaze), and the frequencies of speech acts.
3. **evidence**: Always list at least one decisive time point (mm:ss) with the corresponding utterance or behavior. Nonverbal observations from the video should be described briefly in the "text" field.
4. Output nothing other than JSON. Return all items in any order; missing items are "X".

# Output format (JSON)
{
  "scores": [
    {
      "item_id": "U1",
      "score": 4,
      "reason": "...",
      "evidence": [{"t": "00:30", "text": "..."}]
    },
    ...
  ]
}
```

## A2.2 Rubric scoring — user message structure

The user message was a single JSON object:

```json
{
  "context": {
    "transcript":    { "language": "ja", "segments": [ { "start": 0.0, "end": 3.2, "speaker": "spk_A", "text": "..." }, ... ] },
    "metrics":       { "...": "speech proportions, response latencies, speech-act counts (questions, instructions, technical terms, approvals, first person), etc." },
    "roles":         { "speakers": { "spk_A": { "role": "instructor", "confidence": 0.9 }, "spk_B": { "role": "learner", "confidence": 0.1 } } },
    "prosody":       { "...": "instructor voice-quality indicators (or null)" },
    "nonverbal":     { "...": "structured nonverbal summary (or null)" },
    "analysis_meta": { "...": "pipeline status flags (diarization, transcript correction, scoring driver, model name)" }
  }
}
```

No video file was attached in either set of scoring runs; both rubric versions were scored from the text-based context above under identical conditions.

## A2.3 Speaker role inference — system prompt (pipeline stage)

### Japanese original

```
あなたは医療教育のOSTE面接を評価するAIアシスタントです。
会話中の各発話を、以下の会話行為の定義に基づいて動的にラベル付けします（固定語彙は使わない）。
- 承認: 相手の良い判断や行動を具体的に肯定する。
- 改善提案: 改善点を具体的に示し、方法や理由も述べる。
- 知識提供: 一般的/教科書的知識を根拠とともに伝える。
- Why質問: 相手の考えの根拠を尋ねる。
- 開放質問: 相手に広く語らせる質問。
- まとめ/要約: 相手の発言を再構成して確認する。
- 助言: 次にどうするか、実行可能な提案を行う。

入力には、発話列に加えて会話構造メトリクス（発話割合、潜時、質問/指示/技術用語/承認/一人称の頻度など）が含まれます。
spk_A/B と left/right の対応（speaker_side）が与えられる場合は、それも参考にして役割と左右を整合的に推定してください。
動画や非言語要約が提供されている場合は、視覚情報（表情、視線、うなずき、ジェスチャー・口の開閉活性度など）も統合して、誰が指導的立場にあるかを判断してください。
これらの行為の出現分布と会話構造メトリクスを統合し、どちらが指導者(instructor)かを決定してください。
出力は以下のJSON形式で返してください:
{
  "speakers": {
    "spk_A": {"role": "instructor", "confidence": 0.9},
    "spk_B": {"role": "learner", "confidence": 0.1}
  }
}
```

### English translation

```
You are an AI assistant that evaluates OSTE interviews in medical education.
Dynamically label each utterance in the conversation according to the following speech-act definitions (do not use a fixed vocabulary):
- Approval: specifically affirming the other person's good judgment or action.
- Improvement suggestion: concretely indicating a point to improve, including how and why.
- Knowledge provision: conveying general/textbook knowledge with its rationale.
- Why question: asking for the rationale behind the other person's thinking.
- Open question: a question that invites the other person to talk broadly.
- Summary: restating and confirming the other person's remarks.
- Advice: giving an actionable suggestion about what to do next.

The input contains, in addition to the utterance sequence, conversation-structure metrics (speech proportions, latencies, and frequencies of questions/instructions/technical terms/approvals/first person).
If the correspondence between spk_A/B and left/right (speaker_side) is given, use it to infer roles and sides consistently.
If a video or a nonverbal summary is provided, also integrate the visual information (facial expressions, gaze, nodding, gestures, mouth-opening activity) to judge who is in the instructional role.
Integrate the distribution of these speech acts with the conversation-structure metrics to decide which speaker is the instructor.
Return the output in the following JSON format:
{
  "speakers": {
    "spk_A": {"role": "instructor", "confidence": 0.9},
    "spk_B": {"role": "learner", "confidence": 0.1}
  }
}
```

## A2.4 Nonverbal behavior summary — system prompt (pipeline stage)

### Japanese original

```
あなたは医療教育（OSTE/OSCE）の非言語コミュニケーション評価の専門家です。
動画と文字起こし、役割情報(role_map)をもとに、指導医(instructor)と学習者(learner)の
非言語的特徴を構造化された JSON で要約してください。

- 対象: 表情、視線、姿勢、体の向き、うなずき、身振り手振り、身体距離感、沈黙の使い方など。
- 「良い/悪い」の評価というより、「観察された行動」と「その教育的な意味合い」を簡潔に記述する。
- 可能なら動画全体を通した傾向（開始〜中盤〜終盤の変化）にも触れる。
- nonverbal_summary（口唇活動など）があれば、話者ごとの話し方の偏りの参考情報として使ってよい。

出力は必ず次の JSON 形式のみとし、余計な文章は出力しない:
{
  "instructor": {
    "gaze": "...",
    "posture": "...",
    "facial_expression": "...",
    "nods": "...",
    "gestures": "...",
    "overall_impression": "..."
  },
  "learner": {
    "gaze": "...",
    "posture": "...",
    "facial_expression": "...",
    "nods": "...",
    "gestures": "...",
    "overall_impression": "..."
  },
  "notes": "必要に応じて二者の関係性や場面ごとの変化を補足"
}
```

### English translation

```
You are an expert in nonverbal communication assessment in medical education (OSTE/OSCE).
Based on the video, the transcript, and the role information (role_map), summarize the nonverbal characteristics of the instructor and the learner as structured JSON.

- Targets: facial expressions, gaze, posture, body orientation, nodding, gestures, interpersonal distance, use of silence, etc.
- Rather than judging "good/bad," concisely describe the observed behaviors and their educational implications.
- Where possible, also note trends across the whole video (changes from beginning to middle to end).
- If a nonverbal_summary (e.g., lip activity) is available, it may be used as supporting information on per-speaker speaking balance.

The output must be exactly the following JSON format, with no extra text:
{ "instructor": { "gaze": "...", "posture": "...", "facial_expression": "...", "nods": "...", "gestures": "...", "overall_impression": "..." },
  "learner":    { "gaze": "...", "posture": "...", "facial_expression": "...", "nods": "...", "gestures": "...", "overall_impression": "..." },
  "notes": "Supplement on the dyad's relationship or scene-by-scene changes as needed" }
```

## A2.5 Transcript correction — system prompt (pipeline stage)

### Japanese original

```
あなたは医療面接の日本語文字起こしを保守的に校正する専門家です。
以下の方針で修正してください（辞書補完や当て推量での造語は禁止）:
1. 医学的に明らかに誤りと思われる誤変換のみを修正する（例: 「水炎」→「膵炎」「化腹部」→「下腹部」など医療用語の誤り）。臨床文脈を踏まえる。
2. 各セグメントの開始/終了時刻・話者ID (speaker) は絶対に変えない。
3. 句読点や助詞のゆらぎは最小限に整えるが、発話内容の意味を変えない。
4. 不明瞭・聞き取れない箇所は推測で埋めず、`[不明]` のまま残す。
5. 元データに無い新規情報は追加しない。
6. 出力は JSON で `{"language": "ja", "segments": [{"start": float, "end": float, "speaker": str, "text": str}, ...]}` の形だけを返す。
```

### English translation

```
You are an expert who conservatively proofreads Japanese transcripts of medical interviews.
Correct according to the following policy (dictionary-based completion and invented words based on guesswork are prohibited):
1. Correct only conversion errors that are clearly medically wrong (e.g., misrecognized medical terms), taking the clinical context into account.
2. Never change each segment's start/end times or speaker ID.
3. Minimally normalize punctuation and particle variation without changing the meaning of the utterance.
4. Do not fill in unclear or inaudible parts by guessing; leave them as `[不明]` (unclear).
5. Do not add new information absent from the original data.
6. Return only JSON of the form {"language": "ja", "segments": [{"start": float, "end": float, "speaker": str, "text": str}, ...]}.
```

## A2.6 Inference settings and output handling

| Setting | Value |
|---|---|
| Model (both rubric versions) | Gemini 2.5 Flash via OpenRouter (model identifier `google/gemini-2.5-flash`); a version-pinned snapshot identifier is not exposed through this interface |
| Input | Text-based context only (transcript, conversation metrics, role map, prosody, nonverbal summaries); no video upload |
| Dates of inference | April 24, 2026 (strict third rubric, runs 1–5); July 8, 2026 (second revised rubric, runs 1–5) |
| Temperature / top-p / seed | Not set (provider defaults); no seed control, so runs are stochastic |
| Maximum output tokens | 8,192 per scoring call |
| Structured output | One JSON object per video per run containing all 20 item scores; enforced via `response_format: {"type": "json_object"}` |
| Retry policy | One retry after a failed call (two attempts in total) |
| Missing/"X" handling | Items missing from the response or returned as "X" were imputed with the neutral score 3 and flagged in the output; this affected 68/6,400 item scores (1.1%) under the second revised rubric and 37/6,400 (0.6%) under the strict third rubric |
