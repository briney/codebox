# WEB.md

Supplementary guidelines for web development. Consult this file when working on React, Django, Next.js, or any frontend/backend web code.

---

## Frontend Stack

**React + TypeScript + Tailwind CSS + Next.js (App Router)**

### TypeScript

- **TypeScript is mandatory** for all frontend code. No `.js` or `.jsx` files in React projects.
- Use strict mode (`"strict": true` in `tsconfig.json`).
- Prefer `interface` for object shapes that may be extended; `type` for unions, intersections, and utility types.
- Avoid `any`. Use `unknown` when the type is genuinely uncertain, then narrow with type guards.
- Use `as const` for literal tuples and enums-as-objects.
- Prefer `satisfies` over `as` for type-checking without widening.
- Generic components are fine, but don't over-abstract — if a generic has more than two type parameters, reconsider the design.

### React

- **Functional components only** with hooks. No class components.
- Component files: `PascalCase.tsx`. One exported component per file (small helpers colocated are fine).
- Props: define with an `interface` named `{ComponentName}Props`. Destructure in the function signature.
- State management priority: `useState` → `useReducer` → Zustand / context → Redux (only if already in the project).
- Custom hooks: extract when logic is reused across 2+ components or when a component's hook section exceeds ~15 lines.
- Avoid `useEffect` for derived state — compute it during render or use `useMemo`.
- Memoization: don't prematurely optimize. Use `React.memo`, `useMemo`, `useCallback` only when profiling shows a need or when passing callbacks to large lists.
- Event handlers: name as `handle{Event}` (e.g., `handleClick`, `handleSubmit`). Props that accept handlers: `on{Event}`.

### Next.js (App Router)

- Use the App Router (`app/` directory), not Pages Router, for new projects.
- Server Components by default. Add `"use client"` only when the component needs browser APIs, hooks, or event handlers.
- Data fetching: use `async` Server Components with `fetch` or direct DB/API calls. Use `loading.tsx` and `error.tsx` for Suspense boundaries.
- Route handlers (`route.ts`) for API endpoints. Use proper HTTP methods and status codes.
- Metadata: use the `metadata` export or `generateMetadata` for SEO, not `<Head>`.
- Images: use `next/image` with explicit `width`/`height` or `fill`. Always provide `alt` text.
- Environment variables: `NEXT_PUBLIC_` prefix for client-side, plain for server-side. Never expose secrets to the client.

### Tailwind CSS

- Use utility classes directly in JSX. This is the expected pattern — don't fight it.
- Extract to a component (not a CSS class) when a pattern repeats 3+ times.
- Use `cn()` helper (clsx + tailwind-merge) for conditional/merged classes:
  ```tsx
  import { cn } from "@/lib/utils";
  <div className={cn("base-classes", conditional && "conditional-classes")} />
  ```
- Design tokens: use Tailwind's `theme.extend` in `tailwind.config.ts` for project colors, spacing, fonts. Don't hardcode hex values in utilities.
- Responsive: mobile-first. Use `sm:`, `md:`, `lg:` breakpoints. Test at standard breakpoints.
- Dark mode: use `dark:` variant with class-based strategy if the project supports it.
- Animation: prefer Tailwind's built-in `animate-*` utilities or `transition-*` classes. Use Framer Motion for complex animations.

### Component Library

- **shadcn/ui** is the preferred component library. Install components as needed — they live in your codebase, not in `node_modules`.
- Customize shadcn components by editing the source files directly. That's the point of the library.
- For icons: `lucide-react`.
- Don't install additional UI libraries (Material UI, Chakra, Ant Design) alongside shadcn unless there's a specific missing primitive.

### Data Fetching & State

- **SWR** or **@tanstack/react-query** for client-side data fetching. Always handle three states: loading, error, success (+ empty).
- Server-side: fetch in Server Components or Route Handlers. Avoid client-side fetching for data that can be fetched on the server.
- Forms: use React Hook Form + Zod for validation. Server Actions for form submission in Next.js.
- Optimistic updates for user-facing mutations when latency matters.

### File Organization

```
app/
├── (auth)/               # Route groups for layout sharing
│   ├── login/
│   └── register/
├── dashboard/
│   ├── page.tsx
│   ├── loading.tsx
│   └── error.tsx
├── api/
│   └── route.ts
├── layout.tsx
└── globals.css
components/
├── ui/                   # shadcn/ui primitives
├── forms/                # Form-specific components
└── {feature}/            # Feature-grouped components
lib/
├── utils.ts
├── api.ts                # API client helpers
└── validations.ts        # Zod schemas
hooks/
├── use-{feature}.ts
types/
├── index.ts              # Shared type definitions
```

### Frontend Testing

- **Vitest** for unit tests. **Playwright** for E2E.
- Test user behavior, not implementation: query by role/label, not by class or test ID (unless necessary).
- Use `@testing-library/react` with `userEvent` (not `fireEvent`).
- Mock API calls at the network level (`msw`), not by mocking fetch directly.

---

## Backend (Django)

### Django Conventions

- **Django 4.2+ / 5.x**. Use latest stable for new projects.
- **Django REST Framework** for all API endpoints. Use `ModelSerializer` + `ViewSet` for standard CRUD.
- URL naming: `{app}-{model}-{action}` (e.g., `analysis-run-list`, `analysis-run-detail`).
- Views: prefer `ViewSet` and `APIView` over function-based views.
- Permissions: define per-view. Use DRF permission classes, not Django's built-in `@login_required` for API views.

### Models & Database

- Always create migrations (`makemigrations` + `migrate`). Never edit migrations by hand unless resolving merge conflicts.
- Use `select_related` / `prefetch_related` to avoid N+1 queries. Profile with Django Debug Toolbar in development.
- Model naming: singular (`Analysis`, not `Analyses`). Let Django pluralize the table name.
- Add `__str__` to every model. Add `class Meta: ordering` when a default order makes sense.
- Use `UUIDField` as primary key for models exposed in APIs. Keep the auto `id` for internal-only models.
- Index fields used in filters and lookups: `db_index=True` or `Meta.indexes`.
- Soft delete (add `deleted_at` field) for user-facing data. Hard delete for ephemeral/processing data.

### Settings & Configuration

- Use `django-environ` or split settings (`base.py`, `local.py`, `production.py`).
- Never hardcode secrets. All secrets via environment variables.
- `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`: configure per environment. Never use `*` in production.

### Async & Background Tasks

- **Celery** (with Redis broker) or **Django-Q** for background tasks, depending on what's already in the project.
- Keep tasks idempotent. Always accept primitive arguments (IDs, not model instances).
- Set reasonable timeouts and retry policies. Log task start/end.

### Django + React Integration

- API-only Django backend (DRF) + separate Next.js frontend is the preferred architecture.
- Use token-based auth (JWT via `djangorestframework-simplejwt` or session auth behind a reverse proxy).
- CORS: configure `django-cors-headers` to allow the frontend origin.
- Serve the Next.js app independently (Vercel, standalone Node, or static export behind Nginx).

---

## General Web Practices

### Accessibility

- Semantic HTML: use `<button>`, `<nav>`, `<main>`, `<article>`, not `<div onClick>`.
- All images have `alt` text. Decorative images get `alt=""`.
- Form inputs have associated `<label>` elements.
- Keyboard navigable: all interactive elements reachable via Tab, operable via Enter/Space.

### Security

- Sanitize user input on the server, even if validated on the client.
- Use CSP headers. Set `HttpOnly`, `Secure`, `SameSite` on cookies.
- Never expose API keys, secrets, or internal URLs in client-side code or browser source.

### Performance

- Lazy load below-the-fold images and heavy components.
- Code split at the route level (Next.js does this automatically).
- Monitor Core Web Vitals in production.
