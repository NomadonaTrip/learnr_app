import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import path from 'path';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  test: {
    // Use jsdom environment for React component testing
    environment: 'jsdom',

    // Setup files to run before tests
    setupFiles: ['./tests/setup.ts'],

    // Global test utilities
    globals: true,

    // Coverage configuration
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html', 'lcov'],
      exclude: [
        'node_modules/',
        'tests/',
        '**/*.d.ts',
        '**/*.config.*',
        '**/mockData/**',
        'src/vite-env.d.ts',
      ],
      // Minimum coverage thresholds
      thresholds: {
        lines: 80,
        functions: 80,
        branches: 80,
        statements: 80,
      },
    },

    // Test file patterns
    include: [
      '**/*.{test,spec}.{js,mjs,cjs,ts,mts,cts,jsx,tsx}',
      'tests/**/*.{test,spec}.{js,mjs,cjs,ts,mts,cts,jsx,tsx}',
    ],

    // Exclude patterns
    exclude: [
      'node_modules',
      'dist',
      '.idea',
      '.git',
      '.cache',
    ],

    // Test timeout (milliseconds)
    testTimeout: 10000,

    // Hook timeout (milliseconds)
    hookTimeout: 10000,

    // Fail test on console.error
    onConsoleLog(log, type) {
      if (type === 'error' && log.includes('Warning:')) {
        return false; // Don't fail on React warnings
      }
      return true;
    },

    // Mock CSS modules
    css: {
      modules: {
        classNameStrategy: 'non-scoped',
      },
    },
  },

  // Path aliases (match tsconfig.json paths)
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@components': path.resolve(__dirname, './src/components'),
      '@pages': path.resolve(__dirname, './src/pages'),
      '@hooks': path.resolve(__dirname, './src/hooks'),
      '@services': path.resolve(__dirname, './src/services'),
      '@stores': path.resolve(__dirname, './src/stores'),
      '@utils': path.resolve(__dirname, './src/utils'),
      '@types': path.resolve(__dirname, './src/types'),
    },
  },
});
