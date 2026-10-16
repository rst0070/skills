# Boundaries

Where a seam goes, as a decision separate from what goes behind it.

## Cut around decisions likely to change, not around steps

**Rule.** A module hides one design decision that is likely to change: a format, a protocol, a vendor, a storage layout. Modules are not the steps of a process.

**Test.** List the changes likely in the next year. For each, count the modules that would be touched. A good cut confines each change to one.

```ts
// ❌ temporal decomposition: three modules share the file format
reader.ts   // parses the format
transform.ts // assumes the parsed shape
writer.ts   // serialises the format again
```

```ts
// ✅ the format is one decision, hidden in one module
export interface MemoCodec {
  decode(bytes: Uint8Array): Memo;
  encode(memo: Memo): Uint8Array;
}
```

**Breaks when** the "likely change" is speculation. A seam for a change that never comes is interface the reader pays for on every visit. The list of likely changes is evidence, not imagination.

## The time-derivative test

**Rule.** The right seam absorbs the next variant. When a provider is added or renamed, only the adapter and the registry change; callers do not.

**Test.** Add a provider in your head. Which files change? Adapter and registry: right seam. Any caller: wrong seam.

```ts
// ❌ the capability knows every vendor
if (provider === "google") return detectWithDlp(text);
if (provider === "aws") return detectWithMacie(text);
```

```ts
// ✅ the registry absorbs the variant
export const piiBackends = defineRegistry<PiiBackend>([googleDlp, awsMacie]);
export function detect(deps: { backend: PiiBackend }, text: string) { /* ... */ }
```

**Breaks when** the next variant differs in meaning, not mechanism. Then the contract has to change, and callers should change with it. A seam that silently absorbs a semantic difference is lying.

## The deletion test

**Rule.** A module earns its place by concentrating complexity that would otherwise spread across its callers. A module that only forwards is a pass-through.

**Test.** Delete the module in your head. If complexity vanishes, it was pass-through. If complexity reappears across N callers, it was earning its keep.

```ts
// ❌ pass-through: same signature in, same signature out
class MemoService {
  constructor(private repo: MemoRepository) {}
  getById(id: MemoId) { return this.repo.getById(id); }
}
```

**Breaks when** the forwarding layer is the seam itself: a port whose single adapter happens to be thin today. The port stays because it separates core from dependency (see [dependencies.md](dependencies.md)); a service that forwards from core to core does not.

## Depth

**Rule.** A deep module has a lot of behaviour behind a small interface. The interface counts everything a caller must know, not just the method list.

**Test.** For each method and parameter on the interface, name the caller that needs it. Can the interface be reduced (fewer methods, simpler parameters, more hidden) without any caller losing a capability?

```ts
// ❌ the interface is as wide as the implementation
interface Pager { setPageSize(n: number): void; setCursor(c: string): void; fetchNext(): Promise<Row[]>; hasMore(): boolean; reset(): void }
```

```ts
// ✅ one entry, the paging hidden
/** Every row stamped at or after `since`, oldest first. */
async function* rowsSince(since: Instant): AsyncIterable<Row> { /* paging hidden here */ }
```

**Breaks when** depth is faked by stuffing unrelated behaviour behind one door. The interface is small, but the module hides three decisions instead of one, and a change to any of them risks the others.

## The inner surface is narrower than the outer

**Rule.** What the core exposes to a less-trusted or more-general consumer is deliberately smaller than what the adapter behind it can do. Every option on the inner surface has a consumer that needs it.

**Test.** For each option on an inner interface, name the consumer. An option with no consumer is an egress path waiting to be used.

```ts
// adapter can return the matched text; the capability does not offer it
interface PiiBackend { detect(text: string, opts: { includeQuote: boolean }): Promise<Finding[]> }
interface PiiCapability { detect(text: string): Promise<Finding[]> }   // quote never leaves
```

**Breaks when** the narrowing hides something the consumer is entitled to and now has to work around. The narrow surface is a decision about trust and need, recorded at the interface, not a default.

## Product veto

**Rule.** An abstraction that hides what the user chose the provider for is wrong. The provider-specific feature is promoted into the core's vocabulary, named in the core's words, and kept.

**Test.** Does the abstraction erase a difference a user pays for? Then it has abstracted the product away.

```ts
// ✅ a model-specific capability, named in core vocabulary, on purpose
export interface LlmModel {
  id: ModelId;
  /** Models that expose a reasoning phase; the usecase may enable it per task. */
  supportsThinking: boolean;
}
```

**Breaks when** the veto becomes an excuse to pass the vendor's whole option bag through. The promoted feature is one named field in core vocabulary, not `vendorOptions: Record<string, unknown>`.

## Semantic versus operational

**Rule.** A seam exposes what a result means and hides how it was produced. Differences that change meaning are modelled in the contract; differences in production are hidden behind it.

**Test.** Does this difference change what the result means to the caller? Model it. Does it only change how the result was obtained? Hide it.

```ts
// adapter: operational limit, refuses rather than deciding
class DlpBackend implements PiiBackend {
  readonly maxInputChars = 500_000;
  async detect(text: string) { if (text.length > this.maxInputChars) throw new InputTooLarge(); /* ... */ }
}
// core: the semantic decision (how to window, how to merge) lives here
export function detectInWindows(deps: { backend: PiiBackend }, text: string): Promise<Finding[]> { /* ... */ }
```

**Breaks when** an operational difference has semantic consequences the caller must know (a backend that truncates silently changes what "no findings" means). Then it is semantic, and it belongs in the contract.

## Sources

- Parnas, *On the Criteria To Be Used in Decomposing Systems into Modules* (1972). https://blog.acolyer.org/2016/09/05/on-the-criteria-to-be-used-in-decomposing-systems-into-modules/
- Ousterhout, *A Philosophy of Software Design*: deep modules, pass-through methods, temporal decomposition. https://danlebrero.com/2021/02/24/philosophy-of-software-design-summary/
- Feathers, *Working Effectively with Legacy Code*: a seam is a place to alter behaviour without editing in that place. https://understandlegacycode.com/blog/key-points-of-working-effectively-with-legacy-code/
