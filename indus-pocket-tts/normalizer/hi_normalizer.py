"""
Enhanced Hindi text normalization with comprehensive fixes
and improved handling of edge cases.
"""
import re
from functools import lru_cache
try:
    from .base_normalizer import BaseNormalizer
except ModuleNotFoundError:
    from base_normalizer import BaseNormalizer

# Hindi months (Devanagari)
HINDI_MONTHS = {
    "01": "जनवरी", "1": "जनवरी",
    "02": "फ़रवरी", "2": "फ़रवरी",
    "03": "मार्च", "3": "मार्च",
    "04": "अप्रैल", "4": "अप्रैल",
    "05": "मई", "5": "मई",
    "06": "जून", "6": "जून",
    "07": "जुलाई", "7": "जुलाई",
    "08": "अगस्त", "8": "अगस्त",
    "09": "सितंबर", "9": "सितंबर",
    "10": "अक्टूबर", "11": "नवंबर", "12": "दिसंबर"
}

# Direct number mappings (0-100)
DIRECT_DICT = {
    0: "शून्य", 1: "एक", 2: "दो", 3: "तीन", 4: "चार", 5: "पाँच",
    6: "छः", 7: "सात", 8: "आठ", 9: "नौ", 10: "दस",
    11: "ग्यारह", 12: "बारह", 13: "तेरह", 14: "चौदह", 15: "पंद्रह",
    16: "सोलह", 17: "सत्रह", 18: "अट्ठारह", 19: "उन्नीस", 20: "बीस",
    21: "इक्कीस", 22: "बाईस", 23: "तेईस", 24: "चौबीस", 25: "पच्चीस",
    26: "छब्बीस", 27: "सत्ताईस", 28: "अट्ठाईस", 29: "उनतीस", 30: "तीस",
    31: "इकतीस", 32: "बत्तीस", 33: "तैंतीस", 34: "चौंतीस", 35: "पैंतीस",
    36: "छत्तीस", 37: "सैंतीस", 38: "अड़तीस", 39: "उनतालीस", 40: "चालीस",
    41: "इकतालीस", 42: "बयालीस", 43: "तैंतालीस", 44: "चौंतालीस", 45: "पैंतालीस",
    46: "छियालीस", 47: "सैंतालीस", 48: "अड़तालीस", 49: "उनचास", 50: "पचास",
    51: "इक्यावन", 52: "बावन", 53: "तिरेपन", 54: "चौवन", 55: "पचपन",
    56: "छप्पन", 57: "सत्तावन", 58: "अट्ठावन", 59: "उनसठ", 60: "साठ",
    61: "इकसठ", 62: "बासठ", 63: "तिरेसठ", 64: "चौंसठ", 65: "पैंसठ",
    66: "छयासठ", 67: "सरसठ", 68: "अड़सठ", 69: "उनहत्तर", 70: "सत्तर",
    71: "इकहत्तर", 72: "बहत्तर", 73: "तिहत्तर", 74: "चौहत्तर", 75: "पचहत्तर",
    76: "छिहत्तर", 77: "सतहत्तर", 78: "अठहत्तर", 79: "उन्यासी", 80: "अस्सी",
    81: "इक्यासी", 82: "बयासी", 83: "तिरासी", 84: "चौरासी", 85: "पचासी",
    86: "छियासी", 87: "सत्तासी", 88: "अठासी", 89: "नवासी", 90: "नब्बे",
    91: "इक्यानवे", 92: "बानवे", 93: "तिरानवे", 94: "चौरानवे", 95: "पचानवे",
    96: "छियानवे", 97: "सत्तानवे", 98: "अट्ठानवे", 99: "निन्यानवे", 100: "सौ"
}

VARIATIONS_DICT = {
    150: "डेढ़ सौ", 250: "ढाई सौ", 350: "साढ़े तीन सौ",
    450: "साढ़े चार सौ", 550: "साढ़े पाँच सौ", 650: "साढ़े छः सौ",
    750: "साढ़े सात सौ", 850: "साढ़े आठ सौ", 950: "साढ़े नौ सौ",
    1500: "डेढ़ हज़ार", 2500: "ढाई हज़ार",
    150000: "डेढ़ लाख", 250000: "ढाई लाख",
    15000000: "डेढ़ करोड़", 25000000: "ढाई करोड़"
}

# Hindi digits for reading out digit-by-digit
HINDI_DIGITS = ["शून्य", "एक", "दो", "तीन", "चार", "पाँच", "छः", "सात", "आठ", "नौ"]

# Common Hindi abbreviations
#HINDI_ABBREVIATIONS = {
#    r"\bश्री\.?\b": "श्री",
#    r"\bश्रीमती\.?\b": "श्रीमती",
#    r"\bडॉ\.?\b": "डॉक्टर",
#    r"\bप्रो\.?\b": "प्रोफ़ेसर",
#}

HINDI_ABBREVIATIONS = {
    # Use explicit token boundaries instead of \b for Devanagari.
    # Python \b can split unexpectedly around vowel signs/matras.
    r"(?<![\u0900-\u097FA-Za-z0-9_])प्रोजेक्ट्स\.?(?![\u0900-\u097FA-Za-z0-9_])": "projects",
    r"(?<![\u0900-\u097FA-Za-z0-9_])प्रोजेक्ट\.?(?![\u0900-\u097FA-Za-z0-9_])": "project",
    r"(?<![\u0900-\u097FA-Za-z0-9_])प्रोडक्ट्स\.?(?![\u0900-\u097FA-Za-z0-9_])": "products",
    r"(?<![\u0900-\u097FA-Za-z0-9_])प्रोडक्ट\.?(?![\u0900-\u097FA-Za-z0-9_])": "product",
    r"(?<![\u0900-\u097FA-Za-z0-9_])श्रीमती\.?(?![\u0900-\u097FA-Za-z0-9_])": "श्रीमती",
    r"(?<![\u0900-\u097FA-Za-z0-9_])श्री\.?(?![\u0900-\u097FA-Za-z0-9_])": "श्री",
    r"(?<![\u0900-\u097FA-Za-z0-9_])डॉ\.?(?![\u0900-\u097FA-Za-z0-9_])": "डॉक्टर",
    r"(?<![\u0900-\u097FA-Za-z0-9_])प्रो\.?(?![\u0900-\u097FA-Za-z0-9_])": "प्रोफ़ेसर",
}

# Hindi acronyms (spell out letter by letter)
HINDI_ACRONYMS = {
    "आरबीआई", "जीएसटी", "यूपीआई", "ओटीपी", "केवाईसी", "एटीएम", 
    "पीएफ", "ईएसआई", "एनपीएस", "आधार"
}

# Common measurement units in Hindi - Order matters! Longer patterns first
HINDI_UNITS = [
    (r"\b(\d+(?:\.\d+)?)\s?(किलोमीटर)\b", "किलोमीटर"),
    (r"\b(\d+(?:\.\d+)?)\s?(किलोग्राम)\b", "किलोग्राम"),
    (r"\b(\d+(?:\.\d+)?)\s?(सेंटीमीटर)\b", "सेंटीमीटर"),
    (r"\b(\d+(?:\.\d+)?)\s?(मिलीलीटर)\b", "मिलीलीटर"),
    (r"\b(\d+(?:\.\d+)?)\s?(किमी|km)\b", "किलोमीटर"),
    (r"\b(\d+(?:\.\d+)?)\s?(किलो|kg)\b", "किलोग्राम"),
    (r"\b(\d+(?:\.\d+)?)\s?(सेमी|cm)\b", "सेंटीमीटर"),
    (r"\b(\d+(?:\.\d+)?)\s?(मीटर|m)\b", "मीटर"),
    (r"\b(\d+(?:\.\d+)?)\s?(ग्राम|g)\b", "ग्राम"),
    (r"\b(\d+(?:\.\d+)?)\s?(लीटर|l)\b", "लीटर"),
    (r"\b(\d+(?:\.\d+)?)\s?(ml)\b", "मिलीलीटर"),
]


@lru_cache(maxsize=4096)
def int_to_hindi_words(n: int, use_variations: bool = True) -> str:
    """
    Convert integer to Hindi words using Indian numbering system.
    Handles: 0 to 999,99,99,999 (up to 99 crore)
    """
    if n == 0:
        return "शून्य"
    
    if n < 0:
        return f"माइनस {int_to_hindi_words(-n, use_variations)}"
    
    # Check for colloquial variations first
    if use_variations and n in VARIATIONS_DICT:
        return VARIATIONS_DICT[n]
    
    # Handle 1-100 directly
    if 0 <= n <= 100:
        if n == 100:
            return "एक सौ"
        return DIRECT_DICT.get(n, str(n))
    
    parts = []
    
    # Crore (10,000,000)
    if n >= 10_000_000:
        crore = n // 10_000_000
        n = n % 10_000_000
        if crore == 1:
            parts.append("एक करोड़")
        elif crore <= 100:
            parts.append(DIRECT_DICT.get(crore, str(crore)) + " करोड़")
        else:
            parts.append(int_to_hindi_words(crore, use_variations=False) + " करोड़")
    
    # Lakh (100,000)
    if n >= 100_000:
        lakh = n // 100_000
        n = n % 100_000
        if lakh == 1:
            parts.append("एक लाख")
        elif lakh <= 100:
            parts.append(DIRECT_DICT.get(lakh, str(lakh)) + " लाख")
        else:
            parts.append(int_to_hindi_words(lakh, use_variations=False) + " लाख")
    
    # Thousand (1,000)
    if n >= 1_000:
        thousand = n // 1_000
        n = n % 1_000
        if thousand == 1:
            parts.append("एक हज़ार")
        elif thousand <= 100:
            parts.append(DIRECT_DICT.get(thousand, str(thousand)) + " हज़ार")
        else:
            parts.append(int_to_hindi_words(thousand, use_variations=False) + " हज़ार")
    
    # Hundred (100)
    if n >= 100:
        hundred = n // 100
        n = n % 100
        if hundred == 1:
            parts.append("एक सौ")
        else:
            parts.append(DIRECT_DICT.get(hundred, str(hundred)) + " सौ")
    
    # Remaining (0-99)
    if n > 0:
        parts.append(DIRECT_DICT.get(n, str(n)))
    
    return " ".join(parts)


@lru_cache(maxsize=2048)
def float_to_hindi_words(number_str: str, use_variations: bool = True) -> str:
    """Convert float strings to Hindi words."""
    number_str = str(number_str).strip()
    
    if not number_str:
        return ""
    
    # Handle sign
    sign = ""
    if number_str[0] in "+-":
        sign = "माइनस " if number_str[0] == "-" else "प्लस "
        number_str = number_str[1:]
    
    # If no decimal point, treat as integer
    if "." not in number_str:
        try:
            return f"{sign}{int_to_hindi_words(int(number_str), use_variations)}".strip()
        except ValueError:
            return f"{sign}{number_str}".strip()
    
    # Split into integer and decimal parts
    integer_part, decimal_part = number_str.split(".", 1)
    integer_part = integer_part or "0"
    
    try:
        integer_words = int_to_hindi_words(int(integer_part), use_variations)
    except ValueError:
        integer_words = integer_part
    
    # Handle decimal digits
    decimal_digits = [d for d in decimal_part if d.isdigit()]
    if not decimal_digits or all(d == "0" for d in decimal_digits):
        return f"{sign}{integer_words}".strip()
    
    decimal_words = " ".join(HINDI_DIGITS[int(d)] for d in decimal_digits)
    return f"{sign}{integer_words} दशमलव {decimal_words}".strip()


def say_hindi_digits(num: str) -> str:
    """Convert numeric string to spoken Hindi digits."""
    result = []
    for char in num:
        if char.isdigit():
            result.append(HINDI_DIGITS[int(char)])
        elif char == '.':
            result.append("दशमलव")
        elif char == ',':
            continue  # Skip commas
    return " ".join(result)


def convert_devanagari_digits(text: str) -> str:
    """Convert Devanagari digits (०-९) to Arabic numerals (0-9) for processing."""
    devanagari_to_arabic = str.maketrans("०१२३४५६७८९", "0123456789")
    return text.translate(devanagari_to_arabic)


def ordinal_hindi(n: int) -> str:
    """Convert number to Hindi ordinal form."""
    ordinal_map = {
        1: "पहला", 2: "दूसरा", 3: "तीसरा", 4: "चौथा", 5: "पाँचवाँ",
        6: "छठा", 7: "सातवाँ", 8: "आठवाँ", 9: "नौवाँ", 10: "दसवाँ"
    }
    
    if n in ordinal_map:
        return ordinal_map[n]
    else:
        return int_to_hindi_words(n, use_variations=False) + "वाँ"


def year_to_hindi(year: int) -> str:
    """
    Convert year to natural Hindi pronunciation.
    1947 -> उन्नीस सौ सैंतालीस (not एक हज़ार नौ सौ सैंतालीस)
    """
    if 1000 <= year <= 1999:
        century = year // 100
        remainder = year % 100
        century_words = int_to_hindi_words(century, use_variations=False)
        
        if remainder == 0:
            return f"{century_words} सौ"
        else:
            remainder_words = int_to_hindi_words(remainder, use_variations=False)
            return f"{century_words} सौ {remainder_words}"
    else:
        return int_to_hindi_words(year, use_variations=False)


def spell_alphanumeric_hindi(text: str) -> str:
    """Spell out alphanumeric codes in Hindi."""
    result = []
    for char in text:
        if char.isalpha():
            result.append(char.upper())
        elif char.isdigit():
            result.append(HINDI_DIGITS[int(char)])
        else:
            result.append(char)
    return " ".join(result)


class HindiNormalizer(BaseNormalizer):
    """Enhanced Hindi text normalizer with comprehensive bug fixes."""
    
    def __init__(self, locale: str = "hi-IN", read_urls_as: str = "verbatim", 
                 use_colloquial: bool = True):
        self.read_urls_as = read_urls_as
        self.use_colloquial = use_colloquial
        super().__init__(locale)
    
    def _compile_patterns(self):
        """Compile regex patterns for Hindi normalization."""
        # Enhanced currency patterns to catch Rs, Rs., रु, रु.
        self._re_currency = re.compile(
            r"(₹|रु\.?|Rs\.?)\s?([0-9०-९][0-9०-९,]*)(?:\.([0-9०-९]{1,2}))?",
            re.IGNORECASE
        )
        
        # FIXED: Phone numbers with international prefix support
        self._re_phone = re.compile(r"(\+91[-\s]?)?([6-9]\d[-\s]?\d{4}[-\s]?\d{5}|[6-9]\d{9})\b")
        
        # Dates (DD/MM/YYYY, DD-MM-YYYY)
        self._re_date_dmy = re.compile(r"\b([0-3]?[0-9०-९])[/.-]([0-1]?[0-9०-९])[/.-]([0-9०-९]{4})\b")
        
        # Time pattern
        self._re_time_24h = re.compile(
            r"\b([0-2]?[0-9०-९]):([0-5][0-9०-९])(?::([0-5][0-9०-९]))?(?:\s+बजे)?\b"
        )
        
        # Temperature patterns (°C, °F)
        self._re_temp_c = re.compile(r"\b(\d+(?:\.\d+)?)\s?(?:°\s*)?C\b", re.IGNORECASE)
        self._re_temp_f = re.compile(r"\b(\d+(?:\.\d+)?)\s?(?:°\s*)?F\b", re.IGNORECASE)
        
        # Percentages
        self._re_percent = re.compile(r"\b([0-9०-९]{1,3})(?:\.([0-9०-९]+))?%\b")
        
        # Email addresses
        self._re_email = re.compile(r"\b([A-Za-z0-9._%+-]+)@([A-Za-z0-9.-]+\.[A-Za-z]{2,})\b")
        
        # Enhanced URL pattern to catch domain-only URLs
        self._re_url = re.compile(
            r"\bhttps?://[^\s]+|\bwww\.[^\s]+\b|\b[a-z0-9-]+\.(com|org|net|in|co\.in|edu|gov)\b",
            re.IGNORECASE
        )
        
        # Alphanumeric codes (PAN, IFSC, etc.)
        self._re_alphanumeric = re.compile(r"\b([A-Z]+\d+[A-Z]*)\b")
        
        # Numbers with commas
        self._re_number_comma = re.compile(r"\b([0-9०-९]{1,3}(?:,[0-9०-९]{2,3})+)\b")
        
        # Plain numbers
        self._re_number = re.compile(r"\b([0-9०-९]+)(?:\.([0-9०-९]+))?\b")
        
        # Dotted numeric sequences (IPs, versions)
        self._re_dotted_number = re.compile(r"\b\d+(?:\.\d+){2,}\b")
        
        # Ordinals
        self._re_ordinal = re.compile(r"\b([0-9०-९]+)(st|nd|rd|th)\b", re.IGNORECASE)
        
        # Hindi acronyms
        self._re_hindi_acronym = re.compile(r"\b([A-Z]{2,})\b")
    
    def normalize(self, text: str) -> str:
        """Normalize Hindi text for TTS."""
        if not text or not text.strip():
            return text

        text = self._normalize_dso(text)
        
        # Handle Devanagari digit sequences
        text = self._handle_devanagari_digit_sequences(text)
        
        # Convert remaining Devanagari digits to Arabic
        text = convert_devanagari_digits(text)
        
        # Normalize whitespace and quotes
        text = self._normalize_whitespace(text)
        text = self._normalize_quotes(text)
        
        # Apply Hindi abbreviations
        for pat, repl in HINDI_ABBREVIATIONS.items():
            text = re.sub(pat, repl, text)
        
        # Apply transformations in order
        text = self._expand_temperatures(text)
        text = self._expand_units(text)
        text = self._expand_currency(text)
        text = self._expand_percent(text)
        text = self._expand_dates_times(text)
        text = self._expand_phones(text)
        text = self._expand_alphanumeric_codes(text)
        text = self._expand_emails_urls(text)
        text = self._expand_dotted_numbers(text)
        text = self._expand_numbers(text)
        text = self._expand_acronyms(text)
        
        # Final cleanup
        text = self._normalize_whitespace(text)
        
        return text.strip()
    
    def _handle_devanagari_digit_sequences(self, s: str) -> str:
        """Handle sequences of Devanagari digits by reading them digit-by-digit."""
        devanagari_digit_pattern = re.compile(r'[०-९]+')
        
        def replace_devanagari_sequence(m):
            devanagari_seq = m.group(0)
            devanagari_to_arabic = str.maketrans("०१२३४५६७८९", "0123456789")
            arabic_seq = devanagari_seq.translate(devanagari_to_arabic)
            return say_hindi_digits(arabic_seq)
        
        return devanagari_digit_pattern.sub(replace_devanagari_sequence, s)
    
    def _expand_temperatures(self, s: str) -> str:
        """Expand temperature notations to Hindi."""
        # Celsius
        def repl_c(m):
            num = m.group(1)
            if "." in num:
                num_words = float_to_hindi_words(num, self.use_colloquial)
            else:
                num_words = int_to_hindi_words(int(num), self.use_colloquial)
            return f"{num_words} डिग्री सेल्सियस"
        s = self._re_temp_c.sub(repl_c, s)
        
        # Fahrenheit
        def repl_f(m):
            num = m.group(1)
            if "." in num:
                num_words = float_to_hindi_words(num, self.use_colloquial)
            else:
                num_words = int_to_hindi_words(int(num), self.use_colloquial)
            return f"{num_words} डिग्री फ़ारेनहाइट"
        s = self._re_temp_f.sub(repl_f, s)
        
        return s
    
    def _expand_units(self, s: str) -> str:
        """Expand measurement units to Hindi words."""
        # Process units in order (longer patterns first to avoid partial matches)
        for pat, unit_word in HINDI_UNITS:
            rx = re.compile(pat, re.IGNORECASE)
            def repl(m):
                val_str = m.group(1)
                if "." in val_str:
                    num_words = float_to_hindi_words(val_str, self.use_colloquial)
                else:
                    num_words = int_to_hindi_words(int(val_str), self.use_colloquial)
                return f"{num_words} {unit_word}"
            s = rx.sub(repl, s)
        return s
    
    def _expand_currency(self, s: str) -> str:
        """Expand all currency formats to spoken Hindi."""
        def repl(m):
            symbol, integer, paise = m.groups()
            
            # Remove commas and convert to int
            n = int(integer.replace(",", ""))
            
            # Convert to Hindi words
            spoken = int_to_hindi_words(n, use_variations=self.use_colloquial)
            
            if paise:
                p = int(paise)
                if p == 0:
                    return f"रुपये {spoken}"
                else:
                    # Proper paise handling
                    if len(paise) == 1:
                        p = p * 10  # .5 becomes 50 paise
                    paise_spoken = int_to_hindi_words(p, use_variations=False)
                    return f"रुपये {spoken} और {paise_spoken} पैसे"
            else:
                return f"रुपये {spoken}"
        
        return self._re_currency.sub(repl, s)
    
    def _expand_percent(self, s: str) -> str:
        """Expand percentages to spoken Hindi."""
        def repl(m):
            whole, frac = m.groups()
            whole_spoken = int_to_hindi_words(int(whole), use_variations=False)
            
            if frac:
                frac_spoken = " ".join(HINDI_DIGITS[int(d)] for d in frac)
                return f"{whole_spoken} दशमलव {frac_spoken} प्रतिशत"
            return f"{whole_spoken} प्रतिशत"
        
        s = self._re_percent.sub(repl, s)
        s = s.replace("%", " प्रतिशत")
        return s
    
    def _expand_dates_times(self, s: str) -> str:
        """FIXED: Expand dates and times without redundant words."""
        # Dates
        def repl_date(m):
            d, mth, y = m.groups()
            day = int(d)
            month_num = mth.lstrip("0") or mth
            month = HINDI_MONTHS.get(month_num, month_num)
            year = int(y)
            
            day_spoken = ordinal_hindi(day)
            year_spoken = year_to_hindi(year)
            
            return f"{day_spoken} {month} {year_spoken}"
        
        s = self._re_date_dmy.sub(repl_date, s)
        
        # FIXED: Time with no redundant "घंटे" or duplicate "बजे"
        time_period_words = ["सुबह", "दोपहर", "शाम", "रात"]
        duration_words = ["घंटे", "घंटा", "समय", "लगेगा", "लगे", "लगा"]
        time_words = ["बजे", "बजकर"]
        
        def repl_time(m):
            hh, mm, ss = m.groups()
            h = int(hh)
            minute = int(mm)
            
            # Get context around the match
            match_start = m.start()
            match_end = m.end()
            context_start = max(0, match_start - 20)
            context_end = min(len(s), match_end + 15)
            
            prefix_context = s[context_start:match_start].strip().split()
            suffix_context = s[match_end:context_end].strip().split()
            
            # Check if this is a duration
            is_duration = any(word in suffix_context for word in duration_words)
            
            # Check if time period or time word already exists
            has_time_period = any(word in prefix_context for word in time_period_words)
            has_time_word = any(word in suffix_context for word in time_words)
            
            # FIXED #1: Remove redundant "घंटे" after minutes in durations
            if is_duration:
                hour_words = int_to_hindi_words(h, use_variations=False)
                if minute == 0:
                    return f"{hour_words} घंटे"
                minute_words = int_to_hindi_words(minute, use_variations=False)
                # Return WITHOUT extra "घंटे" at the end
                return f"{hour_words} घंटे {minute_words} मिनट"
            
            # Convert to 12-hour format
            if h == 0:
                h12 = 12
                ampm = "रात"
            elif 1 <= h < 6:
                h12 = h
                ampm = "रात"
            elif 6 <= h < 12:
                h12 = h
                ampm = "सुबह"
            elif h == 12:
                h12 = 12
                ampm = "दोपहर"
            elif 13 <= h < 16:
                h12 = h - 12
                ampm = "दोपहर"
            elif 16 <= h < 20:
                h12 = h - 12
                ampm = "शाम"
            else:
                h12 = h - 12
                ampm = "रात"
            
            hour_spoken = int_to_hindi_words(h12, use_variations=False)
            
            # FIXED #2: No duplicate "बजे" - only add at end if not already present
            if ss:
                sec_spoken = int_to_hindi_words(int(ss), use_variations=False)
                minute_spoken = int_to_hindi_words(minute, use_variations=False)
                time_str = f"{hour_spoken} बजकर {minute_spoken} मिनट {sec_spoken} सेकंड"
            elif minute == 0:
                # Only one "बजे" when no minutes
                time_str = f"{hour_spoken} बजे"
            else:
                minute_spoken = int_to_hindi_words(minute, use_variations=False)
                # Use "बजकर" for minutes, no trailing "बजे"
                time_str = f"{hour_spoken} बजकर {minute_spoken} मिनट"
            
            # Add time period only if not already present
            if has_time_period or has_time_word:
                return time_str
            else:
                return f"{ampm} {time_str}"
        
        s = self._re_time_24h.sub(repl_time, s)
        
        return s
    
    def _expand_phones(self, s: str) -> str:
        """FIXED: Expand phone numbers with international prefix support."""
        def repl(m):
            prefix = m.group(1)  # +91 or None
            num = m.group(2)
            
            # Remove hyphens and spaces from the number
            num_clean = num.replace("-", "").replace(" ", "")
            
            # FIXED #3: Handle international prefix
            if prefix:
                # Convert +91 to spoken form
                prefix_clean = prefix.replace("+", "").replace("-", "").replace(" ", "")
                prefix_spoken = "प्लस " + " ".join(HINDI_DIGITS[int(d)] for d in prefix_clean) + " "
                num_spoken = say_hindi_digits(num_clean)
                return prefix_spoken + num_spoken
            else:
                return say_hindi_digits(num_clean)
        
        return self._re_phone.sub(repl, s)
    
    def _expand_alphanumeric_codes(self, s: str) -> str:
        """Expand alphanumeric codes like PAN, IFSC, etc."""
        def repl(m):
            code = m.group(1)
            # Spell out the code
            return spell_alphanumeric_hindi(code)
        
        return self._re_alphanumeric.sub(repl, s)
    
    def _expand_emails_urls(self, s: str) -> str:
        """Expand emails and URLs to spoken form."""
        # Handle emails
        def repl_email(m):
            user, domain = m.groups()
            user_spoken = user.replace("_", " अंडरस्कोर ").replace(".", " डॉट ")
            domain_spoken = domain.replace(".", " डॉट ")
            return f"{user_spoken} एट {domain_spoken}"
        
        s = self._re_email.sub(repl_email, s)
        
        # Handle URLs
        def repl_url(m):
            url = m.group(0)
            
            if self.read_urls_as == "url":
                return "यू आर एल"
            
            # Remove protocol
            cleaned = re.sub(r"^https?://", "", url, flags=re.IGNORECASE)
            
            if self.read_urls_as == "domain":
                domain = cleaned.split("/")[0]
                return domain.replace(".", " डॉट ")
            
            # Verbatim mode
            cleaned = cleaned.replace("www.", "www डॉट ")
            cleaned = cleaned.replace(".", " डॉट ")
            cleaned = cleaned.replace("/", " स्लैश ")
            cleaned = cleaned.replace("-", " डैश ")
            return cleaned
        
        s = self._re_url.sub(repl_url, s)
        
        return s

    def _expand_dotted_numbers(self, s: str) -> str:
        """Expand dotted numeric sequences (e.g., IPs, versions) as digit groups."""
        def repl(m):
            parts = m.group(0).split(".")
            spoken_parts = [
                " ".join(HINDI_DIGITS[int(d)] for d in part) for part in parts
            ]
            return " डॉट ".join(spoken_parts)
        return self._re_dotted_number.sub(repl, s)
    
    def _expand_numbers(self, s: str) -> str:
        """Expand remaining numbers to spoken Hindi."""
        # First handle numbers with commas
        def repl_comma(m):
            num_str = m.group(1)
            num = int(num_str.replace(",", ""))
            return int_to_hindi_words(num, use_variations=self.use_colloquial)
        
        s = self._re_number_comma.sub(repl_comma, s)
        
        # Then handle decimal numbers
        def repl_decimal(m):
            whole, frac = m.groups()
            whole_num = int(whole)
            whole_spoken = int_to_hindi_words(whole_num, use_variations=self.use_colloquial)
            
            if frac:
                frac_spoken = " ".join(HINDI_DIGITS[int(d)] for d in frac)
                return f"{whole_spoken} दशमलव {frac_spoken}"
            return whole_spoken
        
        s = self._re_number.sub(repl_decimal, s)
        
        return s
    
    def _expand_acronyms(self, s: str) -> str:
        """Expand Hindi acronyms by spelling them out."""
        def repl(m):
            tok = m.group(1)
            # Check if it's a known acronym
            if tok.upper() in ["RBI", "GST", "UPI", "OTP", "KYC", "ATM", "PF", 
                               "ESI", "NPS", "PAN", "IFSC", "EMI", "SIP", "UIDAI"]:
                return " ".join(list(tok))
            return tok
        
        return self._re_hindi_acronym.sub(repl, s)


# Utility function for testing
def test_hindi_normalizer():
    """Test the enhanced Hindi normalizer."""
    normalizer = HindiNormalizer(locale="hi-IN", use_colloquial=True)
    
    test_cases = [
        # FIXED #1: Redundant "घंटे" in time duration
        "दूरी 250 किमी है और समय 3:45 घंटे लगेगा।",
        "यात्रा में 5:30 घंटे लगे।",
        
        # FIXED #2: Duplicate "बजे" in clock time
        "दोपहर 12:00 बजे।",
        "रात 23:59 बजे।",
        "मीटिंग 14:30 बजे होगी।",
        
        # FIXED #3: Lost international prefix (+91) in phone numbers
        "संपर्क: +91-9876543210",
        "कॉल करें +91 9876543210 पर।",
        "फोन: 9876543210",
        
        # Other test cases
        "मुझे Rs 5000 चाहिए।",
        "यह Rs. 2,50,000 का मकान है।",
        "टिकट का दाम Rs 850.50 है।",
        
        "तापमान 37.5°C है।",
        "बुखार 102.5°F है।",
        "पानी 100°C पर उबलता है।",
        
        "ट्रेन 06:30 पर आएगी।",
        "सुबह 5:30 बजे उठना है।",
        
        "PAN नंबर ABCDE1234F है।",
        "IFSC कोड SBIN0001234 है।",
        "ऑर्डर #ABC123 है।",
        
        "विजिट करें example.co.in",
        "साइट https://www.example.com पर जाएं।",
        "देखें india.gov.in पर।",
        
        "दूरी 125.5 किलोमीटर है।",
        "दूरी 50 किमी है।",
        "वजन 75.2 किलो है।",
        "वजन 1.5 किलोग्राम है।",
        "ऊंचाई 180 सेमी है।",
        "लंबाई 5 मीटर है।",
        
        "Rs 1,50,000 का भुगतान 15/12/2024 तक करें।",
        "संपर्क: +91-9876543210, ईमेल: contact@company.co.in",
        "तापमान 25°C है और आर्द्रता 65% है।",
        
        "मेरे पास ₹1,50,000 हैं।",
        "समय है 14:30।",
        "GST दर 18% है।",
        "मुझे ₹2500.50 मिले।",
        "सर्वर आईपी 192.168.32.111 है।",
    ]
    
    print("Enhanced Hindi Normalization Test Cases (FIXED):")
    print("=" * 80)
    for test in test_cases:
        normalized = normalizer.normalize(test)
        print(f"Original:    {test}")
        print(f"Normalized:  {normalized}")
        print("-" * 80)


if __name__ == "__main__":
    test_hindi_normalizer()
