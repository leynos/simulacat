/**
 * @file Tests for the GitHub simulator server.
 */

import { afterEach, describe, expect, test } from "bun:test";
import { mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { type Subprocess, spawn } from "bun";

const SERVER_PATH = join(import.meta.dir, "github-sim-server.ts");

interface ListeningEvent {
  event: "listening";
  port: number;
}

interface ErrorEvent {
  event: "error";
  message: string;
}

type ServerEvent = ListeningEvent | ErrorEvent;

async function readServerOutput(proc: Subprocess): Promise<ServerEvent> {
  const stdout = proc.stdout;
  if (!stdout || typeof stdout === "number") {
    throw new Error("stdout is not a readable stream");
  }
  const reader = stdout.getReader();
  const { value } = await reader.read();
  reader.releaseLock();
  const text = new TextDecoder().decode(value);
  return JSON.parse(text.trim()) as ServerEvent;
}

describe("github-sim-server", () => {
  let tempDir: string;
  let proc: Subprocess | undefined;

  afterEach(() => {
    if (proc) {
      proc.kill();
      proc = undefined;
    }
    if (tempDir) {
      rmSync(tempDir, { recursive: true, force: true });
    }
  });

  test("starts with valid config and outputs listening event", async () => {
    tempDir = mkdtempSync(join(tmpdir(), "sim-test-"));
    const configPath = join(tempDir, "config.json");
    const validConfig = {
      users: [],
      organizations: [],
      repositories: [],
      branches: [],
      blobs: [],
    };
    writeFileSync(configPath, JSON.stringify(validConfig));

    proc = spawn(["bun", SERVER_PATH, configPath], {
      stdout: "pipe",
      stderr: "pipe",
    });

    const event = await readServerOutput(proc);

    expect(event.event).toBe("listening");
    expect((event as ListeningEvent).port).toBeGreaterThan(0);
  });

  test("outputs error for missing config path", async () => {
    proc = spawn(["bun", SERVER_PATH], {
      stdout: "pipe",
      stderr: "pipe",
    });

    const event = await readServerOutput(proc);

    expect(event.event).toBe("error");
    expect((event as ErrorEvent).message).toContain("Usage:");

    await proc.exited;
    expect(proc.exitCode).toBe(1);
  });

  test("outputs error for non-existent config file", async () => {
    proc = spawn(["bun", SERVER_PATH, "/nonexistent/config.json"], {
      stdout: "pipe",
      stderr: "pipe",
    });

    const event = await readServerOutput(proc);

    expect(event.event).toBe("error");
    expect((event as ErrorEvent).message).toContain("Config file not found");

    await proc.exited;
    expect(proc.exitCode).toBe(1);
  });

  test("outputs error for invalid JSON config", async () => {
    tempDir = mkdtempSync(join(tmpdir(), "sim-test-"));
    const configPath = join(tempDir, "config.json");
    writeFileSync(configPath, "not valid json {{{");

    proc = spawn(["bun", SERVER_PATH, configPath], {
      stdout: "pipe",
      stderr: "pipe",
    });

    const event = await readServerOutput(proc);

    expect(event.event).toBe("error");
    expect((event as ErrorEvent).message).toContain("Invalid JSON");

    await proc.exited;
    expect(proc.exitCode).toBe(1);
  });
});
