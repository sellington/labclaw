# Design System — LabClaw Ecosystem

**Version:** 0.2.0
**Updated:** 2026-03-19
**Scope:** Shared tokens and principles inherited by all LabClaw products.

---

## Ecosystem Overview

LabClaw is a Physical AI platform for science laboratories. This document defines the shared visual DNA — colors, typography, spacing, motion — that all products inherit. Each product defines its own personality (accent color, roundness, layout) in its own `.stitch/DESIGN.md`.

### Product Hierarchy

```
LabClaw (ecosystem brand)
├── lab-manager        — Generic lab inventory/document SaaS (any lab)
│   └── shenlab-manager — Shen Lab deployment instance (branding override only)
├── dollar-lab         — $100 AI Neuroscientist research demo
├── labclaw-website    — Marketing/investor website
├── labwork-web        — Web-based AI workspace for scientists
└── labwork-desktop    — Desktop Electron AI workspace
```

### Branding Rules

| Brand | Where Used | Never Used In |
|-------|-----------|---------------|
| **LabClaw** | labclaw-website, labclaw core, ecosystem docs | — |
| **Lab Manager** | lab-manager UI (generic, white-label) | dollar-lab, labclaw-website |
| **Shen Lab** | shenlab-manager ONLY | lab-manager generic, dollar-lab, anywhere else |
| **dollar-lab** | dollar-lab demo/research content | lab-manager, labclaw-website |
| **Labwork** | labwork-web, labwork-desktop | lab-manager, dollar-lab |

### Stitch Projects

| Product | Project ID | Screens |
|---------|-----------|---------|
| lab-manager UI | `11370887761312061505` | 24 (Desktop + Mobile) |
| dollar-lab VC Demo | `11446858989234563851` | 11 (Desktop) |

---

## Aesthetic Direction

- **Direction:** Scientific Precision — Clean, high-contrast dark UI that conveys data reliability and technical authority.
- **Decoration:** Intentional — Subtle grain or gradient texture on surfaces. No flat-solid boredom, no pattern-overload.
- **Mood:** "This tool handles my data carefully." Professional without being cold. Precise without being sterile.
- **Dark mode:** Default for all products. Light mode: invert surface/text roles, reduce primary saturation by 15%.

---

## Shared Tokens (Core DNA)

All products inherit these. Product-level DESIGN.md files override accent color, roundness, and layout only.

### Palette

| Role | Token | Hex | HSL | Usage |
|------|-------|-----|-----|-------|
| Background | `--background` | `#0B0B14` | 254 25% 5% | Page/app background |
| Surface 1 | `--card` | `#12121E` | 254 30% 10% | Cards, panels |
| Surface 2 | `--popover` | `#1A1A2E` | 254 30% 13% | Popovers, elevated |
| Surface 3 | `--muted` | `#242438` | 254 25% 16% | Hover state, table headers |
| Text Primary | `--foreground` | `#F0F0F5` | 250 20% 94% | Headlines, body |
| Text Muted | `--muted-foreground` | `#8E8EA0` | 250 10% 59% | Secondary text |
| Text Ghost | — | `#5A5A6E` | — | Disabled, fine print |
| Border | `--border` | `#2A2A3E` | 254 25% 20% | Dividers, card borders |
| Destructive | `--destructive` | `#FF6B6B` | 0 100% 71% | Errors, danger |
| Warning | — | `#FFB84D` | — | Alerts, caution |
| Info | — | `#5B8DEF` | — | Informational |

### Semantic Colors (product-defined)

These are set per-product in their own DESIGN.md:

| Role | Token | Default | Override per product |
|------|-------|---------|---------------------|
| Primary | `--primary` | `#6C5CE7` (Indigo Violet) | Yes |
| Accent | `--accent` | `#00D4AA` (Vivid Teal) | Yes |

### Typography

| Role | Font | Weights | Notes |
|------|------|---------|-------|
| Display/Hero | Plus Jakarta Sans | 700, 800 | Modern geometric, warmer than Inter |
| Body/UI | DM Sans | 400, 500, 600 | Highly readable at small sizes |
| Code/Mono | JetBrains Mono | 400, 700 | Terminal output, data, API responses |

Stitch always renders as Inter (ignores font prompts). Font customization happens in implementation layer only.

**Scale:**

| Level | Size | Weight | Line Height | Usage |
|-------|------|--------|-------------|-------|
| Display | 48px | 800 | 1.1 | Hero headlines |
| H1 | 36px | 700 | 1.2 | Section headers |
| H2 | 28px | 600 | 1.3 | Subsection headers |
| H3 | 22px | 600 | 1.4 | Card titles |
| Body | 16px | 400 | 1.6 | Main content |
| Caption | 14px | 500 | 1.5 | Labels, metadata |
| Small | 12px | 400 | 1.4 | Badges, tags |

### Spacing

- **Base unit:** 4px
- **Scale:** 2(8px) xs(12px) sm(16px) md(24px) lg(32px) xl(48px) 2xl(64px) 3xl(96px)

### Layout

- **Grid:** 12-column. Breakpoints: sm(640), md(768), lg(1024), xl(1280), 2xl(1400).
- **Border radius scale:**
  - sm: 4px — Inputs, badges
  - md: 8px — Buttons, form controls
  - lg: 12px — Cards, panels, modals
  - xl: 16px — Hero sections, large containers
  - full: 9999px — Pills, avatars

### Motion

- **Approach:** Minimal-functional. Transitions aid comprehension, not decoration.
- **Easing:** enter(ease-out), exit(ease-in), move(ease-in-out)
- **Duration:** micro(50-100ms) short(150-250ms) medium(250-400ms)

### Component Patterns

- **Buttons:** md radius (8px). Primary = bg-primary. Secondary = border. Ghost = transparent.
- **Cards:** lg radius (12px). Surface-1 bg, 1px border. Soft shadow on hover.
- **Inputs:** sm radius (4px). Surface-2 bg, focus ring = primary.
- **Tables:** No rounded corners. Alternating rows. Sticky header with Surface-3.
- **Sidebar:** Full-height, Surface-1, 240px. Active item = primary accent.

---

## Implementation Reference

### CSS Variables (shadcn/ui)

```css
:root {
  --background: 254 25% 5%;
  --card: 254 30% 10%;
  --popover: 254 30% 13%;
  --muted: 254 25% 16%;
  --foreground: 250 20% 94%;
  --muted-foreground: 250 10% 59%;
  --primary: 250 80% 63%;          /* Override per product */
  --primary-foreground: 0 0% 100%;
  --accent: 168 100% 42%;          /* Override per product */
  --accent-foreground: 0 0% 100%;
  --destructive: 0 100% 71%;
  --destructive-foreground: 0 0% 100%;
  --border: 254 25% 20%;
  --input: 254 25% 20%;
  --ring: 250 80% 63%;
  --radius: 0.5rem;
}
```

### Tailwind Extension

```js
extend: {
  colors: {
    void: '#0B0B14',
    surface: { 1: '#12121E', 2: '#1A1A2E', 3: '#242438' },
    line: '#2A2A3E',
    'text-primary': '#F0F0F5',
    'text-muted': '#8E8EA0',
    'text-ghost': '#5A5A6E',
    danger: '#FF6B6B',
    warning: '#FFB84D',
    info: '#5B8DEF',
  },
  fontFamily: {
    display: ['"Plus Jakarta Sans"', 'sans-serif'],
    body: ['"DM Sans"', 'sans-serif'],
    mono: ['"JetBrains Mono"', 'monospace'],
  },
  borderRadius: { sm: '4px', md: '8px', lg: '12px', xl: '16px' },
}
```

Note: `primary` and `accent` are omitted from Tailwind extension — they come from CSS variables per-product.

---

## Stitch-to-Production Pipeline

Stitch = design mockup tool (like Figma). HTML download only, no component export.

```
1. DESIGN IN STITCH           → generate_screen_from_text / edit_screens
2. DOWNLOAD HTML              → get_screen → htmlCode.downloadUrl
3. REFERENCE, DON'T COPY      → Use HTML as visual spec, not deployment artifact
4. IMPLEMENT WITH shadcn/ui   → Map to React components, apply CSS variables
5. BUILD & DEPLOY             → Vite → Cloudflare Pages / Vercel
```

Direct HTML deployment is acceptable for VC demos and prototypes only.

---

## Decisions Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-03-19 | v0.2.0: Split into root + project-level DESIGN.md | Root = shared DNA, project-level = personality overrides. Prevents token conflicts. |
| 2026-03-19 | "Shen Lab" branding scoped to shenlab-manager only | Generic lab-manager must be white-label for any lab. Instance branding in deployment config. |
| 2026-03-19 | Primary #6C5CE7 as ecosystem default | Midpoint between original purple (#895af6) and blue (#5a89f6). Products can override. |
| 2026-03-19 | Font stack: Plus Jakarta Sans + DM Sans | Stitch ignores fonts; applied in implementation layer only. |
| 2026-03-19 | shadcn/ui as component library | Already in labclaw-website. CSS variable theming maps directly to tokens. |
