/**
 * Static security scans for the frontend foundation (Appendix AL §51-§53, §69).
 *
 * These are source-level invariants, not a substitute for the acceptance gate:
 * no token persistence, no dynamic code execution, no unsafe HTML, no secrets and
 * no environment-dependent production bundle.
 */

import { readdirSync, readFileSync, statSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { describe, expect, it } from 'vitest';

/** Vitest runs from the frontend package root. */
const FRONTEND_ROOT = resolve(process.cwd());
const SRC_ROOT = join(FRONTEND_ROOT, 'src');

interface SourceFile {
  path: string;
  content: string;
}

function collectSourceFiles(dir: string): SourceFile[] {
  const files: SourceFile[] = [];
  for (const entry of readdirSync(dir)) {
    const full = join(dir, entry);
    if (statSync(full).isDirectory()) {
      if (entry === 'test') {
        continue;
      }
      files.push(...collectSourceFiles(full));
      continue;
    }
    if (/\.(ts|tsx|css|html)$/.test(entry) && !/\.test\.(ts|tsx)$/.test(entry)) {
      files.push({ path: full, content: stripComments(readFileSync(full, 'utf8')) });
    }
  }
  return files;
}

/**
 * Documentation comments legitimately *discuss* forbidden APIs ("never written to
 * localStorage"); the scan must look at executable source only.
 */
function stripComments(content: string): string {
  return content
    .replace(/\/\*[\s\S]*?\*\//g, '')
    .replace(/(^|\s)\/\/.*$/gm, '$1');
}

const SOURCE_FILES = collectSourceFiles(SRC_ROOT);

function offenders(pattern: RegExp): string[] {
  return SOURCE_FILES.filter((file) => pattern.test(file.content)).map((file) => file.path);
}

describe('frontend security scans', () => {
  it('never persists a token in browser storage', () => {
    expect(SOURCE_FILES.length).toBeGreaterThan(20);
    expect(offenders(/(localStorage|sessionStorage)\s*[.[]/)).toEqual([]);
    expect(offenders(/document\.cookie\s*=/)).toEqual([]);
  });

  it('never evaluates dynamic code', () => {
    expect(offenders(/\beval\s*\(/)).toEqual([]);
    expect(offenders(/new\s+Function\s*\(/)).toEqual([]);
  });

  it('never injects raw HTML', () => {
    expect(offenders(/dangerouslySetInnerHTML/)).toEqual([]);
    expect(offenders(/\.innerHTML\s*=/)).toEqual([]);
  });

  it('carries no secret material', () => {
    expect(
      offenders(
        /(postgres(ql)?:\/\/|sk-[A-Za-z0-9]{16,}|-----BEGIN|jwt[_-]?secret|DATABASE_URL|DB_PASSWORD)/i,
      ),
    ).toEqual([]);
  });

  it('hardcodes no API target in the application source', () => {
    expect(offenders(/VITE_API_TARGET/)).toEqual([]);
    expect(offenders(/localhost:8000/)).toEqual([]);
  });

  it('keeps the environment template public-only', () => {
    const template = readFileSync(join(FRONTEND_ROOT, '.env.example'), 'utf8');
    const assignments = template
      .split(/\r?\n/)
      .filter((line) => /^[A-Za-z_][A-Za-z0-9_]*=/.test(line.trim()));

    expect(assignments.length).toBeGreaterThan(0);
    for (const assignment of assignments) {
      expect(assignment.trim().startsWith('VITE_')).toBe(true);
      expect(assignment).not.toMatch(/(secret|password|token|dsn)/i);
    }
  });
});
