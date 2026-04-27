---
name: code-convention
description: 코드 작성 전 어느 컨벤션을 적용할지 안내. docs/conventions/ 진입점.
---

# Code Convention Skill

작업 중인 파일 경로에 따라 적용할 컨벤션 문서를 선택해 읽어라.

| 파일 위치 | 적용 문서 |
|---|---|
| `backend/**`, `agent/**` | [[../../../docs/conventions/python]] + [[../../../docs/conventions/common]] |
| `admin/**` | [[../../../docs/conventions/typescript]] + [[../../../docs/conventions/common]] |
| 그 외 (docs, .claude 등) | [[../../../docs/conventions/common]] |

레이어 규칙(특히 백엔드 schema → router → dto → service → repo → db)은 컨벤션 문서가 SSOT.

> 본문 추후 보강.
