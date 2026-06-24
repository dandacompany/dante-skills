# Scaffold Files — 그대로 복사

## `tsconfig.json`

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "paths": { "@/*": ["./*"] },
    "plugins": [{ "name": "next" }]
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}
```

## `next.config.ts`

```ts
import type { NextConfig } from "next";
const cfg: NextConfig = {
  reactStrictMode: true,
  env: { NEXT_PUBLIC_BRAND: process.env.NEXT_PUBLIC_BRAND || "musinsa" },
};
export default cfg;
```

## `postcss.config.mjs`

```js
export default { plugins: { tailwindcss: {}, autoprefixer: {} } };
```

## `tailwind.config.ts`

```ts
import type { Config } from "tailwindcss";
const cfg: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        paper: { DEFAULT: "#F7F2E6", soft: "#EDE7D7", strong: "#FCF9F0" },
        ink: { DEFAULT: "#1a1a1a", soft: "#3a3a3a", muted: "#6a6a6a" },
        rust: { DEFAULT: "#A0522D", deep: "#7C3F22" },
        slate2: { DEFAULT: "#435B6C", deep: "#3E5E75" },
        sepia: "#8B6F47",
        amber2: "#C9A857",
        mark2: "#EBC65B",
        link: "#5B7F99",
      },
      fontFamily: {
        editorial: ['"Nanum Myeongjo"', '"Noto Serif KR"', "serif"],
        serif: ['"Noto Serif KR"', "serif"],
        sans: [
          '"Pretendard Variable"',
          '"Pretendard"',
          "-apple-system",
          "system-ui",
          "sans-serif",
        ],
        mono: ['"JetBrains Mono"', '"D2Coding"', "ui-monospace", "monospace"],
      },
      borderRadius: { none: "0", sm: "2px", md: "4px", lg: "8px" },
      boxShadow: {
        emboss:
          "inset 0 1px 0 rgba(255,255,255,0.5), 0 12px 32px -16px rgba(26,26,26,0.18)",
        card: "0 12px 32px -16px rgba(160,82,45,0.18)",
      },
    },
  },
  plugins: [],
};
export default cfg;
```
