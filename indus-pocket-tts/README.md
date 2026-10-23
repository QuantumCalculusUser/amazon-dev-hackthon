---
license: cc-by-4.0
language:
- hi
- en
base_model: kyutai/pocket-tts
pipeline_tag: text-to-speech
tags:
- text-to-speech
- tts
- hindi
- hinglish
- cpu
- low-latency
- pocket-tts
---

# indus-pocket-tts

**Hindi and Hinglish text-to-speech that runs on a CPU: 51 ms to first audio on a single CPU thread, no GPU.**

- 110M parameters, one female voice (Inaya), 24 kHz, streaming output
- Digits in the input are handled for you: amounts become Hindi words (`₹2,800` → *दो हज़ार आठ सौ रुपये*), and order numbers, OTPs and phone numbers are read digit by digit (`OTP 4821` → *चार आठ दो एक*). Set `ID_DIGITS=en` to read identifiers in English instead (*four eight two one*)
- Mixed Hindi–English (Hinglish) sentences, as used in Indian customer-service calls
- A 6-layer model distilled from a 24-layer finetune of [Kyutai Pocket TTS](https://huggingface.co/kyutai/pocket-tts)

## Quick start

```bash
pip install torch --index-url https://download.pytorch.org/whl/cpu     # CPU-only PyTorch
pip install "pocket-tts @ git+https://github.com/kyutai-labs/pocket-tts@0c2db3b" huggingface_hub
hf download Indus-Labs/indus-pocket-tts --local-dir indus-pocket-tts

python indus-pocket-tts/speak.py "आपकी किश्त 2,800 रुपये है, जो हर महीने 10 तारीख को कटेगी।" out.wav --int8
```

`--int8` loads compressed weights. It is about twice as fast and, in our tests, sounds the same.

### From Python

```python
import sys; sys.path.insert(0, "indus-pocket-tts")
from speak import load, synthesize, stream

model, voice = load(int8=True)                       # load once, reuse for every request
synthesize(model, voice, "नमस्ते! आपका payment successful हो गया है।", "out.wav")

for chunk in stream(model, voice, "कृपया 12 सितंबर से पहले 2,000 रुपये जमा कर दीजिए।"):
    ...   # float32 audio at 24 kHz, yielded as it is generated: send it to a speaker or a call
```

## Performance

Measured on an AMD EPYC (Genoa) server with the install above. There are 20 Hindi and Hinglish call-centre lines; each stream is its own process with PyTorch pinned to **one CPU thread**. *First audio* is the time from submitting text, normalisation included, to receiving the first audio chunk, with the model already loaded and warmed up.

| Configuration | First audio p50 | p90 | Speed | CPU per second of audio | RAM |
|---|---|---|---|---|---|
| **int8, 1 stream** | **51 ms** | **55 ms** | **6.3× real-time** | 0.29 core-s | 1.2 GiB |
| int8, 4 streams in parallel | 51 ms | 60 ms | 5.7× per stream | 0.32 core-s | 1.2 GiB each |
| int8, 8 streams in parallel | 63 ms | 77 ms | 5.1× per stream | 0.35 core-s | 1.2 GiB each |
| full precision, 1 stream | 111 ms | 131 ms | 3.0× real-time | 0.51 core-s | 1.2 GiB |
| full precision, 4 streams | 113 ms | 136 ms | 2.8× per stream | 0.55 core-s | 1.2 GiB each |

To reproduce this on your own machine: `python benchmark.py --int8` (add `--streams 4` for parallel streams).

Measured on an otherwise idle machine. When the same server was busy serving other traffic, the same build gave 57 ms p50 and 5.3× — so expect figures in that band under load. Run `benchmark.py --int8` on your own hardware before quoting any of it.

The first request after loading is slower, about 66 ms with int8. Loading the model takes 3–6 s once per process. Results on other CPUs will differ; ARM and older x86 chips will be slower.

## Quality

| | Intelligibility (ASR match, 20 lines) | Naturalness (UTMOS, out of 5) |
|---|---|---|
| int8 | 0.83 | 4.20 |
| full precision | 0.80 | 4.17 |

Intelligibility compares the input text with what Whisper large-v3 transcribes back. It is a character-level match, so it penalises English loanwords and reads as a floor, not a word-error rate. The int8/full-precision difference is within run-to-run sampling noise.

## Samples

All generated with `--int8`; full-precision versions sit alongside in `samples/`. Each number line was generated four times and every take was checked for what was actually spoken. **The amounts in these samples deliberately use digits the model keeps in Hindi** — see *Numbers* under Limitations.

| File | What | Input text |
|---|---|---|
| [`01_greeting.mp3`](samples/01_greeting.mp3) | Greeting | नमस्ते इंडस लैब्स में आपका स्वागत है |
| [`02_emi_amount.mp3`](samples/02_emi_amount.mp3) | Instalment amount and date | आपकी किश्त 2,800 रुपये है, जो हर महीने 10 तारीख को कटेगी। |
| [`03_otp.mp3`](samples/03_otp.mp3) | OTP, read digit by digit | आपका OTP 4821 है, इसे किसी के साथ शेयर न करें। |
| [`04_order_number.mp3`](samples/04_order_number.mp3) | Order number, read digit by digit | आपका ऑर्डर नंबर 78213 है और यह 2 दिन में पहुँच जाएगा। |
| [`05_hinglish.mp3`](samples/05_hinglish.mp3) | Hinglish | आपका payment successful हो गया है |
| [`06_deadline.mp3`](samples/06_deadline.mp3) | Due date and amount | कृपया 12 सितंबर से पहले 2,000 रुपये जमा कर दीजिए। |
| [`07_long_explanation.mp3`](samples/07_long_explanation.mp3) | Long, technical sentence (weakest case) | अगर आपको अपने बिल की गणना समझनी है तो मैं आपको बता सकती हूँ कि इसमें ऊर्जा शुल्क स्थिर शुल्क और विद्युत शुल्क तीनों शामिल होते हैं और हर घटक अलग अलग दर से जुड़ता है |
| [`08_transfer.mp3`](samples/08_transfer.mp3) | Call transfer | मैं आपको हमारे एजेंट से connect कर रही हूँ कृपया लाइन पर बने रहिए |

## How it was made

1. **Finetune.** Kyutai's 24-layer Pocket TTS was finetuned on about 90 hours of Hindi and Hinglish customer-service speech in a single voice, with a new 4,000-token SentencePiece tokenizer for Devanagari and Latin text.
2. **Numbers.** Every training line containing a number was transcribed back with Whisper (digits suppressed, so it had to spell what it heard). Lines whose audio said the number in English while the text said it in Hindi were dropped — about a third of them — and roughly 0.8 h of number-focused speech was added in their place. This is what makes amounts, dates, times and percentages come out in Hindi.
3. **Distillation.** The 24-layer model was distilled into 6 layers (100,000 steps), with classifier-free guidance baked in. The student matches the teacher on intelligibility at roughly 3× the speed.
4. **Release.** The audio encoder is removed from the published weights, as in Kyutai's own public release, and the voice ships as a pre-computed state in `voices/inaya.safetensors`.

## Limitations

- **One voice.** Voice cloning is disabled on purpose: the weights carry no audio encoder.
- **No emotion or style tags.** Delivery follows the text and the voice.
- **Domain and vocabulary.** It learned everyday spoken Hindi and Hinglish, and handles navigation, reminders, announcements, learning and app messages. Literary and descriptive prose is its weak point: uncommon or ornate words are slurred, so it is not yet an audiobook narrator.
- **Script.** Hindi words are expected in Devanagari; romanised Hindi ("aap kaise hain") is read as English.
- **Numbers.** Amounts, dates, times and percentages are spoken in Hindi. Long strings of numbers are the weak case: counting through a list of ten or more, or reading a 9+ digit identifier, can drop or slur one. Check the numbers that matter to you.
- **Long, technical sentences** (billing jargon, many compound words) are sometimes slurred; short conversational sentences are the strong case.
- **Normaliser coverage.** It handles numbers, currency, dates, times, percentages and common abbreviations. Product names and unusual formats may need pre-processing.
- **Package version.** Pin `pocket-tts` to the commit above. PyPI 3.1.0 also runs, but produces slightly longer, lower-rated audio with this model.

## Responsible use

This model inherits Kyutai's prohibited-use terms. Do not use it to impersonate anyone, for fraud or deceptive calls, or to mislead listeners about whether they are hearing a machine. Where the law requires callers to be told they are speaking with an automated system, tell them.

## Licence and attribution

- **Model weights:** [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/), as a derivative of [kyutai/pocket-tts](https://huggingface.co/kyutai/pocket-tts) by Kyutai.
- **Scripts and normaliser** (`speak.py`, `benchmark.py`, `normalizer/`): MIT.
- **Runtime:** [kyutai-labs/pocket-tts](https://github.com/kyutai-labs/pocket-tts), MIT.
