# Frontend Architecture

### Component Organization

```
apps/web/src/
├── components/           # Reusable UI components
├── pages/               # Page-level components (routes)
├── hooks/               # Custom React hooks
├── services/            # API client services
├── stores/              # Zustand state stores
├── utils/               # Utility functions
├── types/               # Frontend-specific types
└── styles/              # Global styles
```

### State Management

- **Zustand** for global state (auth, session, reading queue)
- **React Context** for theme and UI preferences
- **Local state** for forms, modals, timers

**Key Stores:**
- `authStore` - User, tokens, authentication state (persisted)
- `sessionStore` - Current quiz session, question, competency updates
- `readingStore` - Reading queue items, unread badge count

### Routing

- **React Router v6** with protected routes pattern
- Nested routes with Outlet for layout composition
- Auth guard redirects to login with return URL preservation

### API Client

- **Axios** with request/response interceptors
- Automatic JWT token attachment
- Token refresh on 401 responses
- Service layer abstracts API calls

### Browser Support Matrix

**Supported Browsers (Latest 2 Versions):**

| Browser | Versions | Platform | Priority | Notes |
|---------|----------|----------|----------|-------|
| **Chrome** | Latest 2 major versions | Windows, macOS, Linux | Primary | Development primary target |
| **Edge** | Latest 2 major versions | Windows, macOS | Primary | Chromium-based, same engine as Chrome |
| **Firefox** | Latest 2 major versions | Windows, macOS, Linux | Secondary | Gecko engine, test separately |
| **Safari** | Latest 2 major versions | macOS, iOS | Primary | WebKit engine, critical for iOS users |

**Mobile Browser Support:**

| Browser | Versions | Platform | Priority | Notes |
|---------|----------|----------|----------|-------|
| **Safari Mobile** | iOS 14+ | iPhone, iPad | Primary | Largest mobile user base for professionals |
| **Chrome Mobile** | Latest 2 versions | Android | Primary | Default Android browser |
| **Samsung Internet** | Latest version | Android Samsung devices | Tertiary | Chromium-based, usually works |

**Minimum Screen Resolutions:**

| Device Category | Minimum Width | Minimum Height | Breakpoint | Notes |
|-----------------|---------------|----------------|------------|-------|
| **Mobile** | 375px | 667px | 0-767px | iPhone SE and up |
| **Tablet** | 768px | 1024px | 768-1279px | iPad standard |
| **Desktop** | 1280px | 720px | 1280px+ | Minimum usable desktop |

**Responsive Breakpoints:**
```css
/* Mobile-first approach */
/* Base styles: Mobile (375px+) */

@media (min-width: 768px) {
  /* Tablet styles */
}

@media (min-width: 1280px) {
  /* Desktop styles */
}

@media (min-width: 1920px) {
  /* Large desktop (optional) */
}
```

**Polyfill Strategy:**

LearnR uses modern JavaScript (ES2020+) and relies on Vite's built-in browser target configuration. No polyfills required for supported browsers.

**Browser Target (vite.config.ts):**
```typescript
export default {
  build: {
    target: ['es2020', 'edge88', 'firefox78', 'chrome87', 'safari14'],
  },
};
```

**Unsupported Browsers:**
- Internet Explorer (all versions) - End of life, no support
- Browsers older than 2 major versions - Security and performance concerns
- Opera Mini - Limited JavaScript support

**Testing Matrix:**

| Browser | Device | Frequency | Tools |
|---------|--------|-----------|-------|
| Chrome (latest) | Desktop | Every build | Playwright E2E |
| Safari (latest) | macOS, iOS | Every release | Manual + BrowserStack |
| Firefox (latest) | Desktop | Every release | Playwright E2E |
| Edge (latest) | Desktop | Weekly | Playwright E2E |
| Chrome Mobile | Android | Pre-release | BrowserStack |
| Safari Mobile | iPhone | Pre-release | Manual testing |

**Browser-Specific Considerations:**

**Safari:**
- Date input handling (use custom date picker if needed)
- Flexbox gap property (supported in Safari 14.1+)
- Service worker limitations (iOS PWA restrictions)

**Firefox:**
- Scrollbar styling (limited compared to Chrome)
- CSS backdrop-filter (supported in Firefox 103+)

**Mobile Safari:**
- 100vh viewport height issues (use `-webkit-fill-available`)
- Scroll momentum (`-webkit-overflow-scrolling: touch`)
- Fixed position elements during scroll

### Progressive Web App (PWA) Implementation

LearnR implements Progressive Web App capabilities to enhance mobile experience, enable offline error handling, and prepare for future offline features.

#### MVP PWA Features (30-Day Sprint)

**1. Web App Manifest**

Location: `apps/web/public/manifest.json`

```json
{
  "name": "LearnR - CBAP Exam Preparation",
  "short_name": "LearnR",
  "description": "AI-powered adaptive learning for CBAP certification",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#FFFFFF",
  "theme_color": "#0066CC",
  "orientation": "portrait-primary",
  "icons": [
    {
      "src": "/icons/icon-72x72.png",
      "sizes": "72x72",
      "type": "image/png",
      "purpose": "any maskable"
    },
    {
      "src": "/icons/icon-96x96.png",
      "sizes": "96x96",
      "type": "image/png"
    },
    {
      "src": "/icons/icon-128x128.png",
      "sizes": "128x128",
      "type": "image/png"
    },
    {
      "src": "/icons/icon-144x144.png",
      "sizes": "144x144",
      "type": "image/png"
    },
    {
      "src": "/icons/icon-152x152.png",
      "sizes": "152x152",
      "type": "image/png"
    },
    {
      "src": "/icons/icon-192x192.png",
      "sizes": "192x192",
      "type": "image/png"
    },
    {
      "src": "/icons/icon-384x384.png",
      "sizes": "384x384",
      "type": "image/png"
    },
    {
      "src": "/icons/icon-512x512.png",
      "sizes": "512x512",
      "type": "image/png"
    }
  ],
  "categories": ["education", "productivity"],
  "screenshots": [
    {
      "src": "/screenshots/desktop-dashboard.png",
      "sizes": "1280x720",
      "type": "image/png",
      "form_factor": "wide"
    },
    {
      "src": "/screenshots/mobile-quiz.png",
      "sizes": "750x1334",
      "type": "image/png",
      "form_factor": "narrow"
    }
  ]
}
```

**Manifest Configuration in index.html:**
```html
<link rel="manifest" href="/manifest.json">
<meta name="theme-color" content="#0066CC">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<meta name="apple-mobile-web-app-title" content="LearnR">
<link rel="apple-touch-icon" href="/icons/icon-152x152.png">
```

**2. Service Worker for Offline Error Handling**

Location: `apps/web/public/service-worker.js`

**Strategy:** Network-first with graceful offline error page

```javascript
const CACHE_NAME = 'learnr-v1';
const OFFLINE_PAGE = '/offline.html';

// Install event - cache offline page
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll([
        OFFLINE_PAGE,
        '/icons/icon-192x192.png',
        '/styles/offline.css'
      ]);
    })
  );
  self.skipWaiting();
});

// Fetch event - network-first, fallback to offline page
self.addEventListener('fetch', (event) => {
  if (event.request.mode === 'navigate') {
    event.respondWith(
      fetch(event.request).catch(() => {
        return caches.match(OFFLINE_PAGE);
      })
    );
  }
});

// Activate event - cleanup old caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames
          .filter((name) => name !== CACHE_NAME)
          .map((name) => caches.delete(name))
      );
    })
  );
  self.clients.claim();
});
```

**Service Worker Registration (main.tsx):**
```typescript
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker
      .register('/service-worker.js')
      .then((registration) => {
        console.log('SW registered:', registration);
      })
      .catch((error) => {
        console.error('SW registration failed:', error);
      });
  });
}
```

**Offline Page (`apps/web/public/offline.html`):**
```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Offline - LearnR</title>
  <link rel="stylesheet" href="/styles/offline.css">
</head>
<body>
  <div class="offline-container">
    <img src="/icons/icon-192x192.png" alt="LearnR Logo" width="96" height="96">
    <h1>You're Offline</h1>
    <p>LearnR requires an internet connection to load quiz questions and track your progress.</p>
    <p>Please check your connection and try again.</p>
    <button onclick="window.location.reload()">Retry</button>
  </div>
</body>
</html>
```

**3. Add to Home Screen (A2HS) Prompt**

**User Prompt Strategy:**
- Show A2HS prompt after user completes first quiz session (engagement signal)
- Defer prompt using `beforeinstallprompt` event
- User can dismiss permanently (localStorage flag)

**Implementation:**
```typescript
// src/hooks/useInstallPrompt.ts
import { useState, useEffect } from 'react';

export function useInstallPrompt() {
  const [deferredPrompt, setDeferredPrompt] = useState<any>(null);
  const [showPrompt, setShowPrompt] = useState(false);

  useEffect(() => {
    const handler = (e: Event) => {
      e.preventDefault();
      setDeferredPrompt(e);

      // Show prompt if user hasn't dismissed it
      const dismissed = localStorage.getItem('a2hs-dismissed');
      const firstSessionCompleted = localStorage.getItem('first-session-completed');

      if (!dismissed && firstSessionCompleted) {
        setShowPrompt(true);
      }
    };

    window.addEventListener('beforeinstallprompt', handler);
    return () => window.removeEventListener('beforeinstallprompt', handler);
  }, []);

  const promptInstall = async () => {
    if (!deferredPrompt) return;

    deferredPrompt.prompt();
    const { outcome } = await deferredPrompt.userChoice;

    console.log(`User ${outcome === 'accepted' ? 'accepted' : 'dismissed'} A2HS`);
    setDeferredPrompt(null);
    setShowPrompt(false);
  };

  const dismissPrompt = () => {
    localStorage.setItem('a2hs-dismissed', 'true');
    setShowPrompt(false);
  };

  return { showPrompt, promptInstall, dismissPrompt };
}
```

#### Post-MVP PWA Features (Future Roadmap)

**1. Offline Quiz Mode (Q1 2026)**
- Cache last 50 questions in IndexedDB
- Allow offline quiz sessions with local state
- Sync responses when connection restored
- Background Sync API for reliable upload

**2. Background Sync for Progress Tracking**
- Queue competency updates during offline usage
- Sync when connection restored
- Prevent data loss on flaky connections

**3. Push Notifications for Spaced Repetition**
- Remind users when reviews are due
- Daily study streak notifications
- Exam countdown reminders
- Requires user opt-in and notification permission

**4. Offline Reading Library**
- Cache reading content chunks for offline access
- Smart pre-caching based on user's weak areas
- Download BABOK sections for offline study

#### iOS-Specific Considerations

**Safari PWA Limitations:**
- No push notifications support (as of iOS 17)
- Service worker limitations (cleared after 7 days of inactivity)
- No background sync API
- Limited IndexedDB quota (50MB)

**iOS Workarounds:**
- Use Web Share API for sharing progress (instead of push)
- Show in-app reminders (instead of push notifications)
- Aggressive caching strategy for frequently accessed content
- Clear user expectations about offline capabilities

#### PWA Build Configuration

**Vite PWA Plugin (vite.config.ts):**
```typescript
import { VitePWA } from 'vite-plugin-pwa';

export default {
  plugins: [
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['icons/*.png', 'offline.html'],
      manifest: {
        // ... manifest config from above
      },
      workbox: {
        runtimeCaching: [
          {
            urlPattern: /^https:\/\/api\.learnr\.com\/v1\/.*/,
            handler: 'NetworkFirst',
            options: {
              cacheName: 'api-cache',
              expiration: {
                maxEntries: 100,
                maxAgeSeconds: 60 * 60, // 1 hour
              },
            },
          },
        ],
      },
    }),
  ],
};
```

#### Testing PWA Features

**Lighthouse PWA Audit:**
- Target score: 90+ (MVP)
- Required criteria:
  - ✓ Installable (manifest + service worker)
  - ✓ Registers a service worker
  - ✓ Responds with 200 when offline
  - ✓ Provides a valid manifest
  - ✓ Uses HTTPS
  - ✓ Redirects HTTP to HTTPS

**Manual Testing:**
- Test A2HS on Android Chrome, iOS Safari
- Test offline page display (disable network)
- Verify manifest icons at all sizes
- Test app in standalone mode (after install)

---
