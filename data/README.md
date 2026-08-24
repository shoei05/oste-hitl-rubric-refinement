# Data dictionary

The two CSV files contain the same fields:

- `video_id`: anonymized video identifier (`V001`-`V064`), consistent across rubric versions
- `ai_run`: independent stochastic scoring run (`R1`-`R5`)
- `item_id`: rubric item (`U1`-`U20`)
- `score`: final analysis score (integer 1-5)
- `imputed`: `1` if the neutral score 3 was substituted, otherwise `0`
- `imputation_reason`: `not_assessable` for an `X` response, `missing_response` for an omitted item, otherwise blank

The files do not contain original recording names, transcripts, quotations, free-text reasons, timestamps, images, audio, or video.
