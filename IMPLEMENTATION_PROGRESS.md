# Dasy Suggestions Implementation Progress

This file tracks the implementation of items from `main/suggestions.md`.

Status legend: [x] done, [~] in progress, [ ] pending

## Macro System (define-syntax / syntax-rules)

- [x] Add macro core (Syntax, MacroEnv)
- [x] Implement `syntax-rules` matcher (expressions + lists, ellipses)
- [x] Add expander and `define-syntax` handler
- [x] Wire expander into `parse_src`
- [x] Register builtin Dasy macros (cond, doto, when, unless, let)
 - [x] Port thread macros (->, ->>) to Dasy macros (procedural)
 - [x] Port `doto` to Dasy (procedural; returns `(do ...)`)
 - [x] Port field/data access macros: `set-in`, `get-at`
 - [x] Add list + variadic variants: `get-at!`, `set-at`, `set-at!`
 - [x] Port `set-self` to Dasy (procedural; emits `(do ...)` of sets)
- [ ] Flip order and deprecate Hy macros in docs
- [ ] Optional: add `syntax-case`

## Syntax Ergonomics

- [x] Keep canonical attribute/method forms: `(. obj field)` and `(. obj method args ...)`
- [ ] Consider removing `(. None method)` special-case from core (kept for now for compatibility)
- [ ] Document pipelines (`->`, `->>`) and `doto` as preferred idioms

## Keyword Arguments

- [x] Parser already supports `:kw val` at call sites; examples/tests continue to pass
- [ ] Expand docs and tests to showcase call-site kwargs broadly

## Core Surface Tightening

- [~] Retain existing `ALIASES`; plan to trim once macro parity is complete (esp. `->`, `->>`)
- [ ] Dispatch table simplification (follow-up cleanup)

## Notes / Next Steps

- Keep Hy macros working alongside the new expander until feature parity is reached.
- Next focus: trim `ALIASES` and consider removing the `(. None ...)` special-case after users migrate to Dasy-native `doto`/threads. Optional: simplify dispatch table.
- After parity, update docs and examples to prefer Dasy-native macros, then retire Hy macros.

## Compiler Extension Macros

- [x] Port `include!` to Dasy (recursion guard; base-dir aware path resolution)
- [x] Port `interface!` to Dasy (compiles target and injects `(definterface ...)`)
