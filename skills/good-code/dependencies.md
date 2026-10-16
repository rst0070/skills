# Dependencies

Which way may dependencies point. The answer is always the same: inward. Adapters, frameworks, runtimes, and storage depend on the core. The core depends on nothing it does not own.

## The core owns its ports

**Rule.** The core declares the interfaces it needs, in its own vocabulary. Adapters implement them. The core never imports an adapter, a framework, a vendor SDK, or a runtime.

**Test.** Follow every import from the core directory. The walk never leaves the core directory.

```ts
// ❌ core/usecase/signIn.ts
import { createClient } from "@supabase/supabase-js";
export async function signIn(email: string, password: string) {
  const supabase = createClient(URL, KEY);
  const { error } = await supabase.auth.signInWithPassword({ email, password });
  if (error?.code === "invalid_credentials") { /* ... */ }
}
```

```ts
// ✅ core/port/account.ts — the core's own description of the conversation
export interface AccountPort {
  /** Rejects with AccountError; a vendor error type never crosses this line. */
  signIn(credentials: Credentials): Promise<Session>;
}

// ✅ core/usecase/signIn.ts
export function signIn(deps: { account: AccountPort }) {
  return (credentials: Credentials) => deps.account.signIn(credentials);
}

// ✅ adapter/supabase/account.ts — implements the port, owns the SDK
export class SupabaseAccount implements AccountPort { /* ... */ }
```

**Breaks when** the port mirrors the vendor API one method for one. Then the vendor has leaked through the port's shape and the core still has to know the vendor to use it. A port is written in the core's words and is smaller than the vendor's surface.

## One implementation is enough to justify a port

**Rule.** A port is not there so the adapter can be swapped. It is there so the core can be read, reviewed, and changed without understanding the dependency. With the port, a change to business logic and a change to the vendor integration are two diffs, each judged on its own terms. Without it, as the code grows, business logic and dependency become one thing, and the one thing is unreviewable without knowing both.

**Test.** Take a change that touches the core. Can a reviewer judge it correct without opening the adapter? Take a change that touches the adapter. Can a reviewer judge it correct without opening the core?

```ts
// ❌ one thing: the rule and the SQL are inseparable
export async function recentMemos(db: Database, limit: number) {
  const rows = await db.execute("select * from memo where archived = 0 order by updated_at desc limit ?", [limit]);
  return rows.map(toMemo);
}
```

```ts
// ✅ two things, two diffs
// core/repository/memo.ts
export interface MemoRepository {
  /** Non-archived memos, newest first, at most `limit`. */
  recent(limit: number): Promise<Memo[]>;
}
// adapter/sqlite/memoRepository.ts
export class SqliteMemoRepository implements MemoRepository { /* the SQL lives here */ }
```

**Breaks when** the thing behind the port is itself core: pure computation the core owns. A port around a function the core could just call is indirection. A port wraps something the core must not need to learn.

## Loadable in the test runner is the criterion for a parameter

**Rule.** Anything that cannot be loaded in the test runner (a native module, a network client, a device runtime, a process boundary) enters the core as a parameter through a port, never as an import.

**Test.** Run the core's tests with the network off and no native modules linked. They pass unchanged.

```ts
// ❌ core/usecase/extractFacts.ts
import { initLlama } from "llama.rn";
```

```ts
// ✅ core/port/llm.ts
export interface LlmPort {
  complete(prompt: Prompt): Promise<Completion>;
}
// core/usecase/extractFacts.ts
export function extractFacts(deps: { llm: LlmPort }) { /* ... */ }
// adapter/llama/llm.ts — the only file that imports llama.rn
```

**Breaks when** the test runner is taught to load everything (module mocks for native code). That hides the dependency instead of drawing it. The seam exists in the type, or it does not exist.

## Ports face outward, repositories face inward

**Rule.** A port describes a conversation with the outside world: auth, network, crypto, a clock. A repository persists the core's own entities and speaks only in those entities. The core owns both; the distinction is which vocabulary the interface is written in.

**Test.** A repository method takes and returns core entities. A port method describes a purposeful conversation with the world. If an interface does both, it is two interfaces.

```ts
// core/port/clock.ts            — outward: the world's time
export interface ClockPort { now(): Instant }
// core/repository/memo.ts       — inward: our entity
export interface MemoRepository { upsert(memo: Memo): Promise<void> }
```

**Breaks when** the entities are just table rows. Then the "repository" is a storage wrapper with no entity behind it. Call it a port and let the core decide what the entity is.

## Each vendor SDK lives in exactly one module

**Rule.** A vendor SDK is imported by one file. That file is the adapter.

**Test.** Search for the SDK's import. One result.

**Breaks when** the vendor is the house framework and cannot be confined. Then the leak is written down as a known gap next to the design it compromises, not pretended absent. A labelled leak can be reviewed; a silent one cannot.

## Decisions in the core, effects at the edge

**Rule.** Core functions decide. The shell performs I/O and makes no decisions. Every branch belongs to the core; every `await` on the world belongs to the shell.

**Test.** If a core test needs a mock, logic has leaked into the shell. If the shell has a branch, it stole a decision from the core.

```ts
// ❌ shell decides
async function runSync() {
  const session = await auth.session();
  if (!session) return;               // a decision, invisible to core tests
  await sync.run(session);
}
```

```ts
// ✅ core decides, as data; shell carries it out
type CycleResult = { ran: true; pushed: number } | { ran: false; reason: "no-session" | "offline" };
export function planCycle(input: { session: Session | null; online: boolean }): CyclePlan { /* ... */ }
```

**Breaks when** the next decision depends on the result of the effect (a retry loop, a paginated fetch). Then the loop is shell, and the per-step decision is a core function the loop calls.

## A runtime owned by no adapter gets its own layer

**Rule.** When two adapters need the same constructed thing (one HTTP client, one database handle), neither owns it. It gets its own layer that both adapters consume.

**Test.** Search for where the client is constructed. One place, outside every adapter.

**Breaks when** the two adapters genuinely need different instances (different credentials, different pools). Then there are two things, not one shared thing.

## Sources

- Parnas, *On the Criteria To Be Used in Decomposing Systems into Modules* (1972): modules hide design decisions. https://blog.acolyer.org/2016/09/05/on-the-criteria-to-be-used-in-decomposing-systems-into-modules/
- Cockburn, *Hexagonal Architecture*: the application works without a UI or a database; a port is a purposeful conversation. https://alistair.cockburn.us/hexagonal-architecture/
- Bernhardt, *Boundaries*: functional core, imperative shell. https://www.destroyallsoftware.com/talks/boundaries
