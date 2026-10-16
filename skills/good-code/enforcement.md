# Enforcement

What makes it stay true. An invariant that is only remembered is not an invariant; it is a hope. Every invariant in the other chapters has an enforcer, and the enforcer sits as high on the ladder as the codebase allows.

## The enforcer ladder

**Rule.** Enforcers, from strongest to weakest: a type, a validator at construction, a lint or import rule, a contract test, a review, a comment. An invariant is held by the highest rung that can express it. Each rung down is cheaper to write and more expensive to keep true.

**Test.** For every invariant named in a design, name its enforcer. "The team knows" is not an enforcer. "There is a comment" is the bottom rung and is written down as such.

| Invariant | Enforcer |
|---|---|
| A memo is never both archived and pinned | type: a union with no such variant |
| A backend declares its input limit | validator: `defineBackend` throws without it |
| The core imports nothing outside the core | lint: an import rule scoped to `core/**` |
| The fake repository behaves like the real one | contract test: one suite run against both |
| The migration set matches the schema file | contract test: both applied, introspected, compared |
| Why the retry waits 500 ms | comment: the measurement that chose it |

**Breaks when** the strongest rung is reached for by a culture that cannot sustain it (a type-level proof nobody on the team can read). The highest rung the codebase can maintain is the right one; the rule is about not settling lower than that.

## Layering is linted, not remembered

**Rule.** The dependency direction in [dependencies.md](dependencies.md) is a lint rule, not a document. There are three holes through which a dependency sneaks in, and each is closed by its own rule: a path (`../adapter/x`), a package (`react`, `@supabase/supabase-js`), and a global (`crypto`, `fetch`).

**Test.** Write `import React from "react"` in a core file. The lint command fails, not the review.

```js
// eslint.config.js — the core is sealed three ways
{
  files: ["src/core/**/*.ts"],
  rules: {
    "import/no-restricted-paths": ["error", { zones: [{ target: "./src/core", from: "./src/adapter" }, { target: "./src/core", from: "./src/infra" }] }],
    "no-restricted-imports": ["error", { patterns: [{ group: ["react", "react-*", "llama.rn", "@supabase/*"] }, { regex: "^(node:.+|fs|crypto|path)$" }] }],
    "no-restricted-globals": ["error", "crypto", "fetch"],
  },
}
```

**Breaks when** the rule is written and then disabled file by file with inline comments. Each disable is a labelled leak; a dozen of them is a rule that does not exist.

## Two independent realizations are compared by a test

**Rule.** When two artifacts must agree (migrations and a schema file, a fake and a real adapter, a client's encryption and the spec it claims to follow, a content-security policy and the environment it allows), a test derives both and compares them. Agreement is pinned, not assumed.

**Test.** For each pair that must agree, name the test that fails when they drift.

```ts
// schema.test.ts — migrations applied to one database, schema.sql to another, introspection compared
test("schema.sql matches the migration set", async () => {
  const fromMigrations = await introspect(await applyMigrations(openMemory()));
  const fromSchemaFile = await introspect(await applySql(openMemory(), read("schema.sql")));
  expect(fromSchemaFile).toEqual(fromMigrations);
});
```

**Breaks when** one side is derived from the other (the schema file generated from the migrations). Then there is one realization, and the test compares a thing to itself. The rule needs two independent sources.

## Fakes are working implementations with a shared store

**Rule.** A fake used by core tests is a real implementation of the port over an in-memory store, not a set of per-method stubs. Two fakes that model the same storage share one store, so an effect through one is visible through the other.

**Test.** Does the fake pass the same contract suite as the real adapter? Does a core test use any per-method stub?

```ts
// ❌ a stub returns what the test wants; nothing checks the behaviour is possible
const repo = { getById: jest.fn().mockResolvedValue(memo), upsert: jest.fn() };
```

```ts
// ✅ a working fake over one store, so a purge in one surfaces as a tombstone in the other
const store = new FakeLocalStore();
const memos = fakeMemoRepository(store);
const sync = fakeSyncRepository(store);

// memoRepository.contract.test.ts — one suite, both implementations
describe.each([["fake", () => fakeMemoRepository(new FakeLocalStore())], ["sqlite", () => new SqliteMemoRepository(openMemory())]])
  ("MemoRepository (%s)", (_, make) => { /* the same assertions */ });
```

**Breaks when** the fake has to model so much that it becomes a second implementation with its own bugs. That is the signal that the port is too wide; narrow the port rather than grow the fake.

## Mapping adapters are tested against the real thing

**Rule.** An adapter whose job is to map the core's vocabulary onto a vendor's is tested against the vendor (a local stack, a recorded wire shape), not against a mock of the vendor. A test that mocks the vendor and checks the mapping checks the author's belief about the vendor, which is the thing that needed testing.

**Test.** For each adapter, name the test that exercises the real vendor shape. An adapter with only mocked tests is marked untested on purpose, in the adapter, so nobody mistakes the mocks for coverage.

```ts
// adapter/supabase/memoRemote.ts
// Untested under the unit runner on purpose: this file only maps rows.
// Covered by supabase/tests/wire.test.ts against the local stack.
```

**Breaks when** the real thing cannot be run locally at all. Then the next best enforcer is a recorded fixture of the real wire shape, pinned with the date it was captured, and the gap is written down.

## Configuration is code

**Rule.** Pins, environment files, policies, and schemas have tests, because they hold invariants the code relies on. A base image is pinned by digest. A dependency is pinned exactly. A policy is derived from the same source as the environment it must permit.

**Test.** Can an edit to a configuration file break the test run?

```ts
// deployConfig.test.ts — the policy and the environment cannot drift
test("CSP allows exactly the configured origins", () => {
  const csp = parseCsp(read("public/_headers"));
  const env = parseEnv(read(".env.production"));
  expect(csp["connect-src"]).toContain(new URL(env.SUPABASE_URL).origin);
});
```

**Breaks when** every configuration value gets a test asserting it equals itself. The test compares two sources that must agree; a test that reads a value and asserts the value is a tautology.

## A known gap is written next to the design it compromises

**Rule.** Every design has places where it knowingly falls short of these rules. They are listed in the design document, next to the rule they break, with the reason. A reader who finds the gap finds the reason in the same place.

**Test.** Does the architecture document end with the list of what is knowingly wrong? Does a leaked vendor import carry a comment naming it as a leak?

```md
## Current gaps
- `core/usecase/chat.ts` holds model-specific prompt templates. The core test bends here on purpose:
  the templates are the product (see boundaries: product veto). Revisit when a second model ships.
- Fake and real repositories are mirrored by hand. No contract suite pins them yet.
```

**Breaks when** the gaps list is where rules go to die: every violation is "known" and none is scheduled. A gap entry names the condition under which it closes, or it is not a gap but a decision, and goes in the decisions list instead.

## Sources

- Feathers, *Working Effectively with Legacy Code*: legacy code is code without tests; characterization tests pin what the code does before it is changed. https://understandlegacycode.com/blog/key-points-of-working-effectively-with-legacy-code/
- Böckeler, *Harness engineering*: computational sensors (tests, linters, type checkers, architecture rules) are cheap enough to run on every change. https://martinfowler.com/articles/harness-engineering.html
- Google, *Software Engineering at Google*, ch. 9: consistency is enforced so code can be maintained and refactored with tools. https://abseil.io/resources/swe-book/html/ch09.html
