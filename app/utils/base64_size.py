import re

def estimate_base64_decoded_bytes(b64: str) -> int:
    """
    Estimate the number of decoded bytes for a base64 string without decoding.
    Strips whitespace and removes optional data:...,... prefix.
    Always returns an int, never throws; if input is not a string, returns 0.
    """
    if not isinstance(b64, str):
        return 0
    s = b64.strip()
    # Remove data URL prefix if present
    if s.startswith("data:"):
        comma = s.find(",")
        if comma != -1:
            s = s[comma+1:]
    import re
    s = re.sub(r"\s+", "", s)
    padding = s.count('=')
    return max(0, (len(s) * 3 // 4) - padding)
