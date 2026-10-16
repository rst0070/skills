# Vocabulary

What survives a crossing. Each seam has a small canonical vocabulary that logic may branch on, and everything else is cargo.

## Branch on canonical, carry native as cargo

**Rule.** Business logic branches only on values in the canonical vocabulary. Provider-specific values travel alongside, opaque, so nothing is lost and nothing is depended on. A value is promoted into the vocabulary before any logic branches on it, never at the branch.

**Test.** Search the core for string literals that belong to a vendor. None.

```ts
// ❌ logic pinned to a vendor string
if (finding.infoType === "TAIWAN_ID_NUMBER") mask(finding);
```

```ts
// ✅ canonical for logic, native kept visible
type PiiType = "ssn" | "national-id" | "email" | "provider-specific";
interface PiiTypeRef { type: PiiType; providerSpecificType: string | null }

const TAG_BY_INFO_TYPE: Record<string, PiiType> = { TAIWAN_ID_NUMBER: "national-id", US_SOCIAL_SECURITY_NUMBER: "ssn" };
function toRef(infoType: string): PiiTypeRef {
  return { type: TAG_BY_INFO_TYPE[infoType] ?? "provider-specific", providerSpecificType: infoType };
}
```

**Breaks when** the cargo field becomes a side channel: a `switch` on `providerSpecificType` somewhere downstream. Cargo is opaque by contract, and the contract is enforced by the type being `string`, not an enum.

## The canonical set is smaller than the vendor's

**Rule.** The vocabulary holds only the values logic needs to distinguish. A sentinel (`provider-specific`) catches the rest, and the sentinel must name its native value so nothing is silently dropped.

**Test.** For every member of the canonical set, point at the logic that branches on it. A member nothing branches on is cargo in disguise.

```ts
// ✅ the sentinel is only valid with its native name
function piiTypeRef(type: PiiType, native: string | null): PiiTypeRef {
  if (type === "provider-specific" && native === null) throw new TypeError("provider-specific must name its native type");
  return { type, providerSpecificType: native };
}
```

**Breaks when** the product needs the vendor's distinction (see product veto in [boundaries.md](boundaries.md)). Then the distinction is promoted into the canonical set under a core name; it does not stay native.

## The result type enforces the vocabulary

**Rule.** The contract an adapter must honour is checked by the result type at construction, so no adapter can emit a non-conforming result and no caller has to re-check.

**Test.** Construct a non-conforming result by hand. It should be impossible, or fail at construction.

```ts
// ✅ every canonical category appears exactly once; natives unique
const ClassifyResult = z.object({
  categories: z.array(z.object({ category: Category, native: z.string(), score: z.number() })),
}).refine(r => new Set(r.categories.map(c => c.category)).size === CATEGORIES.length, "every category once")
  .refine(r => new Set(r.categories.map(c => c.native)).size === r.categories.length, "natives unique");
```

**Breaks when** the validator is on the request side only. The request is the caller's promise; the result is the adapter's. Both have contracts, and the adapter's is the one that keeps vendor churn out of the core.

## Twin vocabularies across a process boundary are pinned by a test

**Rule.** When a payload crosses a process boundary and cannot import the host's types (a sandbox, a worker, another service), each side defines its own vocabulary, and a test asserts the two are equal. The equality is pinned, not assumed.

**Test.** For each pair of twin types, name the test that fails when they drift.

```ts
// host/verdict.ts
export const Verdict = ["allow", "block", "modify"] as const;
// sandbox/wire.ts — cannot import host
export type WireVerdict = "allow" | "block" | "modify";

// host/__tests__/wireContract.test.ts
type Equal<A, B> = [A] extends [B] ? ([B] extends [A] ? true : false) : false;
const _pinned: Equal<(typeof Verdict)[number], WireVerdict> = true;
```

**Breaks when** the twin is a copy nobody pinned. Two definitions with no test between them are one definition and one bug.

## Options are derived from the registry

**Rule.** A configuration schema that enumerates implementations (which backend, which model) is derived from the registry of implementations, so the schema cannot offer something the code does not have.

**Test.** Register a new implementation. The schema accepts it without an edit. Remove one. The schema rejects it without an edit.

```ts
// ❌ a list that drifts from the code
const BackendSlug = z.enum(["google-dlp", "aws-macie"]);
```

```ts
// ✅ the registry is the source
const BackendSlug = z.enum(piiBackends.slugs());
```

**Breaks when** the schema must be serialised ahead of time for another system. Then the two cannot share a source, and a test pins them equal instead.

## Absence has a reason

**Rule.** An empty result that means "nothing applied" and an empty result that means "something failed" are different values. The type distinguishes them.

**Test.** Can a caller tell, from the value alone, why there is nothing?

```ts
// ❌ empty by entitlement and empty by fault look the same
async function verdicts(message: Message): Promise<Verdict[]>;
```

```ts
// ✅ the reason is in the type
type EngineOutcome =
  | { status: "disabled" }                   // no hooks entitled for this tenant
  | { status: "ran"; verdicts: Verdict[] }   // possibly empty, and that means clean
  | { status: "failed"; reason: FailReason };
```

**Breaks when** the caller genuinely treats every absence the same way. Then the distinction is cost without a consumer. The test is whether any caller branches on the reason; if none does, the union is premature.

## Reasons are stable codes

**Rule.** The reason attached to an error or a status is a value from a closed set, not free text. Codes key alerts, dashboards, and branches; sentences do not.

**Test.** Search for `reason: "` followed by a sentence. Each is a code that does not exist yet.

```ts
// ❌ free text nobody can branch on or count
throw new CapabilityError("the model was retired by the provider");
```

```ts
// ✅ a code for machines, a message for humans
throw new CapabilityError({ reason: "model_unavailable", message: "model retired by the provider" });
```

**Breaks when** the closed set is extended on every new case until it is a free-text field with extra steps. A reason earns its place by having a consumer that branches on it or counts it.

## Sources

- The carry-versus-branch rule is the generalisation of Parnas's information hiding to values: logic depends only on what the module has promised to keep stable.
- Hyrum's Law: every observable behaviour will be depended on, so the observable vocabulary is kept small on purpose. https://www.hyrumslaw.com/
