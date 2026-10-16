# Contracts

What a caller must know, and nothing more. A component is a black box when its typed inputs and outputs are enough to use it correctly.

## The interface is everything the caller must know

**Rule.** The interface includes the types, the invariants, the ordering, the error modes, and the cost. Whatever the signature cannot carry, the contract comment carries, in a few lines. Anything the reader needs only once inside the box is not interface; it is implementation.

**Test.** Can the next reader predict the behaviour from the signature and its comment without opening the implementation?

```ts
// ❌ the signature says nothing; the reader must open it
function list(opts: Record<string, unknown>): Promise<unknown[]>;
```

```ts
// ✅ types carry the shape; the comment carries what types cannot
/** Rows stamped at or after `since`, oldest first, at most `limit`.
 *  The order is load-bearing: the next page starts at the last row's stamp. */
function rowsSince(since: Instant, limit: number): Promise<MemoRow[]>;
```

**Breaks when** the contract comment grows past a few lines. That is not a comment problem; the interface is doing too much. Deepen the module instead of explaining it harder.

## Free types are debt

**Rule.** `any`, `unknown` at a seam, `Record<string, unknown>`, and `as SomeRow[]` casts are untyped holes. Each one is named with the shape it should have.

**Test.** Search the adapters for `as ` and `unknown`. Each hit is either a named debt or a labelled cargo field.

```ts
// ❌ the wire shape is trusted and nothing says so
const { data } = await client.from("memo").select("*");
return data as MemoRow[];
```

```ts
// ✅ the shape is parsed once, at the seam
const rows = MemoRowSchema.array().parse(data);   // zod, or any parser that returns the typed value
return rows;
```

**Breaks when** the value is genuinely opaque cargo the core never branches on. Then the type says so explicitly (`cargo: JsonValue`) and nothing downstream reaches into it. See [vocabulary.md](vocabulary.md).

## Parse, don't validate

**Rule.** A check that returns a boolean throws away what it learned. A parser returns a richer type that keeps the proof, so downstream code cannot forget the check.

**Test.** Is any invariant checked twice? Is any invariant checked once and then not carried by the type?

```ts
// ❌ validated, then forgotten: every consumer takes a string again
function isEmail(s: string): boolean;
function sendWelcome(email: string): Promise<void>;
```

```ts
// ✅ parsed once, carried by the type
type Email = string & { readonly __brand: "Email" };
function parseEmail(s: string): Email | null;
function sendWelcome(email: Email): Promise<void>;
```

**Breaks when** the brand is the only thing enforcing it and anyone can write `s as Email`. A name is not type safety; the parser must be the only way to obtain the type, which means the module boundary must be real.

## Illegal states are unrepresentable

**Rule.** A state is a discriminated union with one variant per state, not a bag of optional fields whose combinations are mostly meaningless.

**Test.** Can a value be constructed that the business says is impossible?

```ts
// ❌ loading with data, error with data, neither: all representable
interface Fetch<T> { loading: boolean; data?: T; error?: Error }
```

```ts
// ✅ exactly the states that exist
type Fetch<T> =
  | { status: "loading" }
  | { status: "ready"; data: T }
  | { status: "failed"; error: FetchError };
```

**Breaks when** the rule set is volatile and every change becomes a cascade of breaking changes across every exhaustive match. That cascade is the point when the rule is stable; when it is not, the union is premature.

## Non-failure outcomes are data

**Rule.** A path that is normal for the business is a value in the result type, not an exception. A sync cycle that did not run, an upsert that lost a race: these are results.

**Test.** Does any thrown error represent a path the caller expects to handle routinely?

```ts
// ❌ a normal outcome dressed as a failure
async function upsertMemos(rows: MemoRow[]): Promise<void> { /* throws ConflictError on a lost race */ }
```

```ts
// ✅ the outcome is the return value
/** Resolves with the ids that won. Losing a race is success with the id absent, never an error. */
async function upsertMemos(rows: MemoRow[]): Promise<MemoId[]>;
```

**Breaks when** "defining the error out of existence" hides a failure someone must act on. A lost race the user should be told about is not success; it is a variant in the result, with a reason.

## Width guard

**Rule.** When two parameters have the same shape, they travel in a named object. When a function needs three fields of a record, it takes the record.

**Test.** Can two arguments be swapped and still type-check?

```ts
// ❌ a transposition of two same-shaped dependencies type-checks
new SyncEngine(remote, memoRepo, syncRepo, keyStore, crypto);
```

```ts
// ✅ named, so a transposition is a compile error
interface SyncEngineDeps { remote: RemotePort; memos: MemoRepository; sync: SyncRepository; keys: KeyStore; crypto: CryptoPort }
new SyncEngine(deps: SyncEngineDeps);
```

**Breaks when** the "record" is a kitchen-sink context object and the function uses one field. Then the wide parameter hides a narrow dependency. Pass what the function needs, as one named thing.

## Lifecycle lives in the type

**Rule.** A state like "obtained but not initialised" has nowhere to live. If a thing must be initialised before use, the only way to obtain it is initialised.

**Test.** Is there a method that must be called before the others? Is there a field that is `undefined` until something happens?

```ts
// ❌ two-phase: a caller can forget the second step
const container = new Container();
await container.initialize();
```

```ts
// ✅ one phase: a container that exists is initialised
class Container {
  private constructor(private readonly deps: Deps) {}
  static async create(config: Config): Promise<Container> { /* ... */ }
}
```

**Breaks when** construction genuinely must be split across time (a handle acquired now, opened later). Then the two phases are two types, and the second type is the only one with the dangerous methods.

## Strict on write, lenient on read

**Rule.** Input the system accepts (requests, configuration) rejects unknown keys so a typo fails loudly. Data the system reads back from its own persistence drops unknown keys with a warning, so an older row never blocks a newer reader.

**Test.** Does a schema change to stored JSON break reads of rows written before the change?

```ts
const HookConfigInput = z.object({ model: ModelId, maxTokens: z.number() }).strict();   // write: typo fails
const StoredVerdict  = z.object({ outcome: Outcome, reason: z.string() }).strip();      // read: unknown keys dropped
```

**Breaks when** lenient reading silently discards a field the reader needed. "Strip with a warning" is lenient; "strip silently" is a lost invariant.

## Sources

- Ousterhout, *A Philosophy of Software Design*: the interface is everything a caller must know; comments carry what the signature cannot. https://danlebrero.com/2021/02/24/philosophy-of-software-design-summary/
- King, *Parse, don't validate*. https://lexi-lambda.github.io/blog/2019/11/05/parse-don-t-validate/
- King, *Names are not type safety*. https://lexi-lambda.github.io/blog/2020/11/01/names-are-not-type-safety/
- Minsky, *Effective ML*: make illegal states unrepresentable. https://blog.janestreet.com/effective-ml-revisited/
- Wlaschin, *Designing with types*. https://fsharpforfunandprofit.com/posts/designing-with-types-making-illegal-states-unrepresentable/
