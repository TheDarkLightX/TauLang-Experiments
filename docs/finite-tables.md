# Finite Tables

Finite tables are the executable entry point for the table research program.

## Standard Claim

A finite table can be treated as a function from a finite key set into a Boolean-algebra carrier:

```text
Table K A := K -> A
```

The core operations are pointwise or key-local:

```text
set(T, k, v)(x) = v       if x = k
set(T, k, v)(x) = T(x)    if x != k

common(T, U)(x) = T(x)    if T(x) = U(x)
common(T, U)(x) = 0       otherwise

select_phi(T)(x) = T(x)   if phi(T(x))
select_phi(T)(x) = 0      otherwise
```

## Boundary

Finite tables are not the same as arbitrary infinite TABA tables. They are the finite executable kernel that should embed into a completed reference semantics.
