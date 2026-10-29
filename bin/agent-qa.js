#!/usr/bin/env node
/**
 * Enterprise Agent-Cortex NPM Launcher
 * =====================================
 * Dispatches CLI subcommands to the underlying Python Standard Library engine (tools/cli.py).
 * Provides cross-platform zero-install execution via `npx agent-cortex <command>`.
 */

const { spawn, execSync } = require('child_process');
const path = require('path');
const fs = require('fs');

const REPO_ROOT = path.resolve(__dirname, '..');
const CLI_PATH = path.join(REPO_ROOT, 'tools', 'cli.py');

// ANSI Color Helpers
const RED = '\x1b[91m';
const GREEN = '\x1b[92m';
const YELLOW = '\x1b[93m';
const CYAN = '\x1b[96m';
const BOLD = '\x1b[1m';
const RESET = '\x1b[0m';

/**
 * Resolves the available Python 3 executable across Windows, macOS, and Linux.
 */
function resolvePython() {
  const candidates = process.platform === 'win32'
    ? ['python', 'py', 'python3']
    : ['python3', 'python'];

  for (const cmd of candidates) {
    try {
      const output = execSync(`${cmd} --version`, { encoding: 'utf-8', stdio: ['ignore', 'pipe', 'ignore'] }).trim();
      const match = output.match(/Python\s+(\d+)\.(\d+)/i);
      if (match) {
        const major = parseInt(match[1], 10);
        const minor = parseInt(match[2], 10);
        if (major > 3 || (major === 3 && minor >= 9)) {
          return { command: cmd, version: output };
        }
      }
    } catch (e) {
      // Continue checking next candidate
    }
  }
  return null;
}

function main() {
  const python = resolvePython();

  if (!python) {
    console.error(`\n${BOLD}${RED}[ERROR] Python 3.9+ is required to execute agent-cortex tools.${RESET}`);
    console.error(`Neither ${CYAN}python3${RESET} nor ${CYAN}python${RESET} (>= 3.9) was found on your PATH.`);
    console.error(`👉 Please install Python from: ${BOLD}https://www.python.org/downloads/${RESET}\n`);
    process.exit(1);
  }

  if (!fs.existsSync(CLI_PATH)) {
    console.error(`\n${BOLD}${RED}[ERROR] Core CLI engine not found at: ${CLI_PATH}${RESET}\n`);
    process.exit(1);
  }

  const args = [CLI_PATH, ...process.argv.slice(2)];

  // Spawn child Python process inheriting standard IO
  const child = spawn(python.command, args, {
    stdio: 'inherit',
    env: { ...process.env, AGENT_QA_INVOKER: 'npm' }
  });

  child.on('error', (err) => {
    console.error(`\n${BOLD}${RED}[ERROR] Failed to start agent-cortex CLI:${RESET}`, err.message);
    process.exit(1);
  });

  child.on('exit', (code, signal) => {
    if (signal) {
      process.kill(process.pid, signal);
    } else {
      process.exit(code ?? 0);
    }
  });

  process.on('SIGINT', () => child.kill('SIGINT'));
  process.on('SIGTERM', () => child.kill('SIGTERM'));
}

main();
