# P-07 — UI UX Specification and Design System

Baseline: 2026-10-30 · Status: **As-built draft — review pending**

Proposed responsible function: Design / Frontend. No named assignment or approval is implied.

## Current design
TWSS IVR uses a code-native TWSS SVG brand mark, React/TypeScript, semantic CSS variables, a compact Light/Dark switch and responsive cards/tables. Corporate navy is the light appearance; soft charcoal is the dark appearance. Charts use muted answer/missed/other colours and readable labels. No bitmap logo or third-party prototype is required.

## Interaction standards
Sidebar entries identify the current screen. Date controls explicitly use IST. Apply filters commits date/department/status choices; Reset affects the active tab. Each tab retains its own applied query while navigating within the workspace. Row-count preferences are stored per route. Direct URLs keep the current selection on refresh; other tabs' filter histories are held in workspace memory, not a durable cross-device account profile.

Counts and rates must name their scope. All answered calls and answered department calls are different cohorts. Missed-call subsection buttons display stable total and department counts. Unknown owner names display unavailable instead of an identifier as a name. Exact transfer edges and ring-attempt figures are not presented as established facts.

## Accessibility and responsive behaviour
Buttons and inputs have accessible labels; chart data is accompanied by text/counts. Heatmap cells identify weekday, IST hour and volume, and the day labels stay visible while scrolling. Dense tables scroll within their containers on small screens. Chrome tests cover mobile width and both appearances. These checks are not a completed accessibility conformance audit; see C-08.

## Content style
Use short business terms and active instructions. Keep operational diagnostics in Admin/developer material. Distinguish no matches from checking, missing data from zero, and current lead state from state at call time.

---
Evidence: frontend/src/themes.ts; frontend/src/themes.css; frontend/src/Brand.tsx; frontend/src/dashboard.css; frontend/src/callPatterns.css. Source baseline: `9fa87271efd5d69d2d769c519150b032df97bdf9`.

[Documentation register](../00_Documentation_Register.md)
