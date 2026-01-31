# Frontend Build Plan (RidgeCare Link)

This doc covers only **Member 2** scope from WORK_SPLIT.md: shared frontend foundations, Dashboard page, and Weather page.

---

## Change Log (Member 2)

### Phase A — Foundation (2026-01-31)
- Added layout + tokens styles: `frontend/src/styles/tokens.css`, `frontend/src/styles/layout.css`, and rewired `frontend/src/index.css`.
- Built app shell components: `frontend/src/components/common/AppShell.tsx`, `frontend/src/components/common/Sidebar.tsx`, `frontend/src/components/common/TopBar.tsx`.
- Added shared UI primitives: `Button`, `Card`, `StatCard`, `StatusBadge`, `StormBanner`, `Table`, `TableEmptyState`, `Modal`, `Drawer`, `Toast`, `Skeleton`, `ErrorState`.
- Wired routing into the shell and toast provider: `frontend/src/App.tsx`, `frontend/src/main.tsx`.
- Updated scaffold pages with baseline layout: `frontend/src/pages/DashboardPage.tsx`, `frontend/src/pages/WeatherPage.tsx`.

---

## 1) Visual Direction (What it should look like)

Goal: clinical, calm, and decisive. The UI should feel like an operations console for nurses: clear priorities, strong status signaling, and low friction actions.

**Design language**
- **Typography**: pair a sturdy sans for UI and a high-contrast serif for page titles.
  - Example: "Space Grotesk" for UI + "Fraunces" for headings.
- **Color**: muted base with strong status colors.
  - Base: off-white, cool gray, slate.
  - Status: green (ok), amber (attention), red (urgent), blue (info).
- **Layout**: sidebar + top bar. Wide, breathable spacing. Cards and tables with strong hierarchy.
- **Motion**: subtle page-load fade/slide and staggered card reveals; no excessive micro-animations.
- **Background**: light gradient wash or soft pattern to avoid flat white.

**Tone & affordances**
- Emphasize triage: badges, timelines, and priority banners.
- All primary actions are obvious and clustered (e.g., "Create Referral", "Trigger Weather Check").

---

## 2) App Structure (Member 2 Pages & Responsibilities)

**App shell**
- Sidebar: Dashboard, Referrals, Patients, Weather
- Top bar: app title, current user (placeholder), environment badge (dev)

**Pages (Member 2)**
1. **Dashboard**
   - Summary cards: active referrals, overdue referrals, high-risk count
   - Storm Mode banner: status + current weather snippet
   - Recent activity feed: referral status changes
   - Quick actions: create referral, check weather

2. **Weather**
   - Current conditions card
   - Storm Mode status w/ thresholds
   - Active alerts list
   - Manual override button
   - Recent storm actions log

---

## 3) Component Inventory

### App Shell
- `AppShell`
  - Sidebar (nav + icon + badge)
  - TopBar (title, user pill, env badge)

### Common UI
- `PageHeader` (title, subtitle, actions)
- `StatCard`
- `StatusBadge` (Pending, Scheduled, Attended, Resolved, Missed)
- `StormBanner` (green/amber/red)
- `Table`
- `TableEmptyState`
- `SearchInput`
- `Select`
- `DateInput`
- `Toggle`
- `Button` (primary, secondary, ghost, danger)
- `Card`
- `Modal`
- `Drawer`
- `Toast` / `ToastProvider`
- `Skeleton` loader
- `ErrorState`

### Dashboard
- `DashboardSummary`
- `ActivityFeed`
- `QuickActions`

### Weather
- `CurrentWeatherCard`
- `StormStatusCard`
- `WeatherAlertsList`
- `StormLog`

---

## 4) API Integration Strategy (Member 2)

**Services (existing folder: `frontend/src/services`)**
- `api.ts`: base Axios client, interceptors
- `weatherService.ts`
- **Optional**: `dashboardService.ts` (or compute from existing endpoints)

**Data contracts**
- Strongly type responses using `types/` or `models/`:
  - `WeatherCondition`, `StormStatus`, `Alert`

**Error/Loading patterns**
- Use a consistent `useAsync` hook or `react-query` (pick one). For simplicity:
  - Implement `useAsync` + `useToast` for now.

---

## 5) Implementation Strategy (Member 2 Phases)

### Phase A — Foundation (Week 1)
- Build AppShell + routing
- Build common UI components and layout system
- Add global styles + CSS variables
- Add toast system and skeleton loaders

### Phase B — Dashboard + Weather (Week 1-2)
- Hook up `/api/weather/current` + `/api/weather/storm-status`
- Implement dashboard summary cards and storm banner
- Use mock data for activity feed if backend not ready

### Phase D — Polish + QA
- Empty states, errors, skeletons
- Keyboard focus + a11y labels
- Consistent spacing, type scale, and status colors

---

## 6) File/Folder Plan (Member 2)

```
frontend/src/
  components/
    common/
      AppShell.tsx
      PageHeader.tsx
      StatCard.tsx
      StatusBadge.tsx
      Table.tsx
      Modal.tsx
      Drawer.tsx
      Toast.tsx
      Skeleton.tsx
      ...
    dashboard/
      DashboardSummary.tsx
      ActivityFeed.tsx
      QuickActions.tsx
    weather/
      CurrentWeatherCard.tsx
      StormStatusCard.tsx
      WeatherAlertsList.tsx
      StormLog.tsx
  pages/
    DashboardPage.tsx
    WeatherPage.tsx
  services/
    api.ts
    weatherService.ts
  styles/
    tokens.css
    layout.css
```

---

## 7) Detailed Implementation Plan (Files + Component Docs)

This section lists every file we will create or change in the **frontend** folder for Member 2 scope, with a brief spec for each component.

### App Shell + Routing
- `frontend/src/App.tsx` (update)
  - Wire routes for Dashboard + Weather and wrap all pages with `AppShell`.
  - Ensure sidebar nav items are rendered and active route is highlighted.
  - Page-level layout should use `PageHeader` and common container spacing.

- `frontend/src/main.tsx` (update)
  - Add `ToastProvider` and any global context providers.

- `frontend/src/components/common/AppShell.tsx` (new)
  - Layout grid: sidebar + topbar + main content.
  - Sidebar includes nav links and simple branding.
  - Topbar includes app title + placeholder user pill + environment badge.

- `frontend/src/components/common/Sidebar.tsx` (new)
  - Renders nav list and section labels.
  - Accepts `items: { label, to, icon }[]`.

- `frontend/src/components/common/TopBar.tsx` (new)
  - Displays page title (optional), user pill, and env badge.

### Common UI
- `frontend/src/components/common/PageHeader.tsx` (new)
  - Title, optional subtitle, and right-aligned action buttons.

- `frontend/src/components/common/Card.tsx` (new)
  - Base container used by StatCard, panels, and lists.

- `frontend/src/components/common/StatCard.tsx` (new)
  - Shows metric value, label, and optional trend.

- `frontend/src/components/common/StatusBadge.tsx` (new)
  - Status chips (Pending, Scheduled, Attended, Resolved, Missed).
  - Maps statuses to color tokens.

- `frontend/src/components/common/StormBanner.tsx` (new)
  - Prominent banner with icon + status messaging.
  - Uses `isSevere` to switch between green/amber/red.

- `frontend/src/components/common/Table.tsx` (new)
  - Lightweight table wrapper (head + body + empty state slot).

- `frontend/src/components/common/TableEmptyState.tsx` (new)
  - Displayed when a table has no rows.

- `frontend/src/components/common/Button.tsx` (new)
  - Variants: primary, secondary, ghost, danger.

- `frontend/src/components/common/Modal.tsx` (new)
  - Generic overlay modal (used later by Member 3).

- `frontend/src/components/common/Drawer.tsx` (new)
  - Side panel container (used later by Member 3).

- `frontend/src/components/common/Toast.tsx` (new)
  - `ToastProvider`, `useToast`, `ToastViewport`.
  - Standard success/error styling.

- `frontend/src/components/common/Skeleton.tsx` (new)
  - Loading placeholder blocks with shimmer.

- `frontend/src/components/common/ErrorState.tsx` (new)
  - Standard inline error state with retry button.

### Dashboard
- `frontend/src/pages/DashboardPage.tsx` (update)
  - Assemble the dashboard page using the components below.
  - Pull data from `dashboardService` or mock until backend is ready.

- `frontend/src/components/dashboard/DashboardSummary.tsx` (new)
  - Renders 3–4 `StatCard`s (active referrals, overdue, high-risk, etc.).

- `frontend/src/components/dashboard/ActivityFeed.tsx` (new)
  - List of recent referral changes (mock data ok).

- `frontend/src/components/dashboard/QuickActions.tsx` (new)
  - Buttons for create referral, trigger weather check.

### Weather
- `frontend/src/pages/WeatherPage.tsx` (update)
  - Fetch `current` and `storm-status` endpoints.
  - Render cards, alerts list, and action button.

- `frontend/src/components/weather/CurrentWeatherCard.tsx` (new)
  - Temperature, snowfall, description, location.

- `frontend/src/components/weather/StormStatusCard.tsx` (new)
  - Shows thresholds and whether `isSevere` is true.

- `frontend/src/components/weather/WeatherAlertsList.tsx` (new)
  - Lists active alerts or empty state.

- `frontend/src/components/weather/StormLog.tsx` (new)
  - Placeholder log list (mocked until backend support exists).

### Services + Types
- `frontend/src/services/weatherService.ts` (update if needed)
  - Add `getCurrentWeather()` and `getStormStatus()` returning typed data.

- `frontend/src/services/dashboardService.ts` (new, optional)
  - Aggregates summary metrics from other services or mock.

- `frontend/src/types/weather.ts` (new)
  - `WeatherCondition`, `StormStatus`, `WeatherAlert` types.

### Styles
- `frontend/src/index.css` (update)
  - Set global styles, font imports, and body background.

- `frontend/src/styles/tokens.css` (new)
  - CSS variables for color, spacing, typography, and shadow.

- `frontend/src/styles/layout.css` (new)
  - Layout utilities, grid, page padding, card spacing.

---

## 8) UI Tokens (initial suggestion)

**Colors**
- `--bg: #f6f7f9`
- `--surface: #ffffff`
- `--text: #101828`
- `--muted: #667085`
- `--border: #e4e7ec`
- `--ok: #12b76a`
- `--warn: #f79009`
- `--danger: #f04438`
- `--info: #2e90fa`

**Type**
- UI: `Space Grotesk`
- Headings: `Fraunces`

---

## 9) Notes / Dependencies

- Needs backend seed data for realistic tables.
- If auth lands, add route guards + session state.
- If performance issues appear, consider `react-query`.

---

## 10) Next Actions (if you want me to proceed)

1) Build AppShell + routing + tokens
2) Implement common UI primitives
3) Wire Weather page first (fast feedback)
