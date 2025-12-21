# Configuring Biome 2.3 with `biome.json`

Biome’s configuration looks deceptively small until you realize it’s a whole
toolchain hiding in a JSON file: **formatter**, **linter**, and **assist**
(code actions). Biome enables all three by default, and you toggle them with
`<tool>.enabled`. ([Biome][1])

Biome expects a config named **`biome.json`** (strict JSON) or
**`biome.jsonc`** (JSON-with-comments). For a plain `biome.json`, you must
avoid comments and trailing commas. Biome projects typically put this file at
the repo root next to `package.json`. ([Biome][1])

______________________________________________________________________

## How Biome finds your config

Biome uses **auto-discovery**: it starts in the working directory and walks up
parent directories until it finds `biome.json` or `biome.jsonc`. If it finds
nothing, Biome falls back to defaults. If both `biome.json` and `biome.jsonc`
exist in the same directory, Biome chooses `biome.json`. ([Biome][1])

Biome also supports **nested** configs since v2.0.0 (handy in big repos).
([Biome][1])

______________________________________________________________________

## A practical baseline `biome.json` for Biome 2.3

This file aims at a typical JS/TS repo, honours `.gitignore`, formats with
spaces, enables recommended lint rules, and uses the 2.3 “double-bang” ignore
semantics for build output.

```json
{
  "$schema": "https://biomejs.dev/schemas/2.3.8/schema.json",
  "vcs": {
    "enabled": true,
    "clientKind": "git",
    "useIgnoreFile": true,
    "defaultBranch": "main"
  },
  "files": {
    "includes": [
      "**",
      "!**/*.generated.*",
      "!**/generated/**",
      "!!**/dist/**",
      "!!**/build/**",
      "!!**/.next/**"
    ]
  },
  "formatter": {
    "indentStyle": "space",
    "indentWidth": 2,
    "lineWidth": 100
  },
  "linter": {
    "rules": {
      "recommended": true
    }
  },
  "assist": {
    "actions": {
      "source": {
        "organizeImports": "on"
      }
    }
  },
  "javascript": {
    "formatter": {
      "quoteStyle": "single"
    }
  }
}
```

A few important notes about what you just pasted:

- Biome publishes a JSON schema and lets you reference either a local file in
  `node_modules` or the hosted schema URL; the example above uses the hosted
  form. ([Biome][2])
- `extends` exists if you want to split or share config; I’ll cover it below.
  ([Biome][2])
- `"organizeImports": "on"` lives under `assist.actions.source`. ([Biome][3])

______________________________________________________________________

## The shape of the config: global vs language-specific

Biome organizes options around the tools it provides (formatter/linter/assist).
Put cross-language settings under the tool key (e.g. `formatter.lineWidth`).
Put language-specific settings under `<language>.<tool>` (e.g.
`javascript.formatter.quoteStyle`) and Biome will override the general value
for that language. ([Biome][1])

Biome lumps **TypeScript, JSX, TSX** under the `javascript` language key.
([Biome][1])

______________________________________________________________________

## `$schema`: make editors smarter, and keep yourself honest

Biome’s schema improves autocomplete and validation in editors.

You can point `$schema` at:

- the schema inside `node_modules/@biomejs/biome/configuration_schema.json`, or
- the hosted schema at `https://biomejs.dev/schemas/<version>/schema.json`.
  ([Biome][2])

I recommend using the hosted schema that matches your installed Biome version
(e.g. `2.3.8` in the example).

______________________________________________________________________

## Selecting files: CLI, `files.includes`, and VCS ignores

Biome gives you three levers:

1. **CLI selection** (what you pass to `biome check …` / `biome format …`)
2. **Configuration allow/deny rules** (`files.includes`)
3. **VCS ignore rules** (`.gitignore`, plus `.ignore`) when you enable them

### `files.includes`: the allowlist (with ordered exceptions)

`files.includes` takes glob patterns for files to process; if a **folder**
matches, Biome processes everything inside it. ([Biome][2])

It also supports **ordered** negated patterns that start with `!`. You must
include `**` first when you want “everything except …”, otherwise the negation
won’t match anything. ([Biome][2])

Example:

```json
{
  "files": {
    "includes": ["**", "!**/*.test.js", "**/special.test.js", "!test"]
  }
}
```

This expresses “include everything, exclude test files, re-include one special
file, and exclude the `test` directory”. ([Biome][2])

Also: Biome ignores `node_modules/` regardless of `files.includes`. ([Biome][2])

### The Biome 2.3 ignore twist: `!` vs `!!`

Biome 2.3 distinguishes between:

- `!pattern`: exclude from formatter/linter runs, **but keep the path indexed**
  for project-wide analysis (module graph / TypeScript inference). ([Biome][2])
- `!!pattern`: “force-ignore” a path from **project-related operations** (so
  Biome won’t index it for module graph/type inference either). ([Biome][1])

This matters if you enable rules/actions that rely on whole-project knowledge.
`!` lets you keep type information from generated files without letting them
spam lint/format; `!!` lets you completely drop heavy output folders like
`dist/` to avoid slowness or memory issues. ([Biome][2])

### “Protected files” Biome refuses to touch

Biome always ignores some lockfiles (it calls them “protected files”), so you
won’t get diagnostics there even if you include them. The current list in the
guide includes `composer.lock`, `npm-shrinkwrap.json`, `package-lock.json`, and
`yarn.lock`. ([Biome][1])

### Honour `.gitignore`: `vcs.useIgnoreFile`

If you want Biome to follow your repo’s ignore rules, enable VCS integration:

- Set `vcs.enabled: true`
- Set `vcs.clientKind: "git"`
- Set `vcs.useIgnoreFile: true`

When `vcs.useIgnoreFile` is true, Biome ignores files in the VCS ignore files
*and* in `.ignore` files, including nested ignore files. ([Biome][2])

If you plan to use “changed files” workflows, set `vcs.defaultBranch` so Biome
knows what “main” means in your repo. ([Biome][2])

______________________________________________________________________

## Formatter: the knobs you actually touch

Biome exposes a small set of global formatting options; the usual suspects
include:

- `formatter.indentStyle`: `"tab"` or `"space"` (default `"tab"`) ([Biome][2])
- `formatter.indentWidth`: indentation size (default `2`, ignored when
  `indentStyle` is `"tab"`) ([Biome][2])
- `formatter.lineWidth`: maximum line length (default `80`) ([Biome][2])

Language overrides go under e.g. `javascript.formatter.*`, and they override
the global `formatter.*` values. ([Biome][1])

______________________________________________________________________

## Linter: recommended rules, groups, and when to enable project-wide analysis

### Start with recommended rules

`linter.rules.recommended` enables the recommended rules across all groups, and
it defaults to `true`. ([Biome][2])

So the boring baseline is:

```json
{
  "linter": {
    "rules": {
      "recommended": true
    }
  }
}
```

### Opt into a specific group (example: `nursery`)

Biome lets you enable recommended rules for a specific group, e.g. `nursery`.
([Biome][2])

```json
{
  "linter": {
    "rules": {
      "nursery": {
        "recommended": true
      }
    }
  }
}
```

### Domains: framework- or project-aware rules

Biome’s **domains** let you turn on rule sets for ecosystems
(React/Next/Vue/etc.) and for project-wide analysis.

For example, enabling the Next.js domain recommended rules looks like:

```json
{
  "linter": {
    "domains": {
      "next": "recommended"
    }
  }
}
```

([Biome][2])

One domain deserves special caution: **`project`**. Rules in the `project`
domain do module-graph and type-informed analysis. When you enable them, Biome
scans the entire project and that scan has a performance impact. ([Biome][2])

That interacts directly with your ignore strategy: use `!` for “don’t
lint/format but keep indexed for types”, and use `!!` for “don’t even index
this folder”. ([Biome][2])

______________________________________________________________________

## Assist: auto-fixes and code actions

Biome’s “assist” tool holds automated actions. A common one: organize imports.

Enable it like this:

```json
{
  "assist": {
    "actions": {
      "source": {
        "organizeImports": "on"
      }
    }
  }
}
```

([Biome][3])

______________________________________________________________________

## Overrides: different rules for different globs

When one part of your tree needs different parser options / formatter / linter
settings, use `overrides`.

The configuration reference shows overrides shaped like an array, each with its
own `includes` and per-language tweaks. ([Biome][2])

A practical example: VS Code settings often contain comments, so you might
allow JSON comments only under `.vscode/**`:

```json
{
  "overrides": [
    {
      "includes": [".vscode/**"],
      "json": {
        "parser": {
          "allowComments": true
        }
      }
    }
  ]
}
```

([Biome][2])

(Keep this out of your root JSON parser settings unless you truly want comments
everywhere.)

______________________________________________________________________

## Nested configs and monorepos: `root` and `extends`

### `root`

By default, every config file counts as a root. If you create a **nested**
config, set `"root": false` in the nested file or Biome will throw an error.
([Biome][2])

### `extends`

`extends` lets you layer config files. Biome applies configs in the `extends`
list and then applies the current file, so put paths in order from “least
relevant” to “most relevant”. ([Biome][2])

Since v2, `extends` also accepts a special string value `"//"` for monorepo
setups. ([Biome][2])

______________________________________________________________________

## Well-known files: JSON that isn’t quite JSON

Biome treats some filenames as “well-known” and adjusts parsing accordingly
(think `tsconfig.json`, `.eslintrc.json`, Babel/TS configs, etc.). The guide
explicitly calls out that these filenames influence whether Biome allows
comments / trailing commas, and it lists several families (TypeScript configs,
ESLint configs, Babel configs, etc.). ([Biome][1])

This saves you from hand-authoring a pile of overrides… most of the time.

______________________________________________________________________

## Mental model: how to avoid confusing yourself

- Use `files.includes` as the **single source of truth** for what Biome should
  even consider. ([Biome][2])
- Use `!…` when you still need indexing for type/module graph correctness
  (generated types, vendor typings, etc.). ([Biome][2])
- Use `!!…` for heavy output folders you never want Biome to index (dist/build
  caches). ([Biome][2])
- Enable `vcs.useIgnoreFile` so your `.gitignore` drives the boring stuff.
  ([Biome][2])
- Treat `linter.domains.project` as a deliberate choice: it buys you smarter
  rules, and it costs project scanning time. ([Biome][2])

Biome gives you sharp tools; the trick is pointing the sharp edges at `dist/`
instead of your shins.

[1]: <https://biomejs.dev/guides/configure-biome/> "Configure Biome | Biome"
[2]: <https://biomejs.dev/reference/configuration/> "Configuration | Biome"
[3]: <https://biomejs.dev/es/guides/getting-started/> "Primeros pasos | Biome"
