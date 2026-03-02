# ARIA Frontend

Frontend web application for ARIA (Activity Report Intelligence Agent), built with React + Vite.

## Stack

- React 19
- Vite
- Tailwind CSS
- Axios

## Run locally

From this directory:

```bash
npm install
npm run dev
```

Default local URL:

- `http://localhost:5173`

## Build for production

```bash
npm run build
npm run preview
```

## API configuration

In Docker Compose, frontend uses:

```env
VITE_API_URL=http://localhost:8000
```

If you run frontend outside Docker, ensure backend is reachable at the same URL, or update your environment accordingly.

## Main folders

- `src/components/` → UI components
- `src/api/` → API client helpers
- `src/context/` → React contexts (auth/state)
- `src/hooks/` → reusable hooks
