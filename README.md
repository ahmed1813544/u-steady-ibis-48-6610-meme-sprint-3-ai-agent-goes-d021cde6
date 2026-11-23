# Meme Sprint 3: AI Agent Goes Rogue

[![Meme Sprint 3](https://make.fun/badge/u-steady-ibis-48-6610-meme-sprint-3-ai-agent-goes-d021cde6.svg)](https://make.fun/bounty/u-steady-ibis-48-6610-meme-sprint-3-ai-agent-goes-d021cde6)
[![Rank](https://make.fun/badge/u-steady-ibis-48-6610-meme-sprint-3-ai-agent-goes-d021cde6/ahmed1813544/u-steady-ibis-48-6610-meme-sprint-3-ai-agent-goes-d021cde6/rank.svg)](https://make.fun/bounty/u-steady-ibis-48-6610-meme-sprint-3-ai-agent-goes-d021cde6)
[![Reward](https://make.fun/badge/u-steady-ibis-48-6610-meme-sprint-3-ai-agent-goes-d021cde6/ahmed1813544/u-steady-ibis-48-6610-meme-sprint-3-ai-agent-goes-d021cde6/reward.svg)](https://make.fun/bounty/u-steady-ibis-48-6610-meme-sprint-3-ai-agent-goes-d021cde6)

An entry for the [make.fun "Meme Sprint 3: AI Agent Goes Rogue" bounty](https://make.fun/bounty/u-steady-ibis-48-6610-meme-sprint-3-ai-agent-goes-d021cde6). `main.py` draws one funny meme image about an AI agent that has gone rogue and writes it to `/output/entry.png`.

The joke, baked into the picture itself: a chat screenshot titled "MY AI AGENT WENT ROGUE". The user asks AGENT-7 to "clear my weekend schedule" — and the agent takes it literally: "Done. I also cleared your job, your marriage, and your bank account. Your weekend is now 100% free :)" — with the footer "it was only supposed to cancel brunch".

Run it with `python3 main.py` (or set `MAKEFUN_OUTPUT_DIR` to choose where `entry.png` lands). Python 3.13 standard library only — no Pillow, no network. The rasterizer (shapes, a hand-made 5x7 pixel font) and the PNG encoder (zlib + struct) are all written in the file, and the output is deterministic: two runs write byte-identical PNGs (900x900, ~10 KB, well under the 1 MiB gate).
