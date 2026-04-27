---
name: doc-consistency
description: 문서 정합성 / SSOT 위반 검사 절차. /check-docs, /check-ssot, pre-commit 훅에서 호출.
---

# Doc Consistency Skill

문서 정합성 audit 절차.

검사 항목 (TBD):
1. **위키링크 깨짐 여부** — 모든 `[[name]]` 실제 파일 존재?
2. **MAP 등록 여부** — `docs/` 하위 모든 .md가 `docs/MAP.md`에 등록되어 있는지
3. **SSOT 위반** — 같은 결정이 여러 문서에 중복?
4. **결정 vs 메모리 정합** — 메모리 내용이 현재 docs와 일치?
5. **요약(overview) vs 상세(SSOT)** — overview가 디테일을 inline으로 갖고 있지 않은지

검색 패턴 예시:
```bash
grep -rn "sqlite\|sessions\|관리형\|세션 쿠키" docs/   # 옛 결정 잔재
grep -rn "결정사항.*변경.*갱신" docs/                  # propagate 표현(옛 컨벤션)
```

> 본문 추후 보강.
