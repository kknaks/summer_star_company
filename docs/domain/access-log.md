# Access Log (출입 기록)

리더기에 카드가 찍힐 때마다 남는 이벤트 로그. 성공/실패 모두 기록. 출퇴근 통계의 원천 데이터.

## 속성 (초안)

| 필드 | 타입 | 비고 |
|---|---|---|
| id | bigserial | PK (시간순 자연 정렬용) |
| occurred_at | timestamptz | 카드 찍힌 시각 (Pi 에이전트 발생 시각 기준). 수동일 땐 admin이 입력한 시각 |
| received_at | timestamptz | 백엔드 수신 시각 (네트워크 단절 후 재전송 추적용). 수동일 땐 INSERT 시각 |
| uid | text NULL | 찍힌 카드의 UID (정규화된 대문자 hex). 카드 탭이면 NOT NULL, 수동 입력이면 NULL |
| card_id | uuid | FK → [[card]]. 미등록 카드/수동 입력이면 NULL |
| user_id | uuid | FK → [[user]]. 미등록 카드면 NULL, 수동 입력은 NOT NULL |
| allowed | bool | 출입 허용 여부 (true=통과, false=거부). 수동 입력은 항상 true |
| source | enum('card','manual') | 출처. 카드 탭 vs admin 수동 입력. default 'card' |
| created_by_user_id | uuid NULL | 수동일 때 작성한 admin id (audit). 카드 탭이면 NULL |
| voided | bool | soft delete 플래그. true면 통계/기본 조회에서 제외 |
| note | text NULL | 수동 입력 시 메모 (선택) |

> `occurred_at` ≠ `received_at`인 경우 = 네트워크 단절로 Pi 로컬 큐에 쌓였다 재전송된 케이스. 출퇴근 통계는 무조건 `occurred_at` 기준.

## 관계

- N [[access-log]] : 1 [[card]] (NULL 가능)
- N [[access-log]] : 1 [[user]] (NULL 가능)

## 출퇴근 해석

리더기 1대 + 단방향 감지라 "출근/퇴근" 구분은 카드 단에선 불가능. **로그는 raw event만 저장**하고, 해석은 조회 레이어에서.

### 원칙

- 직원은 출입(외출 포함)마다 탭하는 게 룰. 까먹는 누락은 항상 발생
- 모호할 때 **사업주에게 유리한 쪽**으로 해석 — 부정 방지 + 직원이 잘 찍을 인센티브
- admin 개입 0 (수동 보정 UI 안 만듦)

### 규칙

1. **하루 경계**: KST 04:00 컷오프 (밤샘 근무 다음날 아침까지 같은 날로 묶기 위해)
2. **더블탭 흡수**: 같은 카드가 30초 이내 재탭이면 1건으로 간주
3. **출근시각 = 1번째 탭, 퇴근시각 = 마지막 탭** (항상 — 앵커 고정)
4. **중간 탭 페어링**: (2,3), (4,5), (6,7) … 각 페어가 **휴게 1건** (외출→복귀)
5. **중간이 홀수면 마지막 orphan은 퇴근시각까지 휴게로 인정** — orphan은 "외출했는데 복귀를 안 찍음" → 재실 증명 실패 → 퇴근까지 휴게 처리
6. **근무시간 = (퇴근 − 출근) − ∑휴게**

### 예시

| 탭 | 출근 | 퇴근 | 휴게 | 근무 |
|---|---|---|---|---|
| 09, 18 | 09 | 18 | 0 | 9h |
| 09, 12, 13, 18 | 09 | 18 | (12,13)=1h | 8h |
| 09, 12, 13 (퇴근 누락) | 09 | 13 | orphan(12)→퇴근13 = 1h | 3h |
| 09, 12, 13, 14, 18 (중간 1개 누락) | 09 | 18 | (12,13)=1h + orphan(14)→퇴근18 = 4h | 4h |

### 원리

페어가 맞아야 "재실 증명"이 성립. 짝이 없는 외출은 "복귀를 못 찍음 = 그동안 자리에 없었다고 본다" → 퇴근까지 전부 휴게 처리. **"안 찍힌 시간은 근무로 인정하지 않는다"** 원칙.

직원이 제대로 안 찍으면 근무시간이 실제보다 짧게 잡혀서 본인이 손해 → 자연스럽게 잘 찍을 인센티브가 생김.

### 처리 위치

**앱 레이어** (백엔드 SQL 또는 [[../spec/admin-web]]). DB 뷰로 안 만듦. 원본 로그는 변형 X.

## 거부 처리

카드 2장 운영 스코프 — 거부 사유 분류는 오버엔지니어링. 그냥 `allowed=false`로만 기록.
조회할 때 [[card]] 상태 / [[user]] 상태 join으로 사후 추론 가능.

## 수동 입력 (admin CRUD)

직원이 탭을 누락한 날 admin이 사후에 보정. raw 카드 탭과 별개 row로 보존.

규칙:
- **권한**: `admin` role만 (staff 차단). [[user#권한]]
- **source 별 가능 동작**:
  - `card`: 수정 X (raw 무결성), void만 가능 (잘못 찍힌 거 무효화)
  - `manual`: 수정/void 모두 가능
- **insert** 시 자동 채움: `source='manual'`, `allowed=true`, `uid=NULL`, `card_id=NULL`, `created_by_user_id=현재 admin`
- **void(soft delete)**: `voided=true`로 플래그. row는 보존 (audit). 통계 쿼리는 `WHERE NOT voided`로 제외
- **복구**: `voided=false` 토글
- **30초 더블탭 흡수는 source 무관하게 적용** — 수동 탭이 카드 탭과 30초 이내면 합쳐짐

통계와의 관계:
- `voided=false`인 모든 row가 출퇴근 해석에 참여 (source 무관)
- 즉 admin이 누락 탭 보정하면 그 날의 페어링이 자동으로 정상화됨

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
