# Frontend Mock Data Setup & Theme Update

## Overview
The frontend has been configured to support a "Mock Mode" for local development without a backend, and the theme has been updated to a Red & White color scheme.

## Changes Made
1. **Mock Data Service**: Added `src/lib/mock-api.ts` to intercept API calls and return sample data.
2. **Configuration**: Added `USE_MOCK_DATA` flag in `src/lib/api-config.ts`.
3. **Authentication**: Updated `AuthContext` to support mock login with `admin@estateflow.local` / `Admin@123!`.
4. **Properties**: Updated `property-api.ts` to serve mock property listings.
5. **Theme**: Updated `src/index.css` to use Red (Primary) and White/Gray (Backgrounds).
6. **UI**: Polished `Login.tsx` and `Properties.tsx` to match the new theme.

## How to Run
1. Ensure you are in the frontend directory: `cd frontend`
2. Run the development server: `npm run dev`
3. Open the browser (usually `http://localhost:8080` or `http://localhost:5173`).
4. **Login**: Use `admin@estateflow.local` and any password (e.g. `Admin@123!`). 
   - Note: Trigger a login error by using email `fail@test.com`.
5. **Explore**:
   - Go to **Properties** page to see the mock listings.
   - Use the **Search** bar to see the AI search mock response.

## Toggling Mock Mode
To disable mock data and connect to the real backend:
1. Open `src/lib/api-config.ts`
2. Set `export const USE_MOCK_DATA = false;`
