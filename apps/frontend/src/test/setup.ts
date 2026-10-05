/**
 * Vitest setup (Appendix AL H45/H46).
 *
 * jsdom + jest-dom matchers. Testing Library cleans up the DOM automatically
 * because `globals: true` is enabled in vitest.config.ts.
 */

import '@testing-library/jest-dom/vitest';
