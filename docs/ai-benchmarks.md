# Local AI measurements

Measured on 2026-10-06 (Asia/Taipei), using synthetic prompts and verified GGUF files. These results select the Arch host defaults; they are not universal throughput guarantees.

## Environment and method

AMD RX 9060 XT (gfx1200), 16,304 MiB dedicated VRAM; Ryzen 7 7700, 8 cores / 16 threads; approximately 32 GB RAM. Dedicated GPU counters were sampled from `/sys/class/drm/card1/device`, not the integrated GPU. Kernel: `7.2.6-arch2-1`; Mesa/Vulkan Radeon: `26.2.3-1`; ROCm runtime: `7.2.4-1`.

The prepared llama.cpp build was 10884, commit `434ddbbc0e30522e897670681e503b797c12b7c1`, with grammar limit 20,000. Actual router tests used llama-swap 224 and the Nix-generated configuration, with only model paths and loopback test ports redirected. Native preparation receipts and services were not redeployed.

`llama-bench` measured PP512, PP4096 and TG128, normally three repetitions. The search compared ROCm0/Vulkan0, q8/q4 KV, ubatch 64/256/512/1024, batch 1024/2048, and threads 4/8 where relevant. Final settings are Vulkan0, all GPU layers, flash attention on, q8 KV, batch 2048, ubatch 512 and eight threads. Increasing ubatch to 1024 reduced 4B PP4096 from 3,277 to 2,979 tok/s and increased peak VRAM by about 508 MiB.

## Candidate results

| Model | PP512 tok/s | PP4096 tok/s | TG128 tok/s | Total GPU peak MiB |
| --- | ---: | ---: | ---: | ---: |
| Existing Qwen3.6 35B A3B MXFP4, ROCm, 16 GPU layers | 486 | — | 20.8 | 9,940 |
| Qwen3.5 9B Q4_K_M, Vulkan | 1,923 | 2,054 | 49.3 | about 6,667 |
| Qwen3.5 4B Q4_K_M, Vulkan | 2,568 | 3,274 | 80.3 | 4,401 |
| Qwen2.5 Coder 1.5B Q8_0, Vulkan | 6,069 | 9,039 | 145.8 | 3,090 |
| Qwen2.5 Coder 3B Q4_K_M, Vulkan | 3,295 | 4,804 | 118.4 | 3,382 |

The original baseline used two repetitions. The 1.5B and initial 9B matrices used flash-attention auto; an explicit-on 9B control reproduced the below-50 result. Peak includes the desktop baseline and is sampled, rather than an allocator cap. Model identities and checksums are pinned in [the artifact registry](../modules/ai/artifacts.nix).

4B is the practical agent default because the 9B candidate missed the throughput target. The completion default is 3B: it passed four small Python/JavaScript/Nix syntax and expected-result fixtures, versus three for 1.5B. This tiny set does not establish general coding quality or equal capability to the original 35B model. Include language context in FIM prefixes: both models misidentified a bare Nix fragment without a `# Nix expression` comment.

## Router and context measurements

With both models resident, a 9,518-token agent prompt yielded 74.8 tok/s alone and 67.1–67.3 tok/s during three overlapping completion requests. Completion sustained 61.0–62.2 tok/s. Warm first content arrived in approximately 48–50 ms for the agent and 10–35 ms for completion. The cold agent request took 3.21 seconds before content, illustrating prompt processing versus generation speed. Total GPU peak was 6,536 MiB, leaving over 9 GiB unused.

Near the former 32K agent context limit, repeated overlapping requests reduced agent generation to 48.0–48.2 tok/s; cold first content took 13.9 seconds. The default agent context is therefore 16K, with completion at 4K. A larger context remains configurable, with a measured speed cost. Harnesses should compact accumulated history and reserve room for output. Their own tool execution and network delays are separate from model throughput; no particular external harness was available for an end-to-end benchmark.

With the final 16K configuration, a 15,168-token synthetic prompt with 128 generated tokens decoded at 72.4 tok/s alone. Three overlapping runs measured agent generation at 59.9, 50.24 and 50.23 tok/s, and completion at 84.3, 60.8 and 60.9 tok/s. Total GPU peak was 6,263 MiB. Cold agent first content took 6.71 seconds; warm requests took 50–55 ms. This clears 50 tok/s in these samples with little margin at long context; it does not guarantee that rate for every workload.

The declared estimates are 6,144 MiB for the agent and 3,072 MiB for completion, within the 11,264 MiB combined budget. This is validation of declared estimates, not a hard GPU allocator limit. The benchmark watchdog stops its own subprocess if free dedicated VRAM drops below 4,096 MiB. Actual Sunshine streaming could not be tested; memory headroom alone cannot prove absence of frame drops or disconnects.

## Thinking and diagnosis

The original verified Qwen3.6 GGUF was tested with `enable_thinking=false` and `true`. False produced `391` for `17 * 23` with no reasoning; true produced reasoning and exhausted a 256-token cap before the final answer. Template inspection confirmed a closed empty thinking block versus an open block. Both decoded around 21 tok/s: disabling thinking reduced generated work but did not fix the slow decoder.

The selected 4B backend was also tested through generated router aliases: false returned `391` without reasoning; the thinking alias returned reasoning and `391`, with a sufficient output limit. Repeated requests confirmed prompt-cache reuse. A synthetic tool-call request produced the expected `lookup_symbol` call and arguments.

The original model was only partially GPU-offloaded under the memory constraint. Fully offloaded smaller models, Vulkan on this GPU, flash attention and shorter retained context provided the measured improvement. Parallel slots share compute and KV memory; they do not guarantee higher per-request speed. The selected policy gives each backend one slot, allowing the two models to work concurrently.

The installed original GGUF has no MTP/nextn tensors. MTP cannot be enabled by adding a flag alone, and draft tensors/buffers also consume memory. No MTP change was needed to meet the measured target. Relevant primary sources: [Unsloth Qwen3.6](https://unsloth.ai/docs/models/qwen3.6), [Qwen3.5 4B model card](https://huggingface.co/Qwen/Qwen3.5-4B), [Qwen2.5 Coder 1.5B model card](https://huggingface.co/Qwen/Qwen2.5-Coder-1.5B), [llama.cpp HIP prompt-processing discussion](https://github.com/ggml-org/llama.cpp/issues/18823), and [MTP buffer discussion](https://github.com/ggml-org/llama.cpp/issues/26038). Those issues informed the investigation; they do not establish that this workstation encountered those exact bugs.

See [the operator guide](ai.md) for configuration, reproduction commands and deployment steps. Scratch evidence remains outside the store in `/var/tmp/nix-ai-benchmark`; no automatic cleanup is performed.
