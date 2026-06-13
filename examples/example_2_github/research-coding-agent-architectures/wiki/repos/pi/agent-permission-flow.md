# pi — Agent permission flow

> Part of [pi](./ARCHITECTURE.md) @ a455f62

## Module purpose

This doc traces how dangerous actions are gated in pi. The headline finding for the comparative study: **pi has no built-in per-tool permission system** — no ask/allow/deny config, no allowlists, no permission modes, no approval prompt before `bash`/`write`/`edit`. This is an explicit design decision, documented in [`docs/security.md`](https://github.com/earendil-works/pi/blob/a455f62f72359f5f2260c16ee3ed653ce968de3d/packages/coding-agent/docs/security.md) and the [README](https://github.com/earendil-works/pi/blob/a455f62f72359f5f2260c16ee3ed653ce968de3d/README.md#L59-L65):

> "Pi does not include a built-in permission system for restricting filesystem, process, network, or credential access. By default, it runs with the permissions of the user and process that launched it." — `README.md` L61

What pi has *instead* are three mechanisms, each covered below:

1. **The `tool_call` extension hook** — a synchronous pre-execution interception point on every tool call that can mutate arguments or block execution. This is the official substrate for user-space permission systems; pi ships example extensions (`permission-gate.ts`, `protected-paths.ts`) that implement classic deny-pattern + approval-dialog flows on top of it.
2. **Project trust** — a startup-time gate controlling whether *project-local configuration* (`.pi/` settings, extensions, skills) is loaded at all. It gates inputs, not tool execution.
3. **OS-level containment** — containers/VMs/sandboxes as the recommended boundary for untrusted work ([`docs/containerization.md`](https://github.com/earendil-works/pi/blob/a455f62f72359f5f2260c16ee3ed653ce968de3d/packages/coding-agent/docs/containerization.md)), explicitly outside pi's process.

## Role in the system

The gating machinery spans two packages. The generic agent loop in `packages/agent` exposes optional `beforeToolCall`/`afterToolCall` hooks on the `Agent` class; the coding-agent app in `packages/coding-agent` installs those hooks once per `AgentSession` and forwards them to the `ExtensionRunner`, which fans out to every loaded extension's `tool_call` handlers. Project trust sits earlier in the lifecycle: `main.ts` resolves it during runtime construction, before project-local extensions are even loaded, so an untrusted repo cannot inject the very extension code that would later sit on the `tool_call` hook.

## Design philosophy: why no built-in gate

`docs/security.md` L27–33 states the rationale: built-in tools run "with the permissions of the pi process," and a partial in-process sandbox "would be easy to misunderstand as a security boundary while still depending on the host shell, filesystem, package managers, credentials, and extension code. Real isolation needs to come from the operating system or a virtualization/container boundary." Project trust is described as "only an input-loading guard" — it "does not make untrusted code, untrusted prompts, or untrusted model output safe" ([security.md L33](https://github.com/earendil-works/pi/blob/a455f62f72359f5f2260c16ee3ed653ce968de3d/packages/coding-agent/docs/security.md)).

For the comparison with opencode/hermes-agent: where those harnesses encode ask/allow/deny policy in core config, pi pushes that entire layer into user-space extensions and the OS.

## Key types & entry points

- `BeforeToolCallResult` ([packages/agent/src/types.ts:L55-L58](https://github.com/earendil-works/pi/blob/a455f62f72359f5f2260c16ee3ed653ce968de3d/packages/agent/src/types.ts#L55-L58)) — `{ block?: boolean; reason?: string }`; returning `{ block: true }` makes the loop emit an error tool result instead of executing.
- `BeforeToolCallContext` ([packages/agent/src/types.ts:L83-L93](https://github.com/earendil-works/pi/blob/a455f62f72359f5f2260c16ee3ed653ce968de3d/packages/agent/src/types.ts#L83-L93)) — assistant message, raw tool call, validated args, current `AgentContext`.
- `prepareToolCall` ([packages/agent/src/agent-loop.ts:L562-L626](https://github.com/earendil-works/pi/blob/a455f62f72359f5f2260c16ee3ed653ce968de3d/packages/agent/src/agent-loop.ts#L562-L626)) — validates args, invokes `config.beforeToolCall`, and short-circuits to an error result on block/abort.
- `AgentSession._installAgentToolHooks` ([packages/coding-agent/src/core/agent-session.ts:L403-L451](https://github.com/earendil-works/pi/blob/a455f62f72359f5f2260c16ee3ed653ce968de3d/packages/coding-agent/src/core/agent-session.ts#L403-L451)) — bridges `Agent.beforeToolCall` → `ExtensionRunner.emitToolCall`.
- `ExtensionRunner.emitToolCall` ([packages/coding-agent/src/core/extensions/runner.ts:L862-L883](https://github.com/earendil-works/pi/blob/a455f62f72359f5f2260c16ee3ed653ce968de3d/packages/coding-agent/src/core/extensions/runner.ts#L862-L883)) — sequential fan-out over extensions; first `block` wins and returns immediately.
- `ToolCallEvent` / `ToolCallEventResult` ([packages/coding-agent/src/core/extensions/types.ts:L806-L865](https://github.com/earendil-works/pi/blob/a455f62f72359f5f2260c16ee3ed653ce968de3d/packages/coding-agent/src/core/extensions/types.ts#L806-L865), [L1020-L1024](https://github.com/earendil-works/pi/blob/a455f62f72359f5f2260c16ee3ed653ce968de3d/packages/coding-agent/src/core/extensions/types.ts#L1020-L1024)) — per-tool typed events (`bash`, `read`, `edit`, `write`, `grep`, `find`, `ls`, custom); `event.input` is mutable in place.
- `ExtensionUIContext` ([packages/coding-agent/src/core/extensions/types.ts:L124-L135](https://github.com/earendil-works/pi/blob/a455f62f72359f5f2260c16ee3ed653ce968de3d/packages/coding-agent/src/core/extensions/types.ts#L124-L135)) — `select`/`confirm`/`input`/`notify` dialogs an extension uses to ask the user mid-gate.
- `resolveProjectTrusted` ([packages/coding-agent/src/core/project-trust.ts:L45-L95](https://github.com/earendil-works/pi/blob/a455f62f72359f5f2260c16ee3ed653ce968de3d/packages/coding-agent/src/core/project-trust.ts#L45-L95)) — the full trust decision waterfall.
- `ProjectTrustStore` / `findNearestTrustEntry` ([packages/coding-agent/src/core/trust-manager.ts:L193-L229](https://github.com/earendil-works/pi/blob/a455f62f72359f5f2260c16ee3ed653ce968de3d/packages/coding-agent/src/core/trust-manager.ts#L193-L229), [L32-L46](https://github.com/earendil-works/pi/blob/a455f62f72359f5f2260c16ee3ed653ce968de3d/packages/coding-agent/src/core/trust-manager.ts#L32-L46)) — file-locked `~/.pi/agent/trust.json`, nearest-ancestor-directory lookup.
- `--approve`/`-a`, `--no-approve`/`-na` ([packages/coding-agent/src/cli/args.ts:L180-L182](https://github.com/earendil-works/pi/blob/a455f62f72359f5f2260c16ee3ed653ce968de3d/packages/coding-agent/src/cli/args.ts#L180-L182)) — one-run trust overrides.
- `/trust` slash command ([packages/coding-agent/src/core/slash-commands.ts:L33](https://github.com/earendil-works/pi/blob/a455f62f72359f5f2260c16ee3ed653ce968de3d/packages/coding-agent/src/core/slash-commands.ts#L33)) — opens `TrustSelectorComponent` to save a persistent decision.

## Data flow 1: tool call → gate → execution/rejection

The runtime gate is a single chokepoint. Every tool call the model emits — built-in or extension-registered — passes through `prepareToolCall` in the agent loop, which calls the optional `beforeToolCall` hook *after* schema validation and *before* execution. In the coding agent, that hook is wired (once, in `_installAgentToolHooks`) to the extension runner, so any loaded extension can veto or rewrite the call. A block never throws into the loop; it is converted to an error tool result that flows back to the LLM as a normal observation.

```mermaid
sequenceDiagram
    autonumber
    participant LLM as 🌐 LLM provider
    participant Loop as agent-loop<br/>`prepareToolCall`
    participant Sess as AgentSession<br/>`beforeToolCall` hook
    participant Run as ExtensionRunner<br/>`emitToolCall`
    participant Ext as Extension handler<br/>(e.g. permission-gate)
    participant U as 👤 User (TUI dialog)
    participant Tool as Tool `execute`

    LLM->>Loop: assistant message with toolCall
    Loop->>Loop: validateToolArguments
    Loop->>Sess: beforeToolCall({toolCall, args})
    Sess->>Run: emitToolCall({type:"tool_call", toolName, input})
    loop each extension, each handler (sequential)
        Run->>Ext: handler(event, ctx)
        opt gate wants approval
            Ext->>U: ctx.ui.select("Allow?", ["Yes","No"])
            U-->>Ext: choice
        end
        Ext-->>Run: undefined | {block:true, reason} | mutate event.input
    end
    alt blocked
        Run-->>Loop: {block:true, reason}
        Loop-->>LLM: error tool result (reason text, isError:true)
    else allowed (possibly mutated args)
        Run-->>Loop: undefined / non-block
        Loop->>Tool: execute(toolCallId, args, signal)
        Tool-->>LLM: tool result
    end
```

Key semantics, from [`docs/extensions.md` L694–L708](https://github.com/earendil-works/pi/blob/a455f62f72359f5f2260c16ee3ed653ce968de3d/packages/coding-agent/docs/extensions.md) and the code:

- **First block wins**: `emitToolCall` returns immediately on the first handler returning `{ block: true }` (runner.ts L875–877). Non-blocking results are overwritten by later handlers.
- **Argument mutation, not replacement**: handlers mutate `event.input` in place; later handlers see earlier mutations; "no re-validation is performed after mutation" (types.ts L851–856).
- **Fail-safe on error**: a throwing `tool_call` handler propagates out of `emitToolCall` (no try/catch there, unlike `tool_result`), and the session hook rethrows — `prepareToolCall`'s catch turns it into an error tool result. Documented as "`tool_call` errors block the tool (fail-safe)" (extensions.md L2559).
- **Parallel-tool caveat**: sibling tool calls from one assistant message are *preflighted sequentially, then executed concurrently*, so a gate sees calls one at a time but cannot rely on sibling results being in session state (extensions.md L698–700).
- **Headless behavior is the extension's job**: `ctx.hasUI` is `true` in TUI and RPC modes, `false` in `--mode json` and `-p` print mode, where UI methods are no-ops backed by `noOpUIContext` (runner.ts L229–246). The shipped gate blocks by default when `!ctx.hasUI`.

## Data flow 2: project trust — the input-loading gate

Trust is resolved once per working directory at runtime construction (`main.ts` L592–630), *before* trust-gated project resources load. Inputs that trigger the gate: a `.pi/` dir in cwd, or `.agents/skills` in cwd or any ancestor (`hasProjectTrustInputs`, trust-manager.ts L174–191). The decision waterfall in `resolveProjectTrusted`:

```mermaid
stateDiagram-v2
    [*] --> Override : --approve / --no-approve
    Override --> Trusted : -a
    Override --> Untrusted : -na
    [*] --> NoInputs : no .pi/ and no .agents/skills
    NoInputs --> Trusted
    [*] --> ExtEvent : project_trust event<br/>(user/global + CLI extensions only)
    ExtEvent --> Trusted : {trusted "yes"}<br/>optional remember→trust.json
    ExtEvent --> Untrusted : {trusted "no"}
    ExtEvent --> Saved : undecided / no handler
    Saved --> Trusted : trust.json nearest<br/>ancestor = true
    Saved --> Untrusted : = false
    Saved --> Default : no entry
    Default --> Trusted : defaultProjectTrust "always"
    Default --> Untrusted : "never"
    Default --> Prompt : "ask" + hasUI
    Default --> Untrusted : "ask" + headless
    Prompt --> Trusted : Trust / Trust parent /<br/>session-only
    Prompt --> Untrusted : Do not trust / cancel
    Trusted --> [*] : load .pi settings, extensions,<br/>skills, packages
    Untrusted --> [*] : skip trust-gated inputs<br/>(AGENTS.md still loads)
```

Notes:

- The `project_trust` extension event lets a user-level extension own the decision programmatically; the first handler returning `"yes"`/`"no"` wins, `"undecided"` falls through (`emitProjectTrustEvent`, runner.ts L197–227).
- Saved decisions live in `~/.pi/agent/trust.json`, keyed by canonical directory, with nearest-ancestor inheritance (`findNearestTrustEntry`) and lockfile-guarded writes. The interactive prompt offers "Trust", "Trust parent folder", "Trust (this session only)", and "Do not trust" variants (`getProjectTrustOptions`, trust-manager.ts L58–88).
- Headless modes (`-p`, `--mode json`, `--mode rpc`) never prompt: `"ask"` resolves to untrusted without UI (project-trust.ts L85–87; security.md L25).
- In an untrusted project the TUI shows: "This project is not trusted. Project .pi resources and packages are ignored. Use /trust to save a trust decision, then restart pi." (interactive-mode.ts L3285).

## Annotated code

### `packages/agent/src/agent-loop.ts` — the block decision point

L581–604: the hook call and the conversion of a block into an error tool result that the LLM sees as a failed tool.

```ts title="packages/agent/src/agent-loop.ts (L581-L604)"
		if (config.beforeToolCall) {
			const beforeResult = await config.beforeToolCall(
				{
					assistantMessage,
					toolCall,
					args: validatedArgs,
					context: currentContext,
				},
				signal,
			);
			if (signal?.aborted) {
				return {
					kind: "immediate",
					result: createErrorToolResult("Operation aborted"),
					isError: true,
				};
			}
			if (beforeResult?.block) {
				return {
					kind: "immediate",
					result: createErrorToolResult(beforeResult.reason || "Tool execution was blocked"),
					isError: true,
				};
			}
		}
```

[L562-L626](https://github.com/earendil-works/pi/blob/a455f62f72359f5f2260c16ee3ed653ce968de3d/packages/agent/src/agent-loop.ts#L562-L626)

### `packages/coding-agent/src/core/agent-session.ts` — wiring the hook to extensions

L403–423: installed once; reads `this._extensionRunner` at call time so extension reloads swap the runner without reinstalling. A non-`Error` throw is wrapped as "Extension failed, blocking execution" — fail-safe.

```ts title="packages/coding-agent/src/core/agent-session.ts (L404-L423)"
	this.agent.beforeToolCall = async ({ toolCall, args }) => {
			const runner = this._extensionRunner;
			if (!runner.hasHandlers("tool_call")) {
				return undefined;
			}

			try {
				return await runner.emitToolCall({
					type: "tool_call",
					toolName: toolCall.name,
					toolCallId: toolCall.id,
					input: args as Record<string, unknown>,
				});
			} catch (err) {
				if (err instanceof Error) {
					throw err;
				}
				throw new Error(`Extension failed, blocking execution: ${String(err)}`);
			}
		};
```

[L403-L451](https://github.com/earendil-works/pi/blob/a455f62f72359f5f2260c16ee3ed653ce968de3d/packages/coding-agent/src/core/agent-session.ts#L403-L451)

### `packages/coding-agent/src/core/extensions/runner.ts` — first-block-wins fan-out

L862–883: sequential iteration over extensions and handlers; an early return on `block` means later gates never run for a vetoed call.

```ts title="packages/coding-agent/src/core/extensions/runner.ts (L862-L883)"
	async emitToolCall(event: ToolCallEvent): Promise<ToolCallEventResult | undefined> {
		const ctx = this.createContext();
		let result: ToolCallEventResult | undefined;

		for (const ext of this.extensions) {
			const handlers = ext.handlers.get("tool_call");
			if (!handlers || handlers.length === 0) continue;

			for (const handler of handlers) {
				const handlerResult = await handler(event, ctx);

				if (handlerResult) {
					result = handlerResult as ToolCallEventResult;
					if (result.block) {
						return result;
					}
				}
			}
		}

		return result;
	}
```

[L862-L883](https://github.com/earendil-works/pi/blob/a455f62f72359f5f2260c16ee3ed653ce968de3d/packages/coding-agent/src/core/extensions/runner.ts#L862-L883)

### `packages/coding-agent/examples/extensions/permission-gate.ts` — the canonical user-space approval flow

The whole shipped example (L10–34): regex denylist on `bash`, approval dialog when a UI exists, block-by-default headless. This is pi's equivalent of an "ask" permission mode — opt-in, ~25 lines.

```ts title="packages/coding-agent/examples/extensions/permission-gate.ts (L10-L34)"
export default function (pi: ExtensionAPI) {
	const dangerousPatterns = [/\brm\s+(-rf?|--recursive)/i, /\bsudo\b/i, /\b(chmod|chown)\b.*777/i];

	pi.on("tool_call", async (event, ctx) => {
		if (event.toolName !== "bash") return undefined;

		const command = event.input.command as string;
		const isDangerous = dangerousPatterns.some((p) => p.test(command));

		if (isDangerous) {
			if (!ctx.hasUI) {
				// In non-interactive mode, block by default
				return { block: true, reason: "Dangerous command blocked (no UI for confirmation)" };
			}

			const choice = await ctx.ui.select(`⚠️ Dangerous command:\n\n  ${command}\n\nAllow?`, ["Yes", "No"]);

			if (choice !== "Yes") {
				return { block: true, reason: "Blocked by user" };
			}
		}

		return undefined;
	});
}
```

[Full file on GitHub](https://github.com/earendil-works/pi/blob/a455f62f72359f5f2260c16ee3ed653ce968de3d/packages/coding-agent/examples/extensions/permission-gate.ts)

Sibling example [`protected-paths.ts` L10–30](https://github.com/earendil-works/pi/blob/a455f62f72359f5f2260c16ee3ed653ce968de3d/packages/coding-agent/examples/extensions/protected-paths.ts#L10-L30) blocks `write`/`edit` on a path denylist (`.env`, `.git/`, `node_modules/`) without prompting, and [`confirm-destructive.ts`](https://github.com/earendil-works/pi/blob/a455f62f72359f5f2260c16ee3ed653ce968de3d/packages/coding-agent/examples/extensions/confirm-destructive.ts) shows the same confirm-dialog pattern applied to session lifecycle events (`session_before_switch` → `{ cancel: true }`).

### `packages/coding-agent/src/core/project-trust.ts` — the trust waterfall

L45–95, trimmed: override → no-inputs → extension event → saved store → `defaultProjectTrust` → prompt.

```ts title="packages/coding-agent/src/core/project-trust.ts (L45-L95, trimmed)"
export async function resolveProjectTrusted(options: ResolveProjectTrustedOptions): Promise<boolean> {
	if (options.trustOverride !== undefined) {
		return options.trustOverride;
	}
	if (!hasProjectTrustInputs(options.cwd)) {
		return true;
	}

	if (options.extensionsResult) {
		const { result, errors } = await emitProjectTrustEvent(
			options.extensionsResult,
			{ type: "project_trust", cwd: options.cwd },
			options.projectTrustContext,
		);
		[...]
		if (result) {
			const trusted = result.trusted === "yes";
			if (result.remember === true) {
				options.trustStore.set(options.cwd, trusted);
			}
			return trusted;
		}
	}

	const decision = options.trustStore.get(options.cwd);
	if (decision !== null) {
		return decision;
	}

	switch (options.defaultProjectTrust ?? "ask") {
		case "always":
			return true;
		case "never":
			return false;
		case "ask":
			break;
	}

	if (!options.projectTrustContext.hasUI) {
		return false;
	}

	const selected = await selectProjectTrustOption(options.cwd, options.projectTrustContext);
	[...]
}
```

[Full file on GitHub](https://github.com/earendil-works/pi/blob/a455f62f72359f5f2260c16ee3ed653ce968de3d/packages/coding-agent/src/core/project-trust.ts)

### `packages/coding-agent/src/core/trust-manager.ts` — persistent decisions with ancestor inheritance

L32–46: trust lookups walk up the directory tree so trusting `~/work` covers every repo under it; `~/.pi/agent/trust.json` maps canonical paths to booleans.

```ts title="packages/coding-agent/src/core/trust-manager.ts (L32-L46)"
function findNearestTrustEntry(data: TrustFile, cwd: string): ProjectTrustStoreEntry | null {
	let currentDir = normalizeCwd(cwd);
	while (true) {
		const value = data[currentDir];
		if (value === true || value === false) {
			return { path: currentDir, decision: value };
		}

		const parentDir = dirname(currentDir);
		if (parentDir === currentDir) {
			return null;
		}
		currentDir = parentDir;
	}
}
```

[L32-L46](https://github.com/earendil-works/pi/blob/a455f62f72359f5f2260c16ee3ed653ce968de3d/packages/coding-agent/src/core/trust-manager.ts#L32-L46)
· [`hasProjectTrustInputs` L174-L191](https://github.com/earendil-works/pi/blob/a455f62f72359f5f2260c16ee3ed653ce968de3d/packages/coding-agent/src/core/trust-manager.ts#L174-L191)
· [`ProjectTrustStore` L193-L229](https://github.com/earendil-works/pi/blob/a455f62f72359f5f2260c16ee3ed653ce968de3d/packages/coding-agent/src/core/trust-manager.ts#L193-L229)

## Comparative takeaways

- **No permission modes, no allow/deny config keys.** The only policy-shaped setting is `defaultProjectTrust: "ask" | "always" | "never"` ([settings-manager.ts:L61](https://github.com/earendil-works/pi/blob/a455f62f72359f5f2260c16ee3ed653ce968de3d/packages/coding-agent/src/core/settings-manager.ts#L61), L95) — and it governs config loading, not tool execution. The CLI equivalents are `--approve`/`--no-approve` per run.
- **The permission *mechanism* is generic middleware, not policy.** `beforeToolCall` → `emitToolCall` is exactly where opencode-style ask/allow/deny would sit; pi ships the chokepoint plus example policies and leaves the policy itself to the user.
- **Approval UI is extension-driven**: `ctx.ui.select/confirm` render TUI dialogs in interactive mode ([interactive-mode.ts:L2018-L2023](https://github.com/earendil-works/pi/blob/a455f62f72359f5f2260c16ee3ed653ce968de3d/packages/coding-agent/src/modes/interactive/interactive-mode.ts#L2018-L2023)), travel over the JSON protocol in RPC mode, and are no-ops headless — so "ask the user" degrades to "deny" only if the gate author writes it that way.
- **Failure posture is deny**: gate exceptions block the tool; trust prompts unavailable headless resolve to untrusted.
- **Real boundary = OS**: for untrusted repos the docs prescribe Docker/OpenShell/micro-VMs with minimal mounts and credentials, not in-process restrictions.

## Source files

| File | Ranges | GitHub |
| --- | --- | --- |
| `README.md` | L59-L65 | [link](https://github.com/earendil-works/pi/blob/a455f62f72359f5f2260c16ee3ed653ce968de3d/README.md#L59-L65) |
| `packages/coding-agent/docs/security.md` | L5-L33 | [link](https://github.com/earendil-works/pi/blob/a455f62f72359f5f2260c16ee3ed653ce968de3d/packages/coding-agent/docs/security.md) |
| `packages/coding-agent/docs/extensions.md` | L694-L708, L2557-L2570, L2597-L2599 | [link](https://github.com/earendil-works/pi/blob/a455f62f72359f5f2260c16ee3ed653ce968de3d/packages/coding-agent/docs/extensions.md) |
| `packages/agent/src/agent-loop.ts` | L562-L626 | [link](https://github.com/earendil-works/pi/blob/a455f62f72359f5f2260c16ee3ed653ce968de3d/packages/agent/src/agent-loop.ts#L562-L626) |
| `packages/agent/src/types.ts` | L55-L58, L83-L93, L262 | [link](https://github.com/earendil-works/pi/blob/a455f62f72359f5f2260c16ee3ed653ce968de3d/packages/agent/src/types.ts#L55-L93) |
| `packages/coding-agent/src/core/agent-session.ts` | L395-L451 | [link](https://github.com/earendil-works/pi/blob/a455f62f72359f5f2260c16ee3ed653ce968de3d/packages/coding-agent/src/core/agent-session.ts#L395-L451) |
| `packages/coding-agent/src/core/extensions/runner.ts` | L197-L246, L862-L883 | [link](https://github.com/earendil-works/pi/blob/a455f62f72359f5f2260c16ee3ed653ce968de3d/packages/coding-agent/src/core/extensions/runner.ts#L862-L883) |
| `packages/coding-agent/src/core/extensions/types.ts` | L124-L135, L806-L865, L1020-L1024 | [link](https://github.com/earendil-works/pi/blob/a455f62f72359f5f2260c16ee3ed653ce968de3d/packages/coding-agent/src/core/extensions/types.ts#L806-L865) |
| `packages/coding-agent/src/core/project-trust.ts` | L23-L95 | [link](https://github.com/earendil-works/pi/blob/a455f62f72359f5f2260c16ee3ed653ce968de3d/packages/coding-agent/src/core/project-trust.ts#L45-L95) |
| `packages/coding-agent/src/core/trust-manager.ts` | L32-L46, L58-L88, L174-L229 | [link](https://github.com/earendil-works/pi/blob/a455f62f72359f5f2260c16ee3ed653ce968de3d/packages/coding-agent/src/core/trust-manager.ts#L32-L46) |
| `packages/coding-agent/src/core/settings-manager.ts` | L61, L95, L862-L869 | [link](https://github.com/earendil-works/pi/blob/a455f62f72359f5f2260c16ee3ed653ce968de3d/packages/coding-agent/src/core/settings-manager.ts#L61) |
| `packages/coding-agent/src/cli/args.ts` | L180-L182, L274-L275 | [link](https://github.com/earendil-works/pi/blob/a455f62f72359f5f2260c16ee3ed653ce968de3d/packages/coding-agent/src/cli/args.ts#L180-L182) |
| `packages/coding-agent/src/cli/project-trust.ts` | L7-L62 | [link](https://github.com/earendil-works/pi/blob/a455f62f72359f5f2260c16ee3ed653ce968de3d/packages/coding-agent/src/cli/project-trust.ts#L7-L62) |
| `packages/coding-agent/src/main.ts` | L584-L645 | [link](https://github.com/earendil-works/pi/blob/a455f62f72359f5f2260c16ee3ed653ce968de3d/packages/coding-agent/src/main.ts#L584-L645) |
| `packages/coding-agent/src/modes/interactive/interactive-mode.ts` | L2003-L2049, L2595, L3285 | [link](https://github.com/earendil-works/pi/blob/a455f62f72359f5f2260c16ee3ed653ce968de3d/packages/coding-agent/src/modes/interactive/interactive-mode.ts#L2003-L2049) |
| `packages/coding-agent/src/modes/interactive/components/trust-selector.ts` | L1-L45 | [link](https://github.com/earendil-works/pi/blob/a455f62f72359f5f2260c16ee3ed653ce968de3d/packages/coding-agent/src/modes/interactive/components/trust-selector.ts#L1-L45) |
| `packages/coding-agent/src/core/slash-commands.ts` | L33 | [link](https://github.com/earendil-works/pi/blob/a455f62f72359f5f2260c16ee3ed653ce968de3d/packages/coding-agent/src/core/slash-commands.ts#L33) |
| `packages/coding-agent/examples/extensions/permission-gate.ts` | L1-L34 | [link](https://github.com/earendil-works/pi/blob/a455f62f72359f5f2260c16ee3ed653ce968de3d/packages/coding-agent/examples/extensions/permission-gate.ts) |
| `packages/coding-agent/examples/extensions/protected-paths.ts` | L10-L30 | [link](https://github.com/earendil-works/pi/blob/a455f62f72359f5f2260c16ee3ed653ce968de3d/packages/coding-agent/examples/extensions/protected-paths.ts#L10-L30) |
| `packages/coding-agent/examples/extensions/confirm-destructive.ts` | L10-L28 | [link](https://github.com/earendil-works/pi/blob/a455f62f72359f5f2260c16ee3ed653ce968de3d/packages/coding-agent/examples/extensions/confirm-destructive.ts) |
