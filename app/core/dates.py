from datetime import datetime

from app.core.models import ParsedDate

# IDA Ireland press dates arrive as e.g. "24/09/2026". Day-first is an
# assumption based on the observed values and IDA being an Irish site.
_FALLBACK_FORMATS = ("%d/%m/%Y",)


def parse_date(raw: object) -> ParsedDate:
    """Parse a date string defensively. Never raises; unparseable input keeps
    its raw text so the UI can show exactly what the source said."""
    text = "" if raw is None else str(raw).strip()
    if not text:
        return ParsedDate(raw=text, value=None)

    try:
        return ParsedDate(raw=text, value=datetime.fromisoformat(text))
    except ValueError:
        pass

    for fmt in _FALLBACK_FORMATS:
        try:
            return ParsedDate(raw=text, value=datetime.strptime(text, fmt))
        except ValueError:
            continue

    return ParsedDate(raw=text, value=None)
