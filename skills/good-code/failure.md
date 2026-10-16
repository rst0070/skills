# Failure

How each side fails, and in which direction. A seam is defined as much by what happens when the far side misbehaves as by what happens when it works.

## Errors are re-minted at the seam

**Rule.** A vendor error never crosses into the core. The adapter maps it, at the seam, to one core error type with a closed code and the original attached as the cause.

**Test.** Search the core for vendor error types or vendor error messages. None.

```ts
// ❌ the vendor's error vocabulary is now the core's
try { await supabase.auth.signInWithPassword(c); }
catch (e) { if (e.message.includes("Invalid login")) { /* ... */ } }
```

```ts
// ✅ a table at the seam; one core type; cause attached
type AccountErrorCode = "invalid-credentials" | "email-unconfirmed" | "rate-limited" | "unavailable";
class AccountError extends Error {
  constructor(readonly code: AccountErrorCode, message: string, opts: { cause: unknown }) { super(message, opts); }
}
const AUTH_CODES: Record<string, AccountErrorCode> = { invalid_credentials: "invalid-credentials", email_not_confirmed: "email-unconfirmed", over_request_rate_limit: "rate-limited" };
function toAccountError(e: AuthError): AccountError {
  return new AccountError(AUTH_CODES[e.code] ?? "unavailable", e.message, { cause: e });
}
```

**Breaks when** the mapping table ends in a catch-all code that folds distinct causes together (`"unknown"` covering an undecryptable row, an unsupported version, and a revoked session). The catch-all is a named debt: the three causes have three consequences and will need three codes.

## Failure classes have distinct consequences, and the type names the class

**Rule.** There are usually three kinds of failure, and each has a different consequence: recoverable (the caller sees a failed result and continues), fail-closed (the operation dies and the input is withheld), and infrastructure (the host itself is broken). The type says which kind it is, so the consequence is decided at the declaration.

**Test.** When a new error is introduced, can you say which of the three it is? If not, its consequence is undecided, and some handler will decide it by accident.

```ts
class CapabilityError extends Error { readonly kind = "recoverable"; constructor(readonly reason: ReasonCode, message: string) { super(message); } }
class CapabilityFailedClosed extends Error { readonly kind = "fail-closed"; /* the session ends, the input is withheld */ }
class SessionError extends Error { readonly kind = "infrastructure"; /* nothing that fails while building a session leaves as anything else */ }
```

**Breaks when** the classes multiply until each error is its own class and the consequence is again decided per handler. Three classes with three consequences; a new class needs a new consequence.

## Each control declares its fail direction

**Rule.** A control that protects something (masking, blocking, authorisation) fails closed: when its infrastructure is down, the protected thing is withheld. A control that merely helps fails open. The direction is declared where the control is defined, not chosen in the handler that catches the error.

**Test.** For each control, what happens when its backend is unreachable? The answer is in the code at the declaration, not in someone's head.

```ts
// ✅ no permissive default; a blocking control cannot be silently allowed through
interface Capability {
  readonly name: string;
  /** When true, any failure withholds the input. No default: the author must choose. */
  readonly failsClosed: boolean;
}
```

```ts
// ✅ a partial finding list would under-report, so the masking control is sequential and fail-fast
for (const window of windows) findings.push(...await backend.detect(window));   // not Promise.allSettled
```

**Breaks when** everything fails closed and the product becomes unavailable whenever anything is. The direction is a decision per control, and "open" is a legitimate answer for a control that only helps.

## Fail at the earliest moment of full information

**Rule.** Every check happens at the earliest point where the information to perform it exists. Configuration time over runtime. Module load over first request. Save over execute.

**Test.** For each invariant, could it be checked earlier with the same information? If yes, it is checked too late.

```ts
// ❌ discovered on the first request that happens to hit it
async function detect(text: string) { if (!process.env.DLP_PROJECT) throw new Error("DLP_PROJECT unset"); }
```

```ts
// ✅ discovered when the module loads, before any request exists
const DLP_PROJECT = process.env.DLP_PROJECT ?? (() => { throw new StartupError("DLP_PROJECT must be set, see .env.example"); })();
```

```ts
// ❌ a missing limit is found by a long input in production
abstract class PiiBackend { maxInputChars?: number }
```

```ts
// ✅ a backend without a limit cannot be registered
function defineBackend(spec: { slug: string; maxInputChars: number; detect: Detect }): PiiBackend {
  if (!(spec.maxInputChars > 0)) throw new TypeError(`${spec.slug} must declare a positive maxInputChars`);
  return Object.freeze(spec);
}
```

**Breaks when** the early check needs information that only exists later (the tenant, the request). Then the earliest moment is later, and that is fine. The rule is earliest with full information, not earliest at any cost.

## No permissive defaults for values that matter

**Rule.** A value that affects security, money, or data retention has no in-code fallback. If it is not configured, the operation that needs it fails, naming the missing value.

**Test.** Search for `?? ` and default parameters on anything security-, money-, or retention-relevant. Each is a lifetime, a limit, or a permission that nobody chose.

```ts
// ❌ a TTL nobody configured picks a lifetime
const ttl = config?.aliasTtlSeconds ?? 86_400;
```

```ts
// ✅ a missing TTL fails the mint
if (config.aliasTtlSeconds === undefined) throw new ConfigMissing("aliasTtlSeconds");
```

**Breaks when** the value is cosmetic (a page size, a colour). Defaults are for things where any value is acceptable.

## Configuration-time validation is UX; execution re-validates

**Rule.** Validating a handler's configuration when it is saved is a courtesy to the author. The handler is untrusted at execution, so the same check runs again when the input arrives.

**Test.** Edit the stored configuration by hand to something invalid. Does execution still refuse it?

**Breaks when** the two checks drift apart. They are one function called from two places, not two functions.

## Cleanup paths neither throw nor swallow

**Rule.** Teardown retries once, then logs and reports, and names in a comment who reconciles the leaked resource. It never raises over the original error, and it never passes silently.

**Test.** Every `catch` inside cleanup has a report and a named reconciler.

```ts
// ❌ silent: the leak is invisible until the pool is exhausted
finally { try { await pool.release(slot); } catch {} }
```

```ts
// ✅ retry, report, name the reconciler
finally {
  await releaseWithRetry(pool, slot).catch(e => {
    log.error("pool slot leaked", { slot, cause: e }); report(e);
    // reconciled by the hourly reapOrphanedSlots job
  });
}
```

**Breaks when** the retry itself is dangerous (a non-idempotent release). Then the retry is dropped, but the report and the named reconciler stay.

## Adapters refuse; the core decides

**Rule.** An adapter that cannot honour the request says so with an error. It does not quietly do something smaller (truncate, sample, skip). What to do about the refusal is a core decision.

**Test.** Does any adapter change the meaning of its result to stay within a limit? That is a silent decision the core cannot see.

```ts
// ❌ "no findings" now sometimes means "we looked at half"
async detect(text: string) { return this.client.inspect(text.slice(0, this.maxInputChars)); }
```

```ts
// ✅ refuse; the capability windows the input and merges the results
async detect(text: string) { if (text.length > this.maxInputChars) throw new InputTooLarge(this.maxInputChars); /* ... */ }
```

**Breaks when** the refusal is the common case and every caller ends up windowing. Then windowing is part of the contract, and the core provides it once, behind the capability, where every caller gets it.

## Sources

- Ousterhout, *A Philosophy of Software Design*: define errors out of existence where semantics allow; otherwise aggregate and handle once. https://danlebrero.com/2021/02/24/philosophy-of-software-design-summary/
- Minsky, *Effective ML*: make common errors obvious. https://blog.janestreet.com/effective-ml-revisited/
