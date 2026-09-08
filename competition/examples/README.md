# Sample submission

`sample_submission.json` shows the exact accepted shape. Submit only
`challenge_id`, `move_spec_version`, and `moves` — the verifier
computes everything else; client-asserted result fields reject the
whole submission.

One submission may mix both trivialization tracks: the `challenge_id`
prefix picks the track (`ac-v1-` / `sac-v1-`) and `move_spec_version`
must be the one that challenge declares (`ac-r2-v1` / `sac-r8-v1`), or
that solution alone is rejected with `E_SPEC_MISMATCH`. Move ids 0–13
mean the same thing in both specs, which is why the same two moves work
as an illustration on either side.

Both sample solutions' two moves (conjugate r0 by x, then undo it) are
legal but end where they started, so the official verdict on each of
the scored challenges they name is `E_NOT_TARGET` with `final_shape` —
useful for testing the pipeline end to end without needing a real
solution. `ac-v1-00001` and `sac-v1-00001` are the same presentation,
so both report `final_shape: [9, 18]`; they differ only in the target
(the ordered pair `(x, y)` versus the empty presentation).

For accepted examples, verify any entry of
`../challenges/training_424.json` or of
`../challenges/stable_training_424.json` against its own
`initial_relators` with the downloadable verifier.
