# Access Log (출입 기록)

리더기에 카드가 찍힐 때마다 남는 이벤트 로그. 성공/실패 모두 기록. 출퇴근 통계의 원천 데이터.

## 속성 (초안)

| 필드 | 타입 | 비고 |
|---|---|---|
| id | bigserial | PK (시간순 자연 정렬용) |
| occurred_at | timestamptz | 카드 찍힌 시각 (Pi 에이전트 발생 시각 기준) |
| received_at | timestamptz | 백엔드 수신 시각 (네트워크 단절 후 재전송 추적용) |
| uid | text | 찍힌 카드의 UID (정규화된 대문자 hex). [[card]]가 미등록이어도 raw로 보존 |
| card_id | uuid | FK → [[card]]. 미등록 카드면 NULL |
| user_id | uuid | FK → [[user]]. 미등록 카드면 NULL |
| allowed | bool | 출입 허용 여부 (true=통과, false=거부) |

> `occurred_at` ≠ `received_at`인 경우 = 네트워크 단절로 Pi 로컬 큐에 쌓였다 재전송된 케이스. 출퇴근 통계는 무조건 `occurred_at` 기준.

## 관계

- N [[access-log]] : 1 [[card]] (NULL 가능)
- N [[access-log]] : 1 [[user]] (NULL 가능)

## 출퇴근 해석

리더기 1대 + 단방향 감지라 "출근/퇴근" 구분은 카드 단에선 불가능. **로그는 raw event만 저장**하고, 해석은 조회 레이어에서.

해석 규칙:
- "하루"의 경계: **KST 04:00 컷오프** (밤샘 근무 다음날 아침까지 같은 날로 묶기 위해)
- 하루 첫 찍힘 = **출근**
- 하루 마지막 찍힘 = **퇴근**
- 중간 찍힘은 raw 로그로 보존만, 출퇴근 통계엔 미반영
- 처리 위치: **앱 레이어** (백엔드 또는 [[../spec/admin-web]]). DB 뷰로 안 만듦. 원본 로그는 변형 X

## 거부 처리

카드 2장 운영 스코프 — 거부 사유 분류는 오버엔지니어링. 그냥 `allowed=false`로만 기록.
조회할 때 [[card]] 상태 / [[user]] 상태 join으로 사후 추론 가능.

## 인덱스 (초안)

- `(occurred_at DESC)` — 최근 로그 조회
- `(user_id, occurred_at DESC)` — 특정 사용자 출퇴근 조회
- `(uid, occurred_at DESC)` — UID로 추적 (미등록 카드 추적 포함)

## 보존

개인 사무실 스코프 — 굳이 만료 정책 안 둬도 양 부담 없음. 직원 5명 × 하루 4번 × 365일 = 7300건/년. 그냥 쌓아둠.

## 참고

- [[../architecture/overview|아키텍처 개요]]
- [[user]] / [[card]]
- 네트워크 단절 시 로컬 큐 동작은 [[../architecture/overview]] 참고
