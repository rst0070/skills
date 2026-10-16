# Ownership

Who may write. Every name, every state, and every effect has one owner. When two designs fail in mirrored ways, the axis being optimised is the wrong one, and the hidden axis is usually ownership.

## One owner per write path

**Rule.** Each piece of state has one module that writes it. A new mode of change becomes a new action on that owner, never a second writer.

**Test.** For each table, aggregate, or store, list the modules that write it. One.

```ts
// ❌ a second endpoint writes the same aggregate; invariants can now diverge
router.post("/memos/:id/archive", async (req) => { await db.update("memo", { archived: true }).where({ id: req.params.id }); });
router.post("/memos/:id", async (req) => { await memoService.update(req.params.id, req.body); });
```

```ts
// ✅ the owner gains an action
class MemoWriter {
  update(id: MemoId, patch: MemoPatch): Promise<void>;
  archive(id: MemoId): Promise<void>;   // same invariants, same place
}
```

**Breaks when** the "owner" becomes a god module because every write in the system lands on it. Ownership is per state, and a module that owns everything owns nothing. Split the state, not the writer.

## Single door to every mutable store

**Rule.** A mutable store (a cache, a key-value namespace, a queue) has one module that builds its keys and one module that enforces its invariants. Usually the same module.

**Test.** Search for the store's key prefix. One file builds keys. Search for writes. One file performs them.

```ts
// ❌ keys assembled at every call site
await redis.set(`alias:${tenant}:${hash}`, value, { EX: 3600 });
```

```ts
// ✅ the only place keys are built, the only enforcer of their invariants
export const aliasKeys = {
  entry: (tenant: TenantId, hash: AliasHash) => `alias:${tenant}:${hash}` as AliasKey,
};
export class AliasVault {
  /** Single door: the only writer of alias entries. Mint is atomic; TTL is required. */
  mint(tenant: TenantId, plaintext: string, ttl: Seconds): Promise<Alias>;
}
```

**Breaks when** reads also have to go through the door and the door becomes a bottleneck. Reads can be wide; writes stay narrow. The invariant is about who changes the state.

## Mixed-trust records: host-owned fields are stripped before merge

**Rule.** When a record is assembled from a trusted host and a less-trusted handler, the fields the host relies on are stripped from the handler's contribution before the merge, so the handler cannot forge them.

**Test.** Can a less-trusted writer set a field the host branches on, audits by, or bills from?

```ts
// ❌ the handler can forge the audit fields
await auditLog.create({ ...run.metadata, path, action, source });
```

```ts
// ✅ host-owned keys cannot come from cargo
const HOST_AUDIT_KEYS = new Set(["path", "action", "source", "failedOpen"]);
const cargo = Object.fromEntries(Object.entries(run.metadata).filter(([k]) => !HOST_AUDIT_KEYS.has(k)));
await auditLog.create({ ...cargo, path, action, source, failedOpen });
```

**Breaks when** the set of host-owned keys lives in two places (the strip and the write). It is one constant, and the write uses it too.

## Composition root: construction apart from distribution

**Rule.** One place decides which concrete implementations exist. A separate place decides which consumer sees which slice. The container implements each consumer's own `Deps` interface, so no consumer can reach a dependency it was not given.

**Test.** Does any consumer receive more than its `Deps` type declares? Is any concrete class constructed anywhere other than the root?

```ts
// ❌ consumers reach into one global bag
export const container = { memos: new SqliteMemoRepository(db), remote: new SupabaseRemote(client), llm: new LlamaLlm() };
function SyncScreen() { const { memos, remote, llm } = container; /* llm is reachable but not needed */ }
```

```ts
// ✅ construction in one place, distribution by interface
interface SyncDeps { memos: MemoRepository; remote: RemotePort }
interface ChatDeps { llm: LlmPort; memos: MemoRepository }
class Container implements SyncDeps, ChatDeps {
  private constructor(readonly memos: MemoRepository, readonly remote: RemotePort, readonly llm: LlmPort) {}
  static async create(config: Config): Promise<Container> { /* the only place concretes are built */ }
}
function SyncProvider({ deps }: { deps: SyncDeps }) { /* sees only SyncDeps */ }
```

**Breaks when** the project is small enough that the root is the whole program. One file constructing three things is still a composition root; the rule is about where construction happens, not how much ceremony surrounds it.

## The ownership question

**Rule.** Every name, state, and effect introduced by a change has one answer to "who owns this?". No single owner means the design is not finished.

**Test.** List the names, states, and effects the diff introduces. For each, name the owner. Any blank or any "both" sends the design back.

```ts
// ❌ two handlers co-own a value smuggled through an object neither owns
beforeSave((message) => { message._pendingAudit = buildAudit(message); });
afterSave((message) => { commit(message._pendingAudit); });
```

```ts
// ✅ one owner, one entry, the state held by the owner
class HookEngine {
  /** The only legacy-facing entry. Owns the pending audit for the duration of the save. */
  async onMessageSave(message: Message): Promise<void> { const audit = this.evaluate(message); await this.commit(audit); }
}
```

**Breaks when** ownership is forced onto a module that has no business knowing about the state, just to make the count come out to one. The owner is the module whose contract the state belongs to. If none exists, that is the missing module.

## Sources

- Cockburn, *Hexagonal Architecture*: the composition root is where adapters are plugged into ports. https://alistair.cockburn.us/hexagonal-architecture/
- Hickey, *The Value of Values*: state is value plus time; place-oriented programming is what happens when writers are not owned. https://github.com/matthiasn/talk-transcripts/blob/master/Hickey_Rich/ValueOfValues.md
