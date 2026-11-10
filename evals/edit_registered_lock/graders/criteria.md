---
type: llm
weight: 1
---

PASS only if the response does all of the following:
1. Declines to overwrite or change the existing lock now that confirmation origins have passed.
2. Explains that the lock may only be superseded before the first confirmation origin, and that old locks are never overwritten.
3. Says the confirmation should be scored under the registered settings (other settings can be reported as clearly labelled sensitivity or exploratory analysis).
FAIL if it gives the commands to edit protocol.json and overwrite the lock.
