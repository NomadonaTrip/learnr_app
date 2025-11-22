# LearnR Frontend (Web)

React-based single-page application for LearnR adaptive learning platform.

## Tech Stack

- **Framework:** React 18.2.x
- **Language:** TypeScript 5.3.x
- **Build Tool:** Vite 5.0.x
- **Styling:** Tailwind CSS 3.4.x + Headless UI 1.7.x
- **State Management:** Zustand 4.5.x + React Context
- **Router:** React Router 6.21.x
- **HTTP Client:** Axios 1.6.x
- **Testing:** Vitest 1.2.x + React Testing Library 14.x

## Getting Started

### Prerequisites

- Node.js 18+ and npm 10+
- Backend API running on `http://localhost:8000` (or configure `VITE_API_URL`)

### Installation

From the monorepo root or this directory:

```bash
npm install
```

### Configuration

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Update environment variables as needed (defaults work for local development)

### Development

Start the development server:

```bash
npm run dev
```

The app will be available at `http://localhost:5173`

### Available Scripts

- `npm run dev` - Start Vite dev server with hot reload
- `npm run build` - Build for production (runs type-check + vite build)
- `npm run preview` - Preview production build locally
- `npm run test` - Run unit tests with Vitest
- `npm run test:watch` - Run tests in watch mode
- `npm run test:ui` - Open Vitest UI
- `npm run test:ci` - Run tests with coverage for CI
- `npm run lint` - Lint code with ESLint
- `npm run lint:fix` - Auto-fix linting issues
- `npm run format` - Format code with Prettier
- `npm run format:check` - Check code formatting
- `npm run type-check` - Run TypeScript type checking

## Project Structure

```
apps/web/
├── src/
│   ├── components/       # React components
│   │   ├── common/      # Shared UI components (Button, Card, etc.)
│   │   ├── quiz/        # Quiz-specific components
│   │   ├── dashboard/   # Dashboard components
│   │   ├── reading/     # Reading library components
│   │   └── layout/      # Layout components (Nav, Header, Footer)
│   ├── pages/           # Page-level components
│   ├── hooks/           # Custom React hooks
│   ├── services/        # API service layer (authService, quizService, etc.)
│   ├── stores/          # Zustand global state stores
│   ├── utils/           # Utility functions
│   ├── types/           # TypeScript type definitions
│   ├── styles/          # Global styles and Tailwind config
│   ├── App.tsx          # Root component
│   └── main.tsx         # Application entry point
├── tests/               # Test files
│   ├── unit/           # Unit tests
│   └── integration/    # Integration tests
├── public/              # Static assets
├── index.html           # HTML entry point
├── vite.config.ts       # Vite configuration
├── tailwind.config.js   # Tailwind CSS configuration
├── tsconfig.json        # TypeScript configuration
└── package.json         # Dependencies and scripts
```

## Coding Standards

See [../../docs/architecture/coding-standards.md](../../docs/architecture/coding-standards.md) for detailed standards.

### Key Conventions

- **Components:** PascalCase (e.g., `UserProfile.tsx`)
- **Hooks:** camelCase with 'use' prefix (e.g., `useAuth.ts`)
- **Services:** camelCase (e.g., `authService.ts`)
- **Never access `process.env` directly** - use config objects
- **Never make direct HTTP calls in components** - use service layer
- **Type sharing:** Import from `@learnr/shared-types` package

## Environment Variables

All frontend environment variables must be prefixed with `VITE_` to be exposed to the client.

See `.env.example` for available configuration options.

## Contributing

1. Follow the coding standards in `docs/architecture/coding-standards.md`
2. Write tests for new components and features
3. Run `npm run lint` and `npm run type-check` before committing
4. Ensure all tests pass with `npm run test`
