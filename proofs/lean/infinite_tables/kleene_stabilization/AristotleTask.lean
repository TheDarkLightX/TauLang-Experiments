/-!
# Aristotle packet F/H: Kleene least fixed point and finite stabilization

This is a self-contained proof packet for the infinite TABA table semantics
stack.

The semantic idea:

* `kleeneMu oc F` is the countable supremum of finite iterations from bottom.
* If `F` is monotone and omega-continuous, that supremum is a fixed point.
* If `Y` is any fixed point of `F`, then `kleeneMu oc F` is below `Y`.
* If the finite iteration sequence stabilizes at a finite step `N`, then the
  completed omega-supremum agrees exactly with that finite iterate.

Fill the sorries without weakening statements. Do not add axioms, unsafe
definitions, new assumptions, or classical quotient shortcuts.
-/

set_option autoImplicit false

namespace AristotleKleeneStabilization

structure OmegaComplete (A : Type) where
  le : A -> A -> Prop
  bot : A
  omegaSup : (Nat -> A) -> A
  le_refl : forall x, le x x
  le_trans : forall {x y z}, le x y -> le y z -> le x z
  le_antisymm : forall {x y}, le x y -> le y x -> x = y
  bot_le : forall x, le bot x
  omegaSup_upper : forall xs n, le (xs n) (omegaSup xs)
  omegaSup_least : forall xs y, (forall n, le (xs n) y) -> le (omegaSup xs) y

def Monotone {A : Type} (oc : OmegaComplete A) (F : A -> A) : Prop :=
  forall {x y}, oc.le x y -> oc.le (F x) (F y)

def Chain {A : Type} (oc : OmegaComplete A) (xs : Nat -> A) : Prop :=
  forall n, oc.le (xs n) (xs (n + 1))

def OmegaContinuous {A : Type} (oc : OmegaComplete A) (F : A -> A) : Prop :=
  forall xs, Chain oc xs -> F (oc.omegaSup xs) =
    oc.omegaSup (fun n => F (xs n))

def iter {A : Type} (oc : OmegaComplete A) (F : A -> A) : Nat -> A
  | 0 => oc.bot
  | n + 1 => F (iter oc F n)

def kleeneMu {A : Type} (oc : OmegaComplete A) (F : A -> A) : A :=
  oc.omegaSup (iter oc F)

theorem iter_chain {A : Type} (oc : OmegaComplete A) (F : A -> A)
    (hMono : Monotone oc F) :
    Chain oc (iter oc F) := by
  intro n
  induction n with
  | zero =>
      exact oc.bot_le (F oc.bot)
  | succ n ih =>
      exact hMono ih

theorem omegaSup_iter_tail_eq {A : Type}
    (oc : OmegaComplete A) (F : A -> A) :
    oc.omegaSup (fun n => iter oc F (n + 1)) =
      oc.omegaSup (iter oc F) := by
  apply oc.le_antisymm
  · apply oc.omegaSup_least
    intro n
    exact oc.omegaSup_upper (iter oc F) (n + 1)
  · apply oc.omegaSup_least
    intro n
    cases n with
    | zero =>
        exact oc.bot_le (oc.omegaSup (fun m => iter oc F (m + 1)))
    | succ n =>
        exact oc.omegaSup_upper (fun m => iter oc F (m + 1)) n

theorem kleeneMu_fixed {A : Type}
    (oc : OmegaComplete A) (F : A -> A)
    (hMono : Monotone oc F)
    (hCont : OmegaContinuous oc F) :
    F (kleeneMu oc F) = kleeneMu oc F := by
  unfold kleeneMu
  rw [hCont (iter oc F) (iter_chain oc F hMono)]
  exact omegaSup_iter_tail_eq oc F

/-!
Target 1:
Any fixed point of a monotone function lies above the Kleene construction.
This supplies the "least" half of least fixed point semantics.
-/
theorem kleeneMu_least_fixed {A : Type}
    (oc : OmegaComplete A) (F : A -> A)
    (hMono : Monotone oc F)
    (Y : A) (hFixed : F Y = Y) :
    oc.le (kleeneMu oc F) Y := by
  unfold kleeneMu
  apply oc.omegaSup_least
  intro n
  induction n with
  | zero =>
      exact oc.bot_le Y
  | succ n ih =>
      have h := hMono ih
      rw [hFixed] at h
      exact h

/-!
Target 2:
A chain is monotone across arbitrary finite index gaps.
This is the induction lemma needed by the stabilization theorem.
-/
theorem chain_le_of_le {A : Type}
    (oc : OmegaComplete A) (xs : Nat -> A)
    (hChain : Chain oc xs)
    {m n : Nat} (h : m <= n) :
    oc.le (xs m) (xs n) := by
  obtain ⟨k, hk⟩ := Nat.le.dest h
  rw [← hk]
  clear h hk n
  induction k with
  | zero =>
      simpa using oc.le_refl (xs m)
  | succ k ih =>
      have hstep : oc.le (xs (m + k)) (xs (m + k + 1)) := hChain (m + k)
      have hnext : oc.le (xs m) (xs (m + k + 1)) :=
        oc.le_trans ih hstep
      simpa [Nat.add_assoc] using hnext

/-!
Target 3:
If the finite iteration sequence stabilizes at `N`, then the completed
omega-supremum is exactly the finite iterate at `N`.
-/
theorem kleeneMu_eq_stable_iter {A : Type}
    (oc : OmegaComplete A) (F : A -> A)
    (hMono : Monotone oc F)
    (N : Nat)
    (hStable : forall n, N <= n -> iter oc F n = iter oc F N) :
    kleeneMu oc F = iter oc F N := by
  unfold kleeneMu
  apply oc.le_antisymm
  · apply oc.omegaSup_least
    intro n
    by_cases hN : N <= n
    · rw [hStable n hN]
      exact oc.le_refl (iter oc F N)
    · have hnN : n <= N := Nat.le_of_lt (Nat.lt_of_not_ge hN)
      exact chain_le_of_le oc (iter oc F) (iter_chain oc F hMono) hnN
  · exact oc.omegaSup_upper (iter oc F) N

theorem packet_fh_receipt {A : Type}
    (oc : OmegaComplete A) (F : A -> A)
    (hMono : Monotone oc F)
    (hCont : OmegaContinuous oc F)
    (Y : A) (hFixed : F Y = Y)
    (N : Nat)
    (hStable : forall n, N <= n -> iter oc F n = iter oc F N) :
    F (kleeneMu oc F) = kleeneMu oc F
      /\ oc.le (kleeneMu oc F) Y
      /\ kleeneMu oc F = iter oc F N := by
  constructor
  · exact kleeneMu_fixed oc F hMono hCont
  constructor
  · exact kleeneMu_least_fixed oc F hMono Y hFixed
  · exact kleeneMu_eq_stable_iter oc F hMono N hStable

end AristotleKleeneStabilization
