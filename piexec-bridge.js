#!/usr/bin/env node
const fs = require('fs');
const { spawnSync } = require('child_process');

function readStdin() {
  return fs.readFileSync(0, 'utf8');
}

function parseInput(raw) {
  if (!raw || !raw.trim()) {
    throw new Error('empty stdin');
  }
  return JSON.parse(raw);
}

function asArray(value) {
  return Array.isArray(value) ? value : (value == null ? [] : [value]);
}

function summarizePlan(plan) {
  if (!plan || typeof plan !== 'object') return null;
  return {
    id: plan.id ?? null,
    plan_key: plan.plan_key ?? null,
    title: plan.title ?? null,
    status: plan.status ?? null,
    objective: plan.objective ?? null,
  };
}

function defaultResponse(input) {
  const primary = summarizePlan(input.primary_plan);
  const linked = asArray(input.linked_plans).map(summarizePlan).filter(Boolean);
  const planKeys = asArray(input.typescript_bridge_request && input.typescript_bridge_request.plan_keys);
  const planIds = asArray(input.typescript_bridge_request && input.typescript_bridge_request.plan_ids);
  const prompt = input.typescript_bridge_request && input.typescript_bridge_request.prompt
    ? input.typescript_bridge_request.prompt
    : 'No prompt supplied.';

  return {
    ok: true,
    bridge: 'piexec-bridge.js',
    mode: 'default-summary',
    received: {
      plan_keys: planKeys,
      plan_ids: planIds,
      prompt,
    },
    primary_plan: primary,
    linked_plans: linked,
    message: 'Pi bridge placeholder: inspect plan data, then replace this summary with a real Pi-agent call.',
  };
}

function callExternalPiAgent(input) {
  const cmd = process.env.PI_AGENT_COMMAND;
  if (!cmd) return null;
  const child = spawnSync(cmd, {
    input: JSON.stringify(input),
    encoding: 'utf8',
    shell: true,
    env: process.env,
    maxBuffer: 1024 * 1024,
  });
  if (child.error) throw child.error;
  const stdout = (child.stdout || '').trim();
  const stderr = (child.stderr || '').trim();
  if (child.status !== 0) {
    return {
      ok: false,
      bridge: 'piexec-bridge.js',
      mode: 'external-command',
      exit_code: child.status,
      stderr,
      stdout,
    };
  }
  try {
    return JSON.parse(stdout || '{}');
  } catch {
    return {
      ok: true,
      bridge: 'piexec-bridge.js',
      mode: 'external-command',
      exit_code: child.status,
      stdout,
      stderr,
    };
  }
}

try {
  const raw = readStdin();
  const input = parseInput(raw);
  const external = callExternalPiAgent(input);
  const output = external || defaultResponse(input);
  process.stdout.write(JSON.stringify(output, null, 2) + '\n');
} catch (err) {
  process.stdout.write(JSON.stringify({
    ok: false,
    bridge: 'piexec-bridge.js',
    error: String(err && err.message ? err.message : err),
  }, null, 2) + '\n');
  process.exit(1);
}
