# Below is a pragmatic, code-heavy review of Dasy’s current syntax and macro story, concrete ergonomics upgrades, and a drop-in plan for a Scheme-style `define-syntax` (hygienic, `syntax-rules`-first; later extensible to `syntax-case`).

---

# 1) What Dasy syntax looks like today (quick review)

```clojure
;; functions
(defn addNums [:uint256 x y] :uint256 [:external :pure]
  (+ x y))

;; tuples, arrays, types
'(1 2 3)              ; tuple
[1 2 3]               ; array
(array :uint256 10)   ; typed array
(hash-map :address :uint256)
```

* Dasy is “Clojure-inspired Lisp with Python influences” and has a Vyper-aligned type surface; base types are keywords `:uint256`, composites via calls `(string 10)`, `(array :uint256 10)`, `(hash-map :address :uint256)`. &#x20;
* Operators chain n-ary: `(+ 2 3 4 5)`, `(< x y z a)`.&#x20;
* Core forms: `defn`, `defvar`, `definterface`, `defstruct`, `defevent`, `defconst` have documented shapes.     &#x20;
* Method/field sugar exists: `self/x` or `(. self x)`; the parser rewrites `sym/attr` and `sym.attr` to the attribute form.&#x20;
* Keyword arguments are parsed (now used for structs/events, and available in calls).  &#x20;
* Reader tweak: `0x...` literals are handled specially by a custom `DasyReader`.&#x20;

### Macros today

* “Macros are written in Hy (a Pythonic Lisp)” (project docs) and provide sugar like `cond`, `condp`, `doto`, `set-in`, `get-at`, `arrow` (`->`), `arroww` (`->>`).   &#x20;
* The parser currently routes macros through Hy’s expander (`hy.macroexpand`), with a small registry (`MACROS`) and a handler.  &#x20;
* There are “compiler extension macros” like `interface!`/`include!` which previously had path/recursion pitfalls; these are now mitigated via a `ParseContext` and `macro_utils` helpers.   &#x20;

---

# 2) Where the syntax can be more ergonomic / lispy

### A. Normalize attribute/method idioms

Today you can write `self/x`, `self.x`, or `(. self x)` and even the Hy “method reference” idiom `((. None append) obj 1)` is handled in the parser. Prefer two canonical forms and let macros cover the rest:

* Canonical **read**: `(. obj field)` (already there)
* Canonical **call**: `(. obj method arg ...)` (already there; parser normalizes `(. None meth)` calls).&#x20;

Then recommend users do pipelines:

```clojure
(-> self/myMap
    (set-at msg/sender 1)
    (set-at msg/sender 11))
```

Replace Hy `arrow`/`arroww` with Dasy-native macros (below) and consider removing the “`. None`” special case from the core, keeping it strictly a macro surface. (Your review doc points out this is “clever but complex”; `doto`/`->` are cleaner.)&#x20;

### B. First-class binding forms

Add small lispy staples:

```clojure
(let [x 10
      y (+ x 2)]
  (* x y))

(when (> n 0) (set self/count (+ self/count n)))
(unless ok (raise "not ok"))
```

These are pure macro sugar to existing `defvar`/`if`/`do`.

### C. Uniform keyword arguments at call sites

Your parser already recognizes `:kw val` pairs in calls. Lean into this by documenting and testing them broadly:

```clojure
(log (Transfer :sender from :receiver to :amount amt)) ; already promoted for events
```

(You’ve used keyword-only structs/events and added aliases; just extend the examples/tests to show call-site kwargs too.)  &#x20;

### D. Tighten the core surface

Move “sugar” out of the parser into macros where possible:

* The `ALIASES` table is great, but consider trimming anything that is better expressed as macros (`->`, `->>`, some attribute sugar), keeping `ALIASES` for stable, spec-level aliases only.&#x20;
* Keep the dispatch table simplification noted in your review as a cleanup task.&#x20;

---

# 3) Replacing Hy with a Scheme-style macro system

## Goals

* **Hygienic** (no accidental capture), **compile-time**, **Dasy-native**.
* Start with **`define-syntax` + `syntax-rules`** (pattern macros, literals, `...`).
* Later add **`syntax-case`** (procedural transformers, `with-syntax`, `datum->syntax`).

## Where it fits in the pipeline

Add a macro-expansion pass **before** AST lowering:

```
source --(DasyReader)--> Hy models
    --(expand module with env)--> Hy models (expanded)
    --(parse_node / parse_expr)--> Vyper AST
    --(CompilerData / Vyper)--> bytecode/interface/abi
```

Hook point: `parse_src` already reads forms with `dasy_read_many`. Expand the sequence there, then feed each expanded form to `parse_node`.&#x20;

## Minimal data model (Python)

```python
# dasy/macro/syntax.py
from dataclasses import dataclass, field
from itertools import count
from hy import models

_gens = count(1)

@dataclass(frozen=True)
class Syntax:
    datum: object                  # a Hy model node (Symbol, Expression, etc.)
    scopes: tuple[int, ...] = ()   # hygiene marks (scope stack)

def is_sym(sx, name=None):
    return isinstance(sx.datum, models.Symbol) and (name is None or str(sx.datum)==name)

def add_mark(sx, mark):
    return Syntax(sx.datum, (*sx.scopes, mark))

def same_id(a, b):
    return isinstance(a.datum, models.Symbol) and isinstance(b.datum, models.Symbol) \
           and (a.datum == b.datum) and (a.scopes == b.scopes)

def datum(sx): return sx.datum

def gensym(prefix="g__"):
    return models.Symbol(f"{prefix}{next(_gens)}")

class MacroEnv:
    def __init__(self):
        self.frames = [{}]         # stack of {str(name) -> transformer}

    def define(self, name: str, transformer):
        self.frames[-1][name] = transformer

    def lookup(self, name: str):
        for fr in reversed(self.frames):
            if name in fr: return fr[name]
        return None

    def push(self): self.frames.append({})
    def pop(self): self.frames.pop()
```

## Pattern engine for `syntax-rules` (ellipses, literals)

A compact implementation that covers the common cases (identifier literals, sequence repetition):

```python
# dasy/macro/syntax_rules.py
from hy import models
from .syntax import Syntax, datum, is_sym, gensym, add_mark

ELLIPSIS = models.Symbol("...")

def _is_expr(x): return isinstance(x, models.Expression)
def _to_syntax(x, scopes): return Syntax(x, scopes)

def match(pattern, stx, literals, scopes, binds=None):
    """Return env dict or None."""
    if binds is None: binds = {}
    p = pattern; d = datum(stx)

    # identifier literal
    if isinstance(p, models.Symbol):
        ps = str(p)
        if ps in literals:
            return binds if (isinstance(d, models.Symbol) and str(d)==ps) else None
        # variable
        binds.setdefault(ps, []).append(_to_syntax(d, stx.scopes))
        return binds

    # sequence patterns (support ... repetition)
    if _is_expr(p) and _is_expr(d):
        i = 0; j = 0
        while i < len(p):
            if i+1 < len(p) and p[i+1] == ELLIPSIS:
                # greedy repetition: bind as many elems as possible
                subpat = p[i]
                # try all splits
                for k in range(j, len(d)+1):
                    trial = dict((k,v.copy()) for k,v in binds.items())
                    ok = True
                    jj = j
                    group = []
                    while jj < k:
                        r = match(subpat, Syntax(d[jj], stx.scopes), literals, scopes, trial)
                        if r is None: ok=False; break
                        jj += 1
                    if ok:
                        binds = trial; j = k; break
                i += 2
            else:
                if j >= len(d): return None
                binds = match(p[i], Syntax(d[j], stx.scopes), literals, scopes, binds)
                if binds is None: return None
                i += 1; j += 1
        return binds if j == len(d) else None

    # atoms must be equal
    return binds if p == d else None

def substitute(template, binds, scopes):
    if isinstance(template, models.Symbol):
        name = str(template)
        if name in binds:
            # last occurrence wins for 1:1, or splice for many
            vals = binds[name]
            return vals[-1].datum if len(vals)==1 else models.Expression([v.datum for v in vals])
        return template
    if isinstance(template, models.Expression):
        out = []
        i = 0
        while i < len(template):
            if i+1 < len(template) and template[i+1] == ELLIPSIS:
                # splice a sequence for the preceding element
                key = template[i]
                assert isinstance(key, models.Symbol), "ellipsis must follow a variable"
                seq = [v.datum for v in binds.get(str(key), [])]
                out.extend(seq)
                i += 2
            else:
                out.append(substitute(template[i], binds, scopes))
                i += 1
        return models.Expression(out)
    return template

class SyntaxRulesMacro:
    def __init__(self, literals, rules):
        self.literals = set(str(x) for x in literals)
        self.rules = rules  # list of (pattern_expr, template_expr)

    def __call__(self, call_stx, env):
        """call_stx.datum = (name arg1 arg2 ...)"""
        form = call_stx.datum
        scopes = call_stx.scopes
        for (pat, tmpl) in self.rules:
            binds = match(pat, Syntax(form, scopes), self.literals, scopes)
            if binds is not None:
                return substitute(tmpl, binds, scopes)
        raise Exception("no syntax-rules pattern matched")
```

## `define-syntax` parser handler

Add a **new core form** in your parser module (no Hy):

```python
# dasy/parser/macros2.py
from hy import models
from .context import ParseContext
from ..macro.syntax_rules import SyntaxRulesMacro
from ..macro.syntax import Syntax
from .utils import add_src_map

def parse_define_syntax(expr, context: ParseContext, env):
    # (define-syntax NAME (syntax-rules (lit ...) ( (pat) tmpl ) ...))
    _, name, spec = expr
    if not (isinstance(spec, models.Expression) and str(spec[0])=="syntax-rules"):
        raise Exception("Only syntax-rules is supported here")

    literals = spec[1] if len(spec) > 1 and isinstance(spec[1], models.Expression) else models.Expression([])
    start = 2 if len(spec) > 1 else 1
    rules = []
    for clause in spec[start:]:
        # each clause is: ((NAME ...) template)
        pat, tmpl = clause
        rules.append((pat, tmpl))

    macro = SyntaxRulesMacro(literals, rules)
    env.define(str(name), macro)
    return None  # not an AST node
```

Integrate an **expansion pass**:

```python
# dasy/parser/expander.py
from hy import models
from ..macro.syntax import Syntax

def expand(form, env):
    if isinstance(form, models.Expression) and len(form) > 0:
        head = form[0]
        if isinstance(head, models.Symbol):
            m = env.lookup(str(head))
            if m:
                # call transformer with full call syntax object
                expanded = m(Syntax(form, ()), env)
                return expand(expanded, env)
        # otherwise recursively expand subforms
        return models.Expression([expand(x, env) for x in form])
    return form

def expand_module(forms, env, parse_define_syntax_fn, context):
    out = []
    for f in forms:
        if (isinstance(f, models.Expression) and len(f)>0 and
            isinstance(f[0], models.Symbol) and str(f[0])=="define-syntax"):
            parse_define_syntax_fn(f, context, env)  # side-effect
            continue
        out.append(expand(f, env))
    return out
```

Wire it in `parse_src`:

```python
# dasy/parser/parse.py (inside parse_src)
from .expander import expand_module
from ..macro.syntax import MacroEnv

env = MacroEnv()
forms = list(dasy_read_many(src))
forms = expand_module(forms, env, macros2.parse_define_syntax, context)
for element in forms:
    ast = parse_node(element, context)
    ...
```

(You can keep Hy macros working in parallel during a transition by trying “Dasy-macros first, Hy fallback”.)

## Port a few built-in macros to `define-syntax`

**`cond`** (with an `:else` literal):

```clojure
(define-syntax cond
  (syntax-rules (:else)
    ((cond :else e)                     e)
    ((cond test expr)                   (if test expr))
    ((cond test expr :else e)           (if test expr e))
    ((cond test expr rest ...)          (if test expr (cond rest ...)))))
```

**`doto`**:

```clojure
(define-syntax doto
  (syntax-rules ()
    ((doto obj) obj)
    ((doto obj (f a ...) rest ...)
     (do (f obj a ...) (doto obj rest ...)))))
```

**`->` / `->>`** (thread first / last):

```clojure
(define-syntax ->
  (syntax-rules ()
    ((-> x) x)
    ((-> x (f a ...)) (f x a ...))
    ((-> x f) (f x))
    ((-> x s1 s2 ...) (-> (-> x s1) s2 ...))))

(define-syntax ->>
  (syntax-rules ()
    ((->> x) x)
    ((->> x (f a ...)) (f a ... x))
    ((->> x f) (f x))
    ((->> x s1 s2 ...) (->> (->> x s1) s2 ...))))
```

**`set-in` / `get-at`** (showing one):

```clojure
(define-syntax set-in
  (syntax-rules ()
    ((set-in obj field new) (set (. obj field) new))))
```

You already ship these as Hy macros; moving them to Dasy macros removes the Hy dependency and simplifies the parser.&#x20;

## Hygiene (no accidental capture)

The `Syntax` wrapper+`scopes` array gives you a simple **mark-based hygiene**:

* When a transformer **introduces** new identifiers, add a fresh mark so they can’t capture/bes captured by user code.
* Pattern variables retain the caller’s scopes so inserted occurrences refer to caller bindings.

If/when you add `syntax-case`, include `datum->syntax`:

```python
def datum_to_syntax(ctx_like, raw):
    # inherit scopes from a syntax object "ctx_like"
    return Syntax(raw, ctx_like.scopes)
```

---

# 4) Parser/core cleanups that help macros

* **Dispatch table** instead of multi-namespace probing: keeps the core predictable and shorter.&#x20;
* Keep attribute/method desugaring minimal; prefer `->`, `doto` in the macro layer (per your own review note).&#x20;
* You already removed global state with a `ParseContext`, which unblocks a real expander. ✔️ &#x20;

---

# 5) Migration plan (concrete)

1. **Introduce the expander** (as above) and keep Hy fallback:

```python
# in parse_expr
if is_macro(cmd_str):          # current Hy path
    return handle_macro(expr, context)
# Dasy-macros happen before we get here during parse_src
```

2. **Land `define-syntax` + `syntax-rules`** with tests:

* Port `cond`, `doto`, `->`, `->>` first.
* Keep golden examples (your `dasybyexample.md`, ERC20) compiling. &#x20;

3. **Flip the order**: try Dasy macros first; deprecate Hy macros in docs.
4. **(Optional) Add `syntax-case`** for power users (pattern + guards + procedural templates).
5. **Retire the Hy macro path** once feature parity is reached.

---

# 6) Extra ergonomic macros you can ship on day 1

```clojure
;; when / unless
(define-syntax when
  (syntax-rules () ((when test body ...) (if test (do body ...)))))

(define-syntax unless
  (syntax-rules () ((unless test body ...) (if test (do body ...)))))

;; let / let* (let* can expand to nested let's)
(define-syntax let
  (syntax-rules ()
    ((let [] body ...)            (do body ...))
    ((let [x v rest ...] body ...) (let [] (defvar x v) (let [rest ...] body ...)))))
```

These compile straight to your existing `defvar`/`if`/`do` machinery.

---

## TL;DR

* Dasy’s surface is already compact and lispy; the biggest win is **moving sugar out of the parser** and into a **Dasy-native, hygienic macro system**.
* The provided `define-syntax` + `syntax-rules` implementation slots cleanly into `parse_src` as a pre-pass, keeps compatibility, and lets you port existing Hy macros one by one.
* Simplify attribute/method treatment and promote pipelines (`->`, `doto`) as the canonical style; keep the parser lean.


