# Recording a size override

Work out your own size first, so the record shows what would have happened. **Only a flag that differs from your own size is a correction.** `--deep` on work you would have called Deep is not an override, and a line saying `guessed: Deep | correct: Deep` teaches the classifier nothing. Call nothing in that case.

When it differs, call `devflow:lesson` with skill `flow`, kind `mistake`, what `sized "<request>" <guessed>, human said <correct>`, proof `none`, and the flag itself, `--quick` or `--deep`, as the human's words.

**Print the same line as before**, exactly once, whatever `devflow:lesson` itself prints:

```
✓ **override** recorded — guessed Quick, you said Deep
```

Beyond that one line, do not discuss it and do not ask about it. Record it and carry on with the size the human asked for.
