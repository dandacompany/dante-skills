# `app/globals.css` — 그대로 복사

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@import url('https://fonts.googleapis.com/css2?family=Nanum+Myeongjo:wght@400;700;800&family=Noto+Serif+KR:wght@400;500;600;700&family=Pretendard+Variable&display=swap');

:root {
  --bg-canvas: #F7F2E6;
  --bg-surface: #FCF9F0;
  --bg-subtle: #EDE7D7;
  --text-primary: #1a1a1a;
  --text-secondary: #3a3a3a;
  --text-muted: #6a6a6a;
  --text-meta: #8B6F47;
  --accent-brand: #A0522D;
  --accent-alt: #435B6C;
  --link-strong: #3E5E75;
  --highlight: #EBC65B;
  --border: rgba(26, 26, 26, 0.12);
  --border-strong: rgba(26, 26, 26, 0.24);
}

html, body {
  background: var(--bg-canvas);
  color: var(--text-primary);
  font-family: 'Noto Serif KR', serif;
  font-feature-settings: 'kern' 1, 'liga' 1;
  -webkit-font-smoothing: antialiased;
}

.type-display { font-family: 'Nanum Myeongjo', 'Noto Serif KR', serif; font-weight: 800; font-size: clamp(48px, 6vw, 96px); line-height: 1.05; letter-spacing: -0.02em; }
.type-hero    { font-family: 'Nanum Myeongjo', 'Noto Serif KR', serif; font-weight: 800; font-size: clamp(40px, 5vw, 72px); line-height: 1.1;  letter-spacing: -0.015em; }
.type-h1      { font-family: 'Nanum Myeongjo', 'Noto Serif KR', serif; font-weight: 700; font-size: clamp(32px, 3.4vw, 48px); line-height: 1.2; }
.type-h2      { font-family: 'Noto Serif KR', serif; font-weight: 700; font-size: clamp(24px, 2.4vw, 32px); line-height: 1.25; }
.type-h3      { font-family: 'Noto Serif KR', serif; font-weight: 700; font-size: 20px; line-height: 1.3; }
.type-body    { font-family: 'Noto Serif KR', serif; font-weight: 400; font-size: 16px; line-height: 1.75; }
.type-small   { font-family: 'Noto Serif KR', serif; font-weight: 400; font-size: 13px; line-height: 1.6; color: var(--text-muted); }
.type-meta    { font-family: 'Pretendard Variable', sans-serif; font-weight: 700; font-size: 11px; letter-spacing: 0.16em; text-transform: uppercase; color: var(--text-meta); }
.num-tabular  { font-family: 'Pretendard Variable', sans-serif; font-variant-numeric: tabular-nums; }

.ledger-hairline {
  border-top: 1px solid var(--border);
  border-bottom: 1px solid var(--border);
  padding: 4px 0;
}

.edge-mark {
  position: absolute;
  font-family: 'Pretendard Variable', sans-serif;
  font-weight: 700;
  font-size: 10px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--text-meta);
}

.rust-stripe { position: relative; }
.rust-stripe::before {
  content: '';
  position: absolute;
  left: 0; top: 0; bottom: 0;
  width: 4px;
  background: var(--accent-brand);
}

.dl-card {
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 24px;
  transition: border-color 0.18s, box-shadow 0.18s;
}
.dl-card:hover {
  border-color: var(--border-strong);
  box-shadow: 0 12px 32px -16px rgba(160, 82, 45, 0.18);
}

.dl-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border-radius: 2px;
  font-family: 'Pretendard Variable', sans-serif;
  font-weight: 700;
  font-size: 10px;
  letter-spacing: 0.16em;
  text-transform: uppercase;
}
.dl-badge-rust  { background: rgba(160, 82, 45, 0.12); color: var(--accent-brand); }
.dl-badge-slate { background: rgba(67, 91, 108, 0.12); color: var(--accent-alt); }
.dl-badge-amber { background: rgba(235, 198, 91, 0.20); color: #6E5318; }

.dl-mark {
  background: linear-gradient(180deg, transparent 60%, var(--highlight) 60%);
  padding: 0 2px;
}
```
