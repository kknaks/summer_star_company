"""NFC UID 정규화. 정책 SSOT: docs/domain/card.md."""


class InvalidUidError(ValueError):
    """UID가 hex 문자열이 아닐 때."""


def normalize_uid(raw: str) -> str:
    """공백/콜론/하이픈 제거 후 대문자화. hex 검증."""
    cleaned = raw.replace(":", "").replace("-", "").replace(" ", "").upper()
    if not cleaned:
        raise InvalidUidError("UID 비어있음")
    try:
        int(cleaned, 16)
    except ValueError as e:
        raise InvalidUidError(f"hex 아님: {raw!r}") from e
    return cleaned
