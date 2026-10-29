import { defineConfig } from '@playwright/test';

export default defineConfig({testDir:'./e2e-internal',workers:1,
  use:{baseURL:'http://localhost:8002',channel:'chrome',headless:true,trace:'off'},reporter:'list'});
