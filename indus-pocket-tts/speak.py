#!/usr/bin/env python3
"""indus-pocket-tts: Hindi and Hinglish text-to-speech on CPU, in the Inaya voice.

Command line:
    python speak.py "आपकी किश्त 2,800 रुपये है, जो हर महीने 10 तारीख को कटेगी।" out.wav --int8

As a library:
    from speak import load, synthesize, stream
    model, voice = load(int8=True)
    synthesize(model, voice, "नमस्ते! आपका payment successful हो गया है।", "out.wav")
    for chunk in stream(model, voice, "..."):   # 24 kHz float32 chunks, for real-time playback
        ...

Before synthesis, numbers, amounts, dates and abbreviations are spelled out as Hindi words by the
rule-based normaliser in normalizer/, which is pure Python and has no dependencies.
Voice cloning is disabled: the model speaks only with the bundled Inaya voice.
"""
import argparse, os, sys, tempfile, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
SAMPLE_RATE = 24000
# Hindi text tokenises longer than English: allow 80 tokens per chunk (the package default of 50
# can split a single long sentence and skip words). All published quality numbers use 80.
MAX_TOKENS = 80


def _local_config() -> str:
    """config.yaml points at hf://__REPO__/...; resolve that to this folder."""
    with open(os.path.join(HERE, "config.yaml"), encoding="utf-8") as f:
        text = f.read().replace("hf://__REPO__", HERE)
    fd, path = tempfile.mkstemp(prefix="indus_pocket_tts_", suffix=".yaml")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(text)
    return path


def load(int8: bool = False, threads: int = 1):
    """Load the model and the Inaya voice. int8=True is about 2x faster, with compressed weights."""
    import torch
    torch.set_num_threads(threads)
    from pocket_tts.models.tts_model import TTSModel
    model = TTSModel.load_model(config=_local_config(), quantize=int8)
    model.has_voice_cloning = False          # the shipped weights carry no audio encoder
    voice = model.get_state_for_audio_prompt(os.path.join(HERE, "voices", "inaya.safetensors"))
    return model, voice


_normalizer = None


# Identifiers (order numbers, OTPs, phone and account numbers) are read digit by digit
# ("OTP 4821" -> "चार आठ दो एक"), amounts as quantities ("₹4,500" -> "चार हज़ार पाँच सौ रुपये").
# A number counts as an identifier when an ID word comes just before it, or when it is 5+ plain
# digits that are not an amount.
# ID_DIGITS="en" reads identifiers in English instead ("four eight two one"), which is how many
# Indian callers say them aloud; this model speaks the Hindi digits more clearly, so Hindi is default.
_ID_DIGITS = os.environ.get("ID_DIGITS", "hi").lower()
_EN_DIGITS = "zero one two three four five six seven eight nine".split()
_ID_WORDS = r"(?:नंबर|नम्बर|नं\.?|संख्या|क्रमांक|आईडी|ओटीपी|पिन|कोड|खाता|अकाउंट|number|no\.?|id|otp|pin|code|account|a/c|ref)"
_AMOUNT_BEFORE = r"(?:₹|rs\.?|inr|रु\.?)\s*$"
_AMOUNT_AFTER = r"^\s*(?:रुपये|रुपए|रुपया|रु\.?|rupees?|rs\.?|/-)"


def _spell_identifiers(text: str) -> str:
    import re
    def repl(m):
        before, digits, after = text[: m.start()], m.group(0), text[m.end():]
        if re.search(_AMOUNT_BEFORE, before, re.I) or re.search(_AMOUNT_AFTER, after, re.I):
            return digits
        after_id_word = re.search(_ID_WORDS + r"\s*[:#-]?\s*$", before, re.I)
        if after_id_word or len(digits) >= 5:
            if _ID_DIGITS == "en":
                return " ".join(_EN_DIGITS[int(d)] for d in digits)
            from normalizer.hi_normalizer import say_hindi_digits
            return say_hindi_digits(digits)
        return digits

    return re.sub(r"(?<![\d,.])\d{3,}(?![\d,.])", repl, text)


def normalize(text: str) -> str:
    """'EMI 4,500 रुपये, ऑर्डर नंबर 78213' -> 'E M I चार हज़ार पाँच सौ रुपये, ऑर्डर नंबर सात आठ दो एक तीन'."""
    global _normalizer
    if _normalizer is None:
        from normalizer.base_normalizer import create_normalizer
        _normalizer = create_normalizer("hi-IN")
    return _normalizer.normalize(_spell_identifiers(text))


def stream(model, voice, text: str, normalize_text: bool = True):
    """Yield audio chunks (float32, 24 kHz, mono) as soon as each is generated."""
    if normalize_text:
        text = normalize(text)
    yield from model.generate_audio_stream(model_state=voice, text_to_generate=text, max_tokens=MAX_TOKENS)


def synthesize(model, voice, text: str, out_path: str, normalize_text: bool = True) -> None:
    from pocket_tts.data.audio import stream_audio_chunks
    stream_audio_chunks(out_path, stream(model, voice, text, normalize_text), SAMPLE_RATE)


def main() -> None:
    ap = argparse.ArgumentParser(description="indus-pocket-tts: Hindi/Hinglish TTS on CPU (Inaya voice)")
    ap.add_argument("text", help="Hindi or Hinglish text; digits and amounts are fine")
    ap.add_argument("out", nargs="?", default="out.wav", help="output .wav (default: out.wav)")
    ap.add_argument("--int8", action="store_true", help="compressed weights: about 2x faster")
    ap.add_argument("--threads", type=int, default=1, help="CPU threads (default: 1)")
    ap.add_argument("--no-normalize", action="store_true", help="skip number/date expansion")
    ap.add_argument("--seed", type=int, default=None, help="fix the random seed for repeatable output")
    a = ap.parse_args()

    if a.seed is not None:
        import torch
        torch.manual_seed(a.seed)
    t = time.perf_counter()
    model, voice = load(a.int8, a.threads)
    load_s = time.perf_counter() - t

    from pocket_tts.data.audio import stream_audio_chunks
    t0 = time.perf_counter(); first = None; chunks = []
    for c in stream(model, voice, a.text, not a.no_normalize):
        if first is None:
            first = time.perf_counter() - t0
        chunks.append(c)
    total = time.perf_counter() - t0
    stream_audio_chunks(a.out, iter(chunks), SAMPLE_RATE)
    dur = sum(c.numel() for c in chunks) / SAMPLE_RATE
    print(f"{a.out}: {dur:.2f} s of audio | first audio after {first * 1000:.0f} ms | "
          f"{dur / total:.1f}x real-time | model load {load_s:.1f} s")
    print("(The first call on a fresh process is slower; run benchmark.py for steady-state numbers.)")


if __name__ == "__main__":
    main()
