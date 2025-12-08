#!/usr/bin/env bun

/**
 * @file GitHub simulator server entry point.
 *
 * Reads configuration from a JSON file and starts the Simulacrum GitHub API
 * simulator on an OS-assigned port. Outputs a JSON listening event to stdout.
 */

import { existsSync, readFileSync } from "node:fs";
import { simulation } from "@simulacrum/github-api-simulator";

interface ListeningEvent {
  event: "listening";
  port: number;
}

interface ErrorEvent {
  event: "error";
  message: string;
}

type ServerEvent = ListeningEvent | ErrorEvent;

function emit(event: ServerEvent): void {
  console.log(JSON.stringify(event));
}

function loadConfig(configPath: string): unknown {
  if (!existsSync(configPath)) {
    throw new Error(`Config file not found: ${configPath}`);
  }

  const content = readFileSync(configPath, "utf-8");
  try {
    return JSON.parse(content) as unknown;
  } catch {
    throw new Error(`Invalid JSON in config file: ${configPath}`);
  }
}

async function main(): Promise<void> {
  const configPath = process.argv[2];

  if (!configPath) {
    emit({ event: "error", message: "Usage: github-sim-server <config-path>" });
    process.exit(1);
  }

  let config: unknown;
  try {
    config = loadConfig(configPath);
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    emit({ event: "error", message });
    process.exit(1);
  }

  const initialState =
    typeof config === "object" && config !== null && "initialState" in config
      ? (config as { initialState: unknown }).initialState
      : config;

  // Narrow the input to the exact `initialState` type expected by simulation options.
  const sim = simulation({
    initialState: initialState as Parameters<typeof simulation>[0] extends {
      initialState?: infer T;
    }
      ? T
      : never,
  });

  const listening = await sim.listen(0);

  if (listening.port === undefined || listening.port === null) {
    emit({ event: "error", message: "Server failed to bind to a port" });
    process.exit(1);
  }

  emit({ event: "listening", port: listening.port });

  const shutdown = async (): Promise<void> => {
    try {
      await listening.ensureClose();
      process.exit(0);
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      emit({ event: "error", message: `Shutdown error: ${message}` });
      process.exit(1);
    }
  };

  process.on("SIGINT", () => void shutdown());
  process.on("SIGTERM", () => void shutdown());
}

main().catch((err: unknown) => {
  const message = err instanceof Error ? err.message : String(err);
  emit({ event: "error", message: `Uncaught error: ${message}` });
  process.exit(1);
});
