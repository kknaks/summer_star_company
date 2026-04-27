import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";

const eslintConfig = defineConfig([
  ...nextVitals,
  ...nextTs,
  // 1인 admin 스코프 — 너무 엄격한 React 19 / Next 16 룰 일부 완화
  {
    rules: {
      // useEffect 안에서 setState 호출 막는 룰 — 우리는 페이지당 1-2회 fetch가 전부라 성능 무관
      "react-hooks/set-state-in-effect": "off",
    },
  },
  globalIgnores([
    ".next/**",
    "out/**",
    "build/**",
    "next-env.d.ts",
  ]),
]);

export default eslintConfig;
