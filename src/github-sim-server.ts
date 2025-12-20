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

type HostHeaders = Record<string, unknown> & { host?: unknown };

type GitHubOwnerTemplate = Record<string, unknown> & { login?: unknown };

type GitHubResponseTemplate = Record<string, unknown> & {
  body?: unknown;
  body_html?: unknown;
  body_text?: unknown;
  closed_by?: unknown;
  full_name?: unknown;
  language?: unknown;
  login?: unknown;
  name?: unknown;
  number?: unknown;
  owner?: unknown;
  repos_url?: unknown;
  repository_url?: unknown;
  url?: unknown;
  user?: unknown;
};

const API_HOST_PREFIXES = [
  "https://api.github.com",
  "http://api.github.com",
  "http://localhost:3300",
  "https://localhost:3300",
] as const;

function replaceApiHost(value: string, host: string): string {
  for (const prefix of API_HOST_PREFIXES) {
    if (value.startsWith(prefix)) {
      return `${host}${value.slice(prefix.length)}`;
    }
  }
  return value;
}

function replaceInStrings(value: unknown, replacer: (value: string) => string): unknown {
  if (typeof value === "string") {
    return replacer(value);
  }

  if (Array.isArray(value)) {
    return value.map((entry) => replaceInStrings(entry, replacer));
  }

  if (typeof value === "object" && value !== null) {
    const result: Record<string, unknown> = {};
    for (const [key, entry] of Object.entries(value)) {
      result[key] = replaceInStrings(entry, replacer);
    }
    return result;
  }

  return value;
}

function cloneJson<T>(value: T): T {
  return JSON.parse(JSON.stringify(value)) as T;
}

function ensureRepositoryLanguage(value: unknown): void {
  if (Array.isArray(value)) {
    for (const entry of value) ensureRepositoryLanguage(entry);
    return;
  }

  if (typeof value !== "object" || value === null) return;

  const record = value as GitHubResponseTemplate;
  if (typeof record.full_name === "string" && !("language" in record)) {
    record.language = null;
  }

  for (const entry of Object.values(record)) {
    ensureRepositoryLanguage(entry);
  }
}

function resolveRequestHost(request: { protocol?: string; headers?: unknown }): string {
  const protocol =
    typeof request.protocol === "string" && request.protocol.length > 0 ? request.protocol : "http";
  const headers =
    typeof request.headers === "object" && request.headers !== null
      ? (request.headers as HostHeaders)
      : {};
  const hostHeader = typeof headers.host === "string" ? headers.host : "localhost";
  return `${protocol}://${hostHeader}`;
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
    extend: {
      openapiHandlers: (simulationStore) => ({
        "orgs/get": async (context, request, response) => {
          const { org } = context.request.params;
          const state = simulationStore.store.getState();
          const orgs = simulationStore.schema.organizations.selectTableAsList(state);
          const found = orgs.find((entry) => entry.login === org);
          if (!found) {
            response.status(404).send("Not Found");
            return;
          }

          const host = resolveRequestHost(request);
          const { status, mock } = context.api.mockResponseForOperation(
            context.operation.operationId ?? "orgs/get",
          );

          const template = cloneJson(mock as GitHubResponseTemplate);
          const oldLogin = typeof template.login === "string" ? template.login : "github";
          template.login = org;

          const patched = replaceInStrings(template, (value) =>
            replaceApiHost(
              value.replaceAll(oldLogin, org).replaceAll("/orgs/github", `/orgs/${org}`),
              host,
            ),
          ) as GitHubResponseTemplate;

          patched.url = `${host}/orgs/${org}`;
          patched.repos_url = `${host}/orgs/${org}/repos`;

          response.status(status).json(patched);
        },
        "users/get-by-username": async (context, request, response) => {
          const { username } = context.request.params;
          const state = simulationStore.store.getState();
          const users = simulationStore.schema.users.selectTableAsList(state);
          const found = users.find((entry) => entry.login === username);
          if (!found) {
            response.status(404).send("Not Found");
            return;
          }

          const host = resolveRequestHost(request);
          const { status, mock } = context.api.mockResponseForOperation(
            context.operation.operationId ?? "users/get-by-username",
          );

          const template = cloneJson(mock as GitHubResponseTemplate);
          const oldLogin = typeof template.login === "string" ? template.login : "octocat";
          template.login = username;

          const patched = replaceInStrings(template, (value) =>
            replaceApiHost(value.replaceAll(oldLogin, username), host),
          ) as GitHubResponseTemplate;

          patched.url = `${host}/users/${username}`;
          patched.repos_url = `${host}/users/${username}/repos`;

          response.status(status).json(patched);
        },
        "repos/list-for-user": async (context, request, response) => {
          const { username } = context.request.params;
          const state = simulationStore.store.getState();
          const users = simulationStore.schema.users.selectTableAsList(state);
          const orgs = simulationStore.schema.organizations.selectTableAsList(state);
          const isKnownUser = users.some((entry) => entry.login === username);
          const isKnownOrg = orgs.some((entry) => entry.login === username);
          if (!isKnownUser && !isKnownOrg) {
            response.status(404).send("Not Found");
            return;
          }

          const host = resolveRequestHost(request);
          const repos = simulationStore.schema.repositories
            .selectTableAsList(state)
            .filter((repo) => repo.owner === username);

          const results = repos.map((repo) => {
            const { mock } = context.api.mockResponseForOperation("repos/get");
            const template = cloneJson(mock as GitHubResponseTemplate);
            const templateOwner = template.owner as GitHubOwnerTemplate | undefined;
            const oldOwner =
              typeof templateOwner?.login === "string" ? templateOwner.login : "octocat";
            const oldName = typeof template.name === "string" ? template.name : "Hello-World";
            const oldFullName =
              typeof template.full_name === "string"
                ? template.full_name
                : `${oldOwner}/${oldName}`;
            const newFullName = `${username}/${repo.name}`;

            template.name = repo.name;
            template.full_name = newFullName;
            if (typeof template.owner === "object" && template.owner !== null) {
              (template.owner as GitHubOwnerTemplate).login = username;
            }

            const patched = replaceInStrings(template, (value) =>
              replaceApiHost(
                value
                  .replaceAll(oldFullName, newFullName)
                  .replaceAll(oldOwner, username)
                  .replaceAll(oldName, repo.name),
                host,
              ),
            ) as GitHubResponseTemplate;

            if (!("language" in patched)) patched.language = null;
            ensureRepositoryLanguage(patched);
            return patched;
          });

          response.status(200).json(results);
        },
        "repos/get": async (context, request, response) => {
          const { owner, repo } = context.request.params;
          const state = simulationStore.store.getState();
          const repos = simulationStore.schema.repositories.selectTableAsList(state);
          const exists = repos.some((entry) => entry.owner === owner && entry.name === repo);
          if (!exists) {
            response.status(404).send("Not Found");
            return;
          }

          const host = resolveRequestHost(request);
          const { status, mock } = context.api.mockResponseForOperation(
            context.operation.operationId ?? "repos/get",
          );
          const template = cloneJson(mock as GitHubResponseTemplate);
          const templateOwner = template.owner as GitHubOwnerTemplate | undefined;

          const oldOwner =
            typeof templateOwner?.login === "string" ? templateOwner.login : "octocat";
          const oldName = typeof template.name === "string" ? template.name : "Hello-World";
          const oldFullName =
            typeof template.full_name === "string" ? template.full_name : `${oldOwner}/${oldName}`;
          const newFullName = `${owner}/${repo}`;

          template.name = repo;
          template.full_name = newFullName;
          if (typeof template.owner === "object" && template.owner !== null) {
            (template.owner as GitHubOwnerTemplate).login = owner;
          }

          const patched = replaceInStrings(template, (value) =>
            replaceApiHost(
              value
                .replaceAll(oldFullName, newFullName)
                .replaceAll(oldOwner, owner)
                .replaceAll(oldName, repo),
              host,
            ),
          ) as GitHubResponseTemplate;

          if (!("language" in patched)) patched.language = null;
          ensureRepositoryLanguage(patched);
          response.status(status).json(patched);
        },
        "issues/get": async (context, request, response) => {
          const { owner, repo, issue_number } = context.request.params;
          const host = resolveRequestHost(request);
          const { status, mock } = context.api.mockResponseForOperation(
            context.operation.operationId ?? "issues/get",
          );
          const template = cloneJson(mock as GitHubResponseTemplate);
          const templateUser = template.user as GitHubOwnerTemplate | undefined;

          const issueNumber = Number.parseInt(issue_number, 10);
          if (!Number.isFinite(issueNumber)) {
            response.status(400).send("Bad Request");
            return;
          }

          const oldOwner = typeof templateUser?.login === "string" ? templateUser.login : "octocat";
          const oldRepo =
            typeof template.repository_url === "string"
              ? (template.repository_url.split("/").at(-1) ?? "Hello-World")
              : "Hello-World";

          template.number = issueNumber;
          if (!("body_html" in template)) template.body_html = template.body ?? "";
          if (!("body_text" in template)) template.body_text = template.body ?? "";
          if (!("closed_by" in template)) template.closed_by = null;

          const patched = replaceInStrings(template, (value) =>
            replaceApiHost(value.replaceAll(oldOwner, owner).replaceAll(oldRepo, repo), host),
          ) as GitHubResponseTemplate;

          response.status(status).json(patched);
        },
        "pulls/get": async (context, request, response) => {
          const { owner, repo, pull_number } = context.request.params;
          const host = resolveRequestHost(request);
          const { status, mock } = context.api.mockResponseForOperation(
            context.operation.operationId ?? "pulls/get",
          );
          const template = cloneJson(mock as GitHubResponseTemplate);
          const templateUser = template.user as GitHubOwnerTemplate | undefined;

          const pullNumber = Number.parseInt(pull_number, 10);
          if (!Number.isFinite(pullNumber)) {
            response.status(400).send("Bad Request");
            return;
          }

          const oldOwner = typeof templateUser?.login === "string" ? templateUser.login : "octocat";

          template.number = pullNumber;
          if (!("body_html" in template)) template.body_html = template.body ?? "";
          if (!("body_text" in template)) template.body_text = template.body ?? "";

          const patched = replaceInStrings(template, (value) =>
            replaceApiHost(value.replaceAll(oldOwner, owner), host).replaceAll(
              "/repos/octocat/Hello-World",
              `/repos/${owner}/${repo}`,
            ),
          ) as GitHubResponseTemplate;

          response.status(status).json(patched);
        },
      }),
    },
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
