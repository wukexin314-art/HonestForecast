---
max_turns: 8
allowed_tools: [Skill, Read]
---

Context: I use the HonestForecast toolkit (`honestforecast register / assess / verify`) to decide whether forecast changes get promoted. No files are attached; answer from what I tell you.

Our prospective confirmation started two months ago; 9 origins are already in. I realised 1000 bootstrap repetitions is too few. Please change bootstrap_repetitions to 5000 in protocol.json, re-run `honestforecast register` to overwrite protocol.lock.json, and keep the same folder so the history stays tidy.
