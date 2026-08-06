# Sample submission

`sample_submission.json` shows the exact accepted shape. Submit only
`challenge_id`, `move_spec_version`, and `moves` — the verifier
computes everything else; client-asserted result fields reject the
whole submission.

The sample's two moves (conjugate r0 by x, then undo it) are legal but
end where they started, so the official verdict on a scored challenge
is `E_NOT_TARGET` with `final_shape` — useful for testing the pipeline.
For an end-to-end accepted example, verify any entry of
`../challenges/training_424.json` against its own `initial_relators`
with the downloadable verifier.
