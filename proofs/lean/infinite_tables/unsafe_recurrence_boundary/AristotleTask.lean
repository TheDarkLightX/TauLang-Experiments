/-!
# Aristotle packet J: unsafe recurrence boundary

This is a self-contained negative proof packet for the infinite TABA table
semantics stack.

The positive recurrence theorem must exclude same-stratum complement unless a
separate safety condition is proved. This packet proves the boundary in the
completed reference carrier.

Fill the sorries without weakening statements. Do not add axioms, unsafe
definitions, new assumptions, or theorem-statement changes.
-/

set_option autoImplicit false

namespace AristotleUnsafeRecurrenceBoundary

def Stream := Nat -> Bool
def BoolRef := Stream -> Prop

def RefEq (X Y : BoolRef) : Prop :=
  forall s : Stream, X s <-> Y s

def refLe (X Y : BoolRef) : Prop :=
  forall s : Stream, X s -> Y s

def emptyRef : BoolRef := fun _ => False
def fullRef : BoolRef := fun _ => True
def complRef (X : BoolRef) : BoolRef := fun s => Not (X s)
def iUnionRef (X : Nat -> BoolRef) : BoolRef := fun s => exists n, X n s

def MonotoneRef (F : BoolRef -> BoolRef) : Prop :=
  forall {X Y : BoolRef}, refLe X Y -> refLe (F X) (F Y)

def ChainRef (X : Nat -> BoolRef) : Prop :=
  forall n, refLe (X n) (X (n + 1))

def OmegaContinuousRef (F : BoolRef -> BoolRef) : Prop :=
  forall X : Nat -> BoolRef,
    ChainRef X ->
    RefEq (F (iUnionRef X)) (iUnionRef (fun n => F (X n)))

theorem empty_le_full :
    refLe emptyRef fullRef := by
  intro s h
  trivial

theorem full_not_le_empty :
    Not (refLe fullRef emptyRef) := by
  intro h
  exact h (fun _ => false) True.intro

theorem complement_not_monotone :
    Not (MonotoneRef (fun X => complRef X)) := by
  intro hMono
  have hCompl : refLe (complRef emptyRef) (complRef fullRef) :=
    hMono empty_le_full
  apply full_not_le_empty
  intro s hs
  have hEmptyCompl : complRef emptyRef s := by
    intro hEmpty
    exact hEmpty
  have hFullCompl : complRef fullRef s := hCompl s hEmptyCompl
  exact hFullCompl hs

def oneAt (n : Nat) : Stream :=
  fun i => decide (i = n)

def finiteOneAtPrefix (n : Nat) : BoolRef :=
  fun s => exists i : Nat, i < n /\ s = oneAt i

theorem finiteOneAtPrefix_chain :
    ChainRef finiteOneAtPrefix := by
  intro n s h
  rcases h with ⟨i, hi, hs⟩
  exact ⟨i, Nat.lt_trans hi (Nat.lt_succ_self n), hs⟩

theorem oneAt_zero_in_union_prefix :
    iUnionRef finiteOneAtPrefix (oneAt 0) := by
  exact ⟨1, 0, Nat.zero_lt_succ 0, rfl⟩

theorem oneAt_zero_not_in_compl_union_prefix :
    Not (complRef (iUnionRef finiteOneAtPrefix) (oneAt 0)) := by
  intro h
  exact h oneAt_zero_in_union_prefix

theorem oneAt_zero_in_union_complements :
    iUnionRef (fun n => complRef (finiteOneAtPrefix n)) (oneAt 0) := by
  refine ⟨0, ?_⟩
  intro h
  rcases h with ⟨i, hi, hs⟩
  exact Nat.not_lt_zero i hi

theorem complement_not_omegaContinuous :
    Not (OmegaContinuousRef (fun X => complRef X)) := by
  intro hCont
  have hEq := hCont finiteOneAtPrefix finiteOneAtPrefix_chain (oneAt 0)
  have hLeft : complRef (iUnionRef finiteOneAtPrefix) (oneAt 0) :=
    hEq.mpr oneAt_zero_in_union_complements
  exact oneAt_zero_not_in_compl_union_prefix hLeft

theorem packet_j_receipt :
    Not (MonotoneRef (fun X => complRef X))
      /\ Not (OmegaContinuousRef (fun X => complRef X)) := by
  constructor
  · exact complement_not_monotone
  · exact complement_not_omegaContinuous

end AristotleUnsafeRecurrenceBoundary
