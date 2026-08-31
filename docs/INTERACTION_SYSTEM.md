# CAREFlow Motion & Interaction Design System

## Overview
CAREFlow India incorporates an editorial-grade, low-frequency motion architecture designed to elevate analytical clarity without compromising performance or accessibility. Built on **Framer Motion** and custom CSS primitives, the interaction layer maintains the signature warm ivory aesthetic and strict data integrity standards.

---

## 1. Interaction Principles

1. **Purposeful & Non-Distracting**: Motion serves to orient the user, signal data relationships, and guide focus. Fast, jarring, or decorative animations are avoided.
2. **Editorial Spring Physics**: Motion uses tailored cubic-bezier cubic curves (`[0.16, 1, 0.3, 1]`) and low-stiffness spring mechanics to replicate physical material response.
3. **Accessibility First (`prefers-reduced-motion`)**: Every motion primitive monitors `useReducedMotion()`. When reduced motion is requested, entrance transitions degrade gracefully into zero-duration layout renders.
4. **Data-Centric Motion**: Chart elements (e.g. `ForecastChart`, `TrendChart`) utilize coordinate-aware path drawing (`pathLength`) and staggered opacity to visualize time-series evolution.

---

## 2. Motion Primitives

### `PageTransition`
* **File Path**: `frontend/src/components/motion/PageTransition.tsx`
* **Behavior**: Non-blocking route entrance wrapper that smoothly fades (`opacity: 0 -> 1`) and slides up (`y: 10px -> 0px`). Automatically bypasses animation in testing environments and reduced-motion mode.
* **Usage**: Wraps all core workspace routes (`/overview`, `/facilities`, `/regions`, `/forecast`, `/data-quality`).

### `ScrollReveal`
* **File Path**: `frontend/src/components/motion/ScrollReveal.tsx`
* **Behavior**: Intersection-observer driven reveal trigger. Animates sections as they scroll into view using directional offsets (`up`, `down`, `left`, `right`) and configurable delay orchestration.
* **Usage**: Wraps key section cards and analytical panels across the landing and operational pages.

### `TextReveal`
* **File Path**: `frontend/src/components/motion/TextReveal.tsx`
* **Behavior**: Staggered word-by-word reveal for editorial hero titles and narrative section headings.

### `InteractiveHeading`
* **File Path**: `frontend/src/components/motion/InteractiveHeading.tsx`
* **Behavior**: Micro-interaction wrapper for section titles featuring subtle hover accent underlines and scale adjustments.

---

## 3. Component Micro-Interactions

| Component | Interaction Type | Easing & Timing |
| :--- | :--- | :--- |
| `LandingCTA` | Magnetic button spring with hover glow & arrow translation | `type: "spring", stiffness: 400, damping: 25` |
| `ForecastChart` | Path-length SVG drawing for historical and forecasted series | `duration: 1.2s, ease: "easeInOut"` |
| `ContextualPopup` | Modal backdrop fade & pop-in scale transition | `duration: 0.2s, ease: [0.16, 1, 0.3, 1]` |
| `TopNav` & `MobileNav` | Smooth height expansion & pill selector slide indicator | `type: "spring", stiffness: 350, damping: 30` |

---

## 4. Design Token Integration

All motion styles maintain harmony with the CAREFlow Design System tokens:
* **Background Surface**: Warm Ivory (`#FAF9F6`, CSS `--bg-app`)
* **Primary Accent**: Muted Deep Teal (`CSS --teal-600`) & Imperial Purple (`CSS --purple-600`)
* **Border Subtlety**: Low-contrast warm borders (`CSS --border-subtle`)
