#!/usr/bin/env node

const fs = require('node:fs');
const path = require('node:path');
const { spawnSync } = require('node:child_process');

const rootDir = process.cwd();
const npmCmd = process.platform === 'win32' ? 'npm.cmd' : 'npm';
const yarnCmd = process.platform === 'win32' ? 'yarn.cmd' : 'yarn';
const useShell = process.platform === 'win32';

function run(cmd, args, options = {}) {
  const result = spawnSync(cmd, args, {
    cwd: rootDir,
    stdio: 'inherit',
    shell: useShell,
    env: process.env,
    ...options,
  });

  if (typeof result.status === 'number' && result.status !== 0) {
    process.exit(result.status);
  }

  if (result.error) {
    console.error(result.error.message);
    process.exit(1);
  }
}

function runCapture(cmd, args) {
  const result = spawnSync(cmd, args, {
    cwd: rootDir,
    stdio: ['ignore', 'pipe', 'pipe'],
    shell: useShell,
    env: process.env,
    encoding: 'utf8',
  });

  return {
    ok: result.status === 0 && !result.error,
    stdout: (result.stdout || '').trim(),
  };
}

function yarnExists() {
  return runCapture(yarnCmd, ['--version']).ok;
}

function ensureYarnInPath() {
  const prefix = runCapture(npmCmd, ['config', 'get', 'prefix']);
  if (!prefix.ok || !prefix.stdout) {
    return;
  }

  const delimiter = process.platform === 'win32' ? ';' : ':';
  process.env.PATH = `${prefix.stdout}${delimiter}${process.env.PATH}`;
}

function ensureYarn() {
  if (yarnExists()) {
    return;
  }

  console.log('Installing yarn globally (one-time setup)...');
  run(npmCmd, ['install', '-g', 'yarn']);

  ensureYarnInPath();

  if (!yarnExists()) {
    console.error('yarn is still not available in PATH after install.');
    process.exit(1);
  }
}

function needsInstall() {
  return !fs.existsSync(path.join(rootDir, 'node_modules'));
}

function needsAjvFix() {
  return !fs.existsSync(path.join(rootDir, 'node_modules', 'ajv', 'dist', 'compile', 'codegen.js'));
}

function installDepsIfNeeded() {
  if (needsInstall()) {
    console.log('Installing dependencies...');
    run(npmCmd, ['install', '--legacy-peer-deps', '--no-package-lock']);
  }

  if (needsAjvFix()) {
    console.log('Installing AJV compatibility packages...');
    run(npmCmd, [
      'install',
      'ajv@^8',
      'ajv-keywords@^5',
      '--no-save',
      '--no-package-lock',
      '--legacy-peer-deps',
    ]);
  }
}

function startDocs() {
  run(npmCmd, ['run', 'start']);
}

ensureYarnInPath();
ensureYarn();
installDepsIfNeeded();
startDocs();
