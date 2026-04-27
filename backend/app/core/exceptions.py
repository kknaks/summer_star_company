"""도메인 예외. router에서 HTTPException으로 변환."""


class DomainError(Exception):
    """모든 도메인 예외의 베이스."""


class UserNotFoundError(DomainError):
    pass


class CardNotFoundError(DomainError):
    pass


class CardUidConflictError(DomainError):
    """이미 등록된 UID로 새 카드 생성 시도."""


class ReaderUnavailableError(DomainError):
    """등록 리더(#2)가 연결되지 않았거나 통신 실패."""


class CardScanTimeoutError(DomainError):
    """등록 리더에 timeout 동안 카드 안 찍힘."""
