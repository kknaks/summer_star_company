// Minimal PWA service worker — installability 충족용 (network-first pass-through).
// 본격 오프라인은 후순위 (1인 admin 항상 온라인 전제).

self.addEventListener("install", () => {
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(self.clients.claim());
});

self.addEventListener("fetch", () => {
  // pass-through. Chrome의 PWA 설치 프롬프트는 fetch 리스너 존재만 요구.
});
