---
name: good-code
description: Reference on what good code is, architecturally - how business logic stays separable from the things that carry it, which way dependencies point, where seams go, what crosses them, who owns state, and what enforces each invariant. Use when designing or reviewing a module, deciding where a port or seam belongs, judging whether a diff keeps the core clean, or when another skill needs a definition of good code. Information only - it prescribes no workflow.
---

# Good Code

A reference, not a procedure. It says what good code is and what it is not, so a design, a review, or another skill has something to measure against. It does not say what to do next.

## Thesis

Good code is code whose correctness is established by something cheaper than reading it. The business logic (the **core**) is separable from everything that carries it (frameworks, vendors, runtimes, storage), and every component can be understood from its typed inputs and outputs alone.

Two conditions, and both must hold:

1. The core can be maintained without learning any unstable dependency.
2. Any component can be understood from its typed inputs and outputs alone.

The moment either one forces a reader to open a box, the design has failed. The failure is falsifiable:

- Maintaining the core requires reading a vendor SDK's source or changelog.
- A component's behaviour cannot be predicted from its typed signature.
- Business logic branches on a vendor-specific value that was never promoted into a stable vocabulary.
- Two modules can each plausibly claim the same state or the same write path.
- An invariant is held only by a comment, a habit, or a reviewer's memory.

## Glossary

Use these terms exactly. The first eight are shared with the `codebase-design` vocabulary so the two can be swapped.

- **Module**: anything with an interface and an implementation. Scale-agnostic: a function, a class, a package.
- **Interface**: everything a caller must know to use the module correctly. The type signature, plus invariants, ordering, error modes, required configuration, cost. Not just the `interface` keyword.
- **Implementation**: what is inside the module.
- **Seam**: the place where a module's interface lives; where behaviour can be changed without editing the module. Where to put it is a separate decision from what goes behind it.
- **Adapter**: a concrete thing that satisfies an interface at a seam. Names a role, not a substance.
- **Depth**: behaviour per unit of interface. Deep means a lot behind a little.
- **Leverage**: what callers get from depth. One implementation pays back across every call site and test.
- **Locality**: what maintainers get from depth. Change, bugs, and verification concentrate in one place.
- **Core**: the business logic. The part that must stay maintainable without learning any unstable dependency.
- **Port**: an interface the core owns, written in the core's vocabulary, describing a conversation with something outside the core. Adapters implement ports; the core never implements an adapter's shape.
- **Contract**: what a module guarantees, stated as meaning rather than mechanism. The interface is the contract made concrete.
- **Invariant**: a fact that must hold. Every invariant has exactly one enforcer.
- **Enforcer**: the thing that makes a broken invariant fail. In order of preference: a type, a validator at construction, a lint or import rule, a contract test, a review, a comment.
- **Canonical vocabulary**: the small typed set of values logic may branch on.
- **Cargo**: a value carried through a module opaque, never branched on.
- **Owner**: the one module allowed to write a given state or build a given name.
- **Write path**: a route by which state changes. Each state has one.

## How each chapter is written

Every rule has four parts: the rule, a test that can be applied to a diff, a bad/good pair in TypeScript, and where the rule breaks. The examples are shapes, not a library; the names are illustrative. Each chapter ends with its sources.

## Chapters

| Chapter | Question it answers |
|---|---|
| [dependencies.md](dependencies.md) | Which way may dependencies point? Why one implementation is enough to justify a port. |
| [boundaries.md](boundaries.md) | Where does a seam go? What changes when a provider is added, what vanishes when a module is deleted. |
| [contracts.md](contracts.md) | What must a caller know? The interface as a black box, outcomes as data, illegal states unrepresentable. |
| [vocabulary.md](vocabulary.md) | What survives a crossing? Canonical values, cargo, twin vocabularies pinned across a process boundary. |
| [failure.md](failure.md) | How does each side fail? Errors re-minted at the seam, fail direction, earliest failure, no permissive defaults. |
| [ownership.md](ownership.md) | Who may write? One owner per write path, single door per store, composition root. |
| [enforcement.md](enforcement.md) | What makes it stay true? The enforcer ladder, linted layering, two realizations compared. |
