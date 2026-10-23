"""
Enhanced English text normalization for Indian context (en-IN).
Combines features from both normalizers for better coverage.
"""
import re
from functools import lru_cache
try:
    from .base_normalizer import BaseNormalizer
except ModuleNotFoundError:
    from base_normalizer import BaseNormalizer

# Constants for English normalization
MONTHS = {
    "01": "January", "1": "January",
    "02": "February", "2": "February",
    "03": "March", "3": "March",
    "04": "April", "4": "April",
    "05": "May", "5": "May",
    "06": "June", "6": "June",
    "07": "July", "7": "July",
    "08": "August", "8": "August",
    "09": "September", "9": "September",
    "10": "October", "11": "November", "12": "December"
}

ACRONYMS = {
    "RBI", "IRCTC", "UPI", "NEFT", "IMPS", "PAN", "GST", "OTP", "KYC", "IFSC",
    "EMI", "ATM", "HRA", "PF", "ESI", "SIP", "AMC", "NPS", "UIDAI", "AADHAAR",
    "AI", "ML", "API", "URL", "HTML", "CSS", "IT"
}

COMMON_ABBREVIATIONS = {
    r"\bPvt\.?\s*Ltd\.?\b": "Private Limited",
    r"\bGovt\.?\b": "Government",
    r"\bDept\.?\b": "Department",
    # r"\bNo\.?\b": "Number",
    r"\bRd\.?\b": "Road",
    r"\bSt\.?\b": "Street",
    r"\bFlr\.?\b": "Floor",
    r"\bMr\.": "Mister",
    r"\bMrs\.": "Misses",
    r"\bMs\.": "Miss",
    r"\bDr\.": "Doctor",
    r"\bAr\.": "Architect",
    r"\bProf\.": "Professor",
    r"\bInc\.": "Incorporated",
    r"\bLtd\.": "Limited",
    r"\bCo\.": "Company",
}

UNITS = {
    r"\b(\d+(?:\.\d+)?)\s*km\b": ("kilometre", "kilometres"),
    r"\b(\d+(?:\.\d+)?)\s*kg\b": ("kilogram", "kilograms"),
    r"\b(\d+(?:\.\d+)?)\s*g\b": ("gram", "grams"),
    r"\b(\d+(?:\.\d+)?)\s*ml\b": ("millilitre", "millilitres"),
    r"\b(\d+(?:\.\d+)?)\s*l\b": ("litre", "litres"),
    r"\b(\d+(?:\.\d+)?)\s*cm\b": ("centimetre", "centimetres"),
    r"\b(\d+(?:\.\d+)?)\s*mm\b": ("millimetre", "millimetres"),
    r"\b(\d+(?:\.\d+)?)\s*m\b": ("metre", "metres"),
    r"\b(\d+(?:\.\d+)?)\s*ft\b": ("foot", "feet"),
    r"\b(\d+(?:\.\d+)?)\s*sq\.?ft\b": ("square foot", "square feet"),
    r"\b(\d+(?:\.\d+)?)\s*km/h\b": ("kilometre per hour", "kilometres per hour"),
    r"\b(\d+(?:\.\d+)?)\s*mph\b": ("mile per hour", "miles per hour"),
    r"\b(\d+(?:\.\d+)?)\s*V\b": ("volt", "volts"),
    r"\b(\d+(?:\.\d+)?)\s*kWh\b": ("kilowatt hour", "kilowatt hours"),
    r"\b(\d+(?:\.\d+)?)\s*min\b": ("minute", "minutes"),
    r"\b(\d+(?:\.\d+)?)\s*sec\b": ("second", "seconds"),
}

DIGITS = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]

# English ordinal exceptions for better conversion
ORDINAL_EXCEPTIONS = {
    "one": "first", "two": "second", "three": "third", "four": "fourth",
    "five": "fifth", "six": "sixth", "seven": "seventh", "eight": "eighth",
    "nine": "ninth", "ten": "tenth", "eleven": "eleventh", "twelve": "twelfth",
    "thirteen": "thirteenth", "fourteen": "fourteenth", "fifteen": "fifteenth",
    "sixteen": "sixteenth", "seventeen": "seventeenth", "eighteen": "eighteenth",
    "nineteen": "nineteenth", "twenty": "twentieth", "thirty": "thirtieth",
    "forty": "fortieth", "fifty": "fiftieth", "sixty": "sixtieth",
    "seventy": "seventieth", "eighty": "eightieth", "ninety": "ninetieth",
    "hundred": "hundredth", "thousand": "thousandth", "lakh": "lakhth",
    "crore": "croreth", "million": "millionth", "billion": "billionth"
}


@lru_cache(maxsize=4096)
def int_to_words_indian(n: int) -> str:
    """Convert integer to words using Indian numbering system (thousand, lakh, crore)."""
    if n == 0:
        return "zero"
    
    if n < 0:
        return f"minus {int_to_words_indian(-n)}"
    
    ones = ["", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine",
            "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen",
            "seventeen", "eighteen", "nineteen"]
    tens = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]

    def two_digits(x):
        if x < 20:
            return ones[x]
        t, o = divmod(x, 10)
        return tens[t] + ("" if o == 0 else " " + ones[o])

    def three_digits(x):
        h, rem = divmod(x, 100)
        s = ""
        if h > 0:
            s += ones[h] + " hundred"
            if rem > 0:
                s += " and " if rem < 100 else " "
        if rem > 0:
            s += two_digits(rem)
        return s

    parts = []
    crore, n = divmod(n, 10_000_000)
    lakh, n = divmod(n, 100_000)
    thousand, n = divmod(n, 1_000)
    hundred = n

    if crore:
        parts.append(int_to_words_indian(crore) + " crore")
    if lakh:
        parts.append(two_digits(lakh) + " lakh")
    if thousand:
        parts.append(two_digits(thousand) + " thousand")
    if hundred:
        parts.append(three_digits(hundred))
    
    return " ".join(parts).strip()


@lru_cache(maxsize=2048)
def float_to_words(number_str: str) -> str:
    """Convert float strings to words (e.g., '12.5' → 'twelve point five')."""
    number_str = str(number_str).strip()
    
    if not number_str:
        return ""
    
    # Handle sign
    sign = ""
    if number_str[0] in "+-":
        sign = "minus " if number_str[0] == "-" else "plus "
        number_str = number_str[1:]
    
    # If no decimal point, treat as integer
    if "." not in number_str:
        try:
            return f"{sign}{int_to_words_indian(int(number_str))}".strip()
        except ValueError:
            return f"{sign}{number_str}".strip()
    
    # Split into integer and decimal parts
    integer_part, decimal_part = number_str.split(".", 1)
    integer_part = integer_part or "0"
    
    try:
        integer_words = int_to_words_indian(int(integer_part))
    except ValueError:
        integer_words = integer_part
    
    # Handle decimal digits
    decimal_digits = [d for d in decimal_part if d.isdigit()]
    if not decimal_digits or all(d == "0" for d in decimal_digits):
        return f"{sign}{integer_words}".strip()
    
    decimal_words = " ".join(DIGITS[int(d)] for d in decimal_digits)
    return f"{sign}{integer_words} point {decimal_words}".strip()


@lru_cache(maxsize=2048)
def ordinal_to_words(n: int) -> str:
    """Convert number to ordinal words (1 → first, 2 → second, etc.)."""
    if n < 0:
        return f"minus {ordinal_to_words(-n)}"
    
    cardinal = int_to_words_indian(n)
    if not cardinal:
        return str(n)
    
    parts = cardinal.split()
    last_word = parts[-1]
    
    # Check for exception mappings
    replacement = ORDINAL_EXCEPTIONS.get(last_word)
    if replacement:
        parts[-1] = replacement
        return " ".join(parts)
    
    # Apply standard rules
    if last_word.endswith("y"):
        parts[-1] = f"{last_word[:-1]}ieth"
    else:
        parts[-1] = f"{last_word}th"
    
    return " ".join(parts)


def say_digits(num: str) -> str:
    """Convert numeric string to spoken digits."""
    return " ".join(DIGITS[int(d)] for d in num if d.isdigit())


def spell_alphanumeric(text: str) -> str:
    """Spell out alphanumeric codes letter by letter and digit by digit."""
    result = []
    for char in text:
        if char.isalpha():
            result.append(char.upper())
        elif char.isdigit():
            result.append(DIGITS[int(char)])
        else:
            result.append(char)
    return " ".join(result)


class EnglishNormalizer(BaseNormalizer):
    """Enhanced English text normalizer for Indian context."""
    
    def __init__(self, locale: str = "en-IN", read_urls_as: str = "verbatim",
                 use_colloquial: bool = True):
        self.read_urls_as = read_urls_as
        # Accepted for signature parity with HindiNormalizer / create_normalizer;
        # English number-to-words has no colloquial variants, so it's stored but unused.
        self.use_colloquial = use_colloquial
        super().__init__(locale)
    
    def _compile_patterns(self):
        """Compile regex patterns for English normalization."""
        # Currency patterns
        self._re_currency = re.compile(r"(₹)\s?([0-9][0-9,]*)(?:\.([0-9]{1,2}))?")
        self._re_usd = re.compile(r"\bRs\.?\s*([0-9][0-9,]*)(?:\.([0-9]{1,2}))?\b", re.IGNORECASE)
        self._re_dollar = re.compile(r"\$\s?([0-9][0-9,]*(?:\.\d{1,2})?)")
        
        # Contact patterns
        self._re_phone = re.compile(r"(?:\+91[-\s]?|0)?([6-9]\d{9})\b")
        self._re_email = re.compile(r"\b([A-Za-z0-9._%+-]+)@([A-Za-z0-9.-]+\.[A-Za-z]{2,})\b")
        
        # Date/Time patterns
        self._re_date_dmy = re.compile(r"\b([0-3]?\d)[/.-]([0-1]?\d)[/.-](\d{2,4})\b")
        self._re_date_iso = re.compile(r"\b(\d{4})[-/]([0-1]?\d)[-/]([0-3]?\d)\b")
        self._re_time_24h = re.compile(
            r"\b([01]?\d|2[0-3]):([0-5]\d)(?::([0-5]\d))?\s*(AM|PM)?\b", 
            re.IGNORECASE
        )
        
        # URL and web patterns
        self._re_url = re.compile(
            r"\bhttps?://[^\s]+|\bwww\.[^\s]+\b|\b[\w-]+\.[a-z]{2,}\b", 
            re.IGNORECASE
        )
        
        # Number patterns
        self._re_percent = re.compile(r"(\d+(?:\.\d+)?)\s?%")
        self._re_ordinal = re.compile(r"\b(\d+)(st|nd|rd|th)\b", re.IGNORECASE)
        self._re_dotted_number = re.compile(r"\b\d+(?:\.\d+){2,}\b")
        
        # Text patterns
        self._re_acronym = re.compile(r"\b([A-Z]{2,})\b")
        self._re_alphanumeric = re.compile(r"\b([A-Z]+\d+)\b")
        self._re_at_symbol = re.compile(r"@")
    
    def normalize(self, text: str) -> str:
        """Normalize English text for TTS."""
        if not text or not text.strip():
            return text

        text = self._normalize_dso(text)
        text = self._normalize_whitespace(text)
        text = self._normalize_quotes(text)

        # Apply abbreviations
        for pat, repl in COMMON_ABBREVIATIONS.items():
            text = re.sub(pat, repl, text, flags=re.IGNORECASE)

        # Apply transformations in order (order matters!)
        text = self._expand_units(text)
        text = self._expand_currency(text)
        text = self._expand_percent(text)
        text = self._expand_dates_times(text)
        text = self._expand_phones(text)
        text = self._expand_alphanumeric_codes(text)
        text = self._expand_emails_urls(text)
        text = self._expand_dotted_numbers(text)
        text = self._expand_ordinals(text)
        text = self._expand_at_symbol(text)
        text = self._expand_acronyms(text)
        text = self._expand_numbers(text)
        text = self._normalize_whitespace(text)

        return text.strip()
    
    def _expand_currency(self, s: str) -> str:
        """Expand currency symbols to words."""
        # Handle ₹ symbol
        def repl_rupee(m):
            _, integer, paise = m.groups()
            integer_clean = integer.replace(",", "")
            try:
                rupee_value = int(integer_clean)
            except ValueError:
                return m.group(0)
            
            spoken_rupees = int_to_words_indian(rupee_value)
            rupee_word = "rupee" if rupee_value == 1 else "rupees"
            result = f"{spoken_rupees} {rupee_word}"
            
            if paise and paise.strip("0"):
                paise_value = int(paise.lstrip("0") or "0")
                spoken_paise = int_to_words_indian(paise_value)
                result += f" and {spoken_paise} paise"
            
            return result

        s = self._re_currency.sub(repl_rupee, s)

        # Handle Rs. notation
        def repl_rs(m):
            integer, paise = m.groups()
            integer_clean = integer.replace(",", "")
            try:
                rupee_value = int(integer_clean)
            except ValueError:
                return m.group(0)
            
            spoken_rupees = int_to_words_indian(rupee_value)
            rupee_word = "rupee" if rupee_value == 1 else "rupees"
            result = f"{spoken_rupees} {rupee_word}"
            
            if paise and paise.strip("0"):
                paise_value = int(paise.lstrip("0") or "0")
                spoken_paise = int_to_words_indian(paise_value)
                result += f" and {spoken_paise} paise"
            
            return result

        s = self._re_usd.sub(repl_rs, s)
        
        # Handle $ symbol
        def repl_dollar(m):
            num_str = m.group(1).replace(",", "")
            if "." in num_str:
                words = float_to_words(num_str)
            else:
                words = int_to_words_indian(int(num_str))
            return f"{words} dollars"
        
        s = self._re_dollar.sub(repl_dollar, s)
        
        return s
    
    def _expand_percent(self, s: str) -> str:
        """Expand percentages to words."""
        def repl(m):
            num = m.group(1)
            if "." in num:
                num_words = float_to_words(num)
            else:
                num_words = int_to_words_indian(int(num))
            return f"{num_words} percent"
        return self._re_percent.sub(repl, s)
    
    def _expand_dates_times(self, s: str) -> str:
        """Expand dates and times to words."""
        # Handle DD/MM/YYYY format
        def repl_dmy(m):
            d, mth, y = m.groups()
            month = MONTHS.get(mth.lstrip("0"), mth)
            day = int(d)
            day_ordinal = ordinal_to_words(day)
            year_words = int_to_words_indian(int(y))
            return f"{day_ordinal} {month} {year_words}"
        s = self._re_date_dmy.sub(repl_dmy, s)

        # Handle YYYY-MM-DD format
        def repl_iso(m):
            y, mth, d = m.groups()
            month = MONTHS.get(mth.lstrip("0"), mth)
            day = int(d)
            day_ordinal = ordinal_to_words(day)
            year_words = int_to_words_indian(int(y))
            return f"{day_ordinal} {month} {year_words}"
        s = self._re_date_iso.sub(repl_iso, s)

        # Handle time format
        def repl_time(m):
            hh, mm, ss, ampm = m.groups()
            h = int(hh)
            minute = int(mm)
            
            if ampm:
                period = ampm.upper()
                display_hour = h if 1 <= h <= 12 else h % 12 or 12
            else:
                period = "AM" if h < 12 else "PM"
                display_hour = h if 1 <= h <= 12 else h % 12 or 12
            
            hour_words = int_to_words_indian(display_hour)
            
            if minute == 0:
                result = f"{hour_words} {period}"
            else:
                minute_words = int_to_words_indian(minute)
                result = f"{hour_words} {minute_words} {period}"
            
            return result
        s = self._re_time_24h.sub(repl_time, s)

        return s
    
    def _expand_phones(self, s: str) -> str:
        """Expand phone numbers to spoken digits."""
        return self._re_phone.sub(lambda m: say_digits(m.group(1)), s)
    
    def _expand_units(self, s: str) -> str:
        """Expand measurement units to words."""
        for pat, (sg, pl) in UNITS.items():
            rx = re.compile(pat, re.IGNORECASE)
            def repl(m):
                val_str = m.group(1)
                if "." in val_str:
                    num_words = float_to_words(val_str)
                    val = float(val_str)
                else:
                    val = int(val_str)
                    num_words = int_to_words_indian(val)
                
                unit = self.pluralize(sg, pl, val)
                return f"{num_words} {unit}"
            s = rx.sub(repl, s)
        return s
    
    def _expand_alphanumeric_codes(self, s: str) -> str:
        """Expand alphanumeric codes to spelled-out form."""
        return self._re_alphanumeric.sub(
            lambda m: spell_alphanumeric(m.group(1)), s
        )
    
    def _expand_emails_urls(self, s: str) -> str:
        """Expand emails and URLs to spoken form."""
        # Handle emails
        def repl_email(m):
            user, domain = m.groups()
            user_spoken = user.replace("_", " underscore ").replace(".", " dot ")
            domain_spoken = domain.replace(".", " dot ")
            return f"{user_spoken} at {domain_spoken}"
        s = self._re_email.sub(repl_email, s)

        # Handle URLs
        def repl_url(m):
            url = m.group(0)
            
            if self.read_urls_as == "url":
                return "URL"
            
            # Remove protocol
            stripped = re.sub(r"^https?://", "", url, flags=re.IGNORECASE)
            
            if self.read_urls_as == "domain":
                domain = stripped.split("/")[0]
                return domain.replace(".", " dot ")
            
            # verbatim mode
            return (
                stripped.replace(".", " dot ")
                .replace("/", " slash ")
                .replace("-", " dash ")
            )
        s = self._re_url.sub(repl_url, s)
        return s

    def _expand_dotted_numbers(self, s: str) -> str:
        """Expand dotted numeric sequences (e.g., IPs, versions) as digit groups."""
        def repl(m):
            parts = m.group(0).split(".")
            spoken_parts = [say_digits(part) for part in parts]
            return " dot ".join(spoken_parts)
        return self._re_dotted_number.sub(repl, s)
    
    def _expand_ordinals(self, s: str) -> str:
        """Expand ordinal numbers to words (1st → first)."""
        return self._re_ordinal.sub(
            lambda m: ordinal_to_words(int(m.group(1))), s
        )
    
    def _expand_at_symbol(self, s: str) -> str:
        """Expand @ symbol to 'at'."""
        return self._re_at_symbol.sub(" at ", s)
    
    def _expand_acronyms(self, s: str) -> str:
        """Expand known acronyms to spelled-out form."""
        def repl(m):
            tok = m.group(1)
            if tok.upper() in ACRONYMS:
                return " ".join(list(tok))
            return tok
        return self._re_acronym.sub(repl, s)
    
    def _expand_numbers(self, s: str) -> str:
        """Expand remaining numbers to words."""
        # Handle floats first
        s = re.sub(
            r"(?<![\w/])\d+\.\d+(?![\w/])",
            lambda m: float_to_words(m.group(0)),
            s,
        )
        
        # Handle integers
        s = re.sub(
            r"(?<![\w/])\d+(?![\w/])",
            lambda m: int_to_words_indian(int(m.group(0))),
            s,
        )
        
        return s


# Utility function for testing
def test_english_normalizer():
    """Test the enhanced English normalizer with various inputs."""
    normalizer = EnglishNormalizer(locale="en-IN", read_urls_as="verbatim")
    
    test_cases = [
        "I have ₹1,50,000 in my account.",
        "Today's date is 15/12/2024.",
        "The time is 14:30.",
        "My number is 9876543210.",
        "GST rate is 18%.",
        "I received ₹2500.50.",
        "This costs ₹125.",
        "It's 250 km away.",
        "My email is support@company.co.in.",
        "Visit www.example.com.",
        "This is the 1st attempt.",
        "Temperature is 37.5 degrees.",
        "Discount of 12.5% available.",
        "Meeting at 09:00 AM.",
        "Let's meet at 22:30.",
        "Bill amount is ₹350.",
        "Hey, how is it going my 33467 friends?",
        "Pay $50.75 today.",
        "The 2nd place winner gets Rs 5000.",
        "Call me @ 3:45 PM.",
        "Distance is 12.5 km from here.",
        "Weight: 75.5 kg, Height: 180 cm",
        "Email: user.name@domain.com",
        "License plate: AB1234",
        "Temperature: -5.5°C",
        "Pay Rs. 1,00,000 by 31/12/2024.",
        "Server IP: 192.168.32.111",
    ]
    
    print("Enhanced English Normalization Test Cases:")
    print("=" * 80)
    for test in test_cases:
        normalized = normalizer.normalize(test)
        print(f"Original:    {test}")
        print(f"Normalized:  {normalized}")
        print("-" * 80)


if __name__ == "__main__":
    test_english_normalizer()
