import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  fullyParallel: true,
  retries: 2,
  workers: process.env.CI ? 4 : undefined,
  use: {
    headless: true,
    trace: 'on-first-retry',
  },
});
