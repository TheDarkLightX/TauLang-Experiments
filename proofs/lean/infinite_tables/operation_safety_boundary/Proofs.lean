import Mathlib.Order.CompleteBooleanAlgebra

/-!
# v553, Official Operation Safety Boundary

This cycle isolates the next table-language boundary after v552.

Safe:

* selecting by a fixed lower-stratum guard is monotone and omega-continuous,
* revising by a fixed lower-stratum guard and a fixed replacement is monotone
  and omega-continuous.

Unsafe:

* using the current recursive value as the guard can be anti-monotone,
* selecting by an arbitrary value predicate is not monotone in general.

This does not implement full TABA `select`, `common`, or revision. It proves the
semantic classifier that says which shapes may be admitted to the recursive
kernel without breaking the Kleene fixed-point lane.
-/

namespace OfficialOperationSafetyBoundary

def OmegaContinuous1 {α : Type*} [CompleteLattice α] (F : α -> α) : Prop :=
  forall X : Nat -> α,
    (forall n, X n <= X (n + 1)) ->
      F (⨆ n, X n) = ⨆ n, F (X n)

def fixedGuardSelect {α : Type*} [CompleteBooleanAlgebra α]
    (guard : α) : α -> α :=
  fun x => guard ⊓ x

def fixedGuardRevision {α : Type*} [CompleteBooleanAlgebra α]
    (guard replacement : α) : α -> α :=
  fun old => (guard ⊓ replacement) ⊔ (guardᶜ ⊓ old)

theorem fixedGuardSelect_mono {α : Type*} [CompleteBooleanAlgebra α]
    (guard : α) :
    Monotone (fixedGuardSelect guard) := by
  intro x y hxy
  exact inf_le_inf le_rfl hxy

theorem fixedGuardSelect_omegaContinuous {α : Type*}
    [CompleteBooleanAlgebra α] (guard : α) :
    OmegaContinuous1 (fixedGuardSelect guard) := by
  intro X _hchain
  simp only [fixedGuardSelect]
  rw [inf_iSup_eq]

theorem fixedGuardRevision_mono {α : Type*} [CompleteBooleanAlgebra α]
    (guard replacement : α) :
    Monotone (fixedGuardRevision guard replacement) := by
  intro x y hxy
  exact sup_le_sup le_rfl (inf_le_inf le_rfl hxy)

theorem fixedGuardRevision_omegaContinuous {α : Type*}
    [CompleteBooleanAlgebra α] (guard replacement : α) :
    OmegaContinuous1 (fixedGuardRevision guard replacement) := by
  intro X _hchain
  simp only [fixedGuardRevision]
  rw [inf_iSup_eq]
  rw [sup_iSup]

def currentGuardBadBool (b : Bool) : Bool :=
  (b ⊓ false) ⊔ (bᶜ ⊓ true)

theorem currentGuardBadBool_false :
    currentGuardBadBool false = true := by
  simp [currentGuardBadBool]

theorem currentGuardBadBool_true :
    currentGuardBadBool true = false := by
  simp [currentGuardBadBool]

theorem currentGuardBadBool_not_monotone :
    ¬ Monotone currentGuardBadBool := by
  intro hmono
  have hle : false <= true := by decide
  have hbad := hmono hle
  simp [currentGuardBadBool] at hbad
  have hnot : ¬ (true <= false) := by decide
  exact hnot hbad

def singletonFalse : Bool -> Bool
  | false => true
  | true => false

def topBoolSet : Bool -> Bool :=
  fun _ => true

def emptyBoolSet : Bool -> Bool :=
  fun _ => false

def isSingletonFalse (s : Bool -> Bool) : Bool :=
  s false && !(s true)

def arbitraryPredicateSelectSet (s : Bool -> Bool) : Bool -> Bool :=
  fun x =>
    match isSingletonFalse s with
    | true => s x
    | false => false

theorem univ_ne_singletonFalse :
    isSingletonFalse topBoolSet = false := by
  simp [isSingletonFalse, topBoolSet]

theorem arbitraryPredicateSelectSet_not_monotone :
    ¬ Monotone arbitraryPredicateSelectSet := by
  intro hmono
  have hle : singletonFalse <= topBoolSet := by
    intro x
    cases x <;> decide
  have hbad := hmono hle
  have hbadFalse := hbad false
  simp [arbitraryPredicateSelectSet, singletonFalse,
    univ_ne_singletonFalse] at hbadFalse
  have hnot : ¬ (true <= false) := by decide
  exact hnot hbadFalse

def commonWithSingletonFalseSet (s : Bool -> Bool) : Bool -> Bool :=
  fun x =>
    match isSingletonFalse s with
    | true => s x
    | false => false

theorem commonWithSingletonFalseSet_not_monotone :
    ¬ Monotone commonWithSingletonFalseSet := by
  simpa [commonWithSingletonFalseSet, arbitraryPredicateSelectSet]
    using arbitraryPredicateSelectSet_not_monotone

theorem v553_official_operation_boundary_receipt {α : Type*}
    [CompleteBooleanAlgebra α] (guard replacement : α) :
    Monotone (fixedGuardSelect guard) /\
      OmegaContinuous1 (fixedGuardSelect guard) /\
      Monotone (fixedGuardRevision guard replacement) /\
      OmegaContinuous1 (fixedGuardRevision guard replacement) /\
      ¬ Monotone currentGuardBadBool /\
      ¬ Monotone arbitraryPredicateSelectSet /\
      ¬ Monotone commonWithSingletonFalseSet := by
  constructor
  · exact fixedGuardSelect_mono guard
  constructor
  · exact fixedGuardSelect_omegaContinuous guard
  constructor
  · exact fixedGuardRevision_mono guard replacement
  constructor
  · exact fixedGuardRevision_omegaContinuous guard replacement
  constructor
  · exact currentGuardBadBool_not_monotone
  constructor
  · exact arbitraryPredicateSelectSet_not_monotone
  · exact commonWithSingletonFalseSet_not_monotone

end OfficialOperationSafetyBoundary
