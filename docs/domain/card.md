# Card (NFC 카드)

물리적 NFC 카드 한 장. UID로 고유 식별되며 [[user]] 한 명에 귀속.

## 속성 (초안)

| 필드 | 타입 | 비고 |
|---|---|---|
| id | uuid | PK |
| uid | text | NFC UID 대문자 hex 문자열, 구분자 없음 (예: `59FAC303`). UNIQUE. 저장 전 정규화 필수 |
| user_id | uuid | FK → [[user]] |
| label | text | 사용자가 구분용으로 붙이는 이름 (예: "메인", "예비") |
| active | bool | 분실/회수 시 false |
| registered_at | timestamptz | 카드 등록 시각 |
| created_at | timestamptz | |
| updated_at | timestamptz | |

> ACR122U는 보통 4바이트 UID 반환 (Mifare Classic 등). 7바이트 카드도 있으니 길이 가변 문자열로 둠.

## 관계

- N [[card]] : 1 [[user]] — 한 사용자가 여러 카드 보유 가능 (예비카드)
- 1 [[card]] : N [[access-log]] — 각 출입 기록은 어떤 카드로 찍었는지 남김

## 등록 흐름

리더기 2대 구조라 등록은 **등록용 리더(#2)에서 pull 방식**으로 이뤄짐 (출입용 Pi와 무관).

1. admin이 [[../spec/admin-web]] 사용자 상세 페이지에서 "카드 추가" 클릭
2. 웹 → `POST /api/cards/scan` (백엔드)
3. 백엔드가 집 서버에 직결된 등록 리더(#2)에서 카드 한 장 읽음 (timeout 30초)
   - 30초 내 안 찍으면 `408 Timeout` 응답
   - UID 캡처되면 `200 { uid }` 응답
4. 웹: UID 표시 + 라벨 입력
5. admin이 저장 클릭 → `POST /api/cards { uid, user_id, label }`
6. 백엔드: UID 정규화 → UNIQUE 검사 → `cards` INSERT (`active=true`)

> UID가 이미 등록되어 있으면 6단계에서 409로 거부.

## UID 충돌 / 미등록 카드

- 미등록 UID 카드 찍힘 → 출입 거부 + [[access-log]]에 `result=denied`, `user_id=NULL`로 기록
- 같은 UID가 다른 카드로 또 등록되는 건 막아야 함 (UNIQUE 제약)

## 분실/회수

- 분실: `active = false`로 soft delete. 기존 [[access-log]] 보존을 위해 row 자체는 삭제 X
- 회수 후 재발급: 같은 사용자에게 새 카드 새 UID로 발급. 이전 카드 row는 inactive 유지

## 정책

- **UID 정규화**: 입력 받은 UID는 항상 대문자 hex, 구분자 제거 후 저장 (`"59:fa:c3:03"` → `"59FAC303"`). 백엔드 입력 단에서 정규화 함수 거치게 강제
- **카드 매수 제한**: 없음 (한 사용자가 N장 자유롭게)

## 참고

- [[../architecture/overview|아키텍처 개요]]
- [[user]] — 카드 소유자
- [[access-log]] — 출입 기록
