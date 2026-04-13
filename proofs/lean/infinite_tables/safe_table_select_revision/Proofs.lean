import Mathlib.Order.CompleteBooleanAlgebra

/-!
# v554, Safe Table Syntax with Select and Revision

This cycle folds v553 back into the table grammar. Safe `select` and `revise`
are first-class value constructors, not just external lemmas.

Scope:

* row guards read fixed lower-stratum data,
* `select` uses a fixed lower-stratum guard,
* `revise` uses a fixed lower-stratum guard,
* recursive references remain positive,
* lower-stratum prime is allowed because it is fixed relative to the current
  recurrence,
* explicit defaults are required.

Boundary:

* no same-stratum prime,
* no current-state-dependent row guards,
* no current-state-dependent select or revision guards,
* no arbitrary value-predicate select,
* no equality-style recursive `common`,
* no NSO, Guarded Successor, or Tau runtime lowering.
-/

namespace SafeTableSyntaxWithSelectRevision

abbrev State (I α : Type*) := I -> α
abbrev LowerEnv (L α : Type*) := L -> α

inductive GuardTerm (L α : Type*) where
  | bot : GuardTerm L α
  | top : GuardTerm L α
  | const : α -> GuardTerm L α
  | lower : L -> GuardTerm L α
  | lowerPrime : L -> GuardTerm L α
  | meet : GuardTerm L α -> GuardTerm L α -> GuardTerm L α
  | join : GuardTerm L α -> GuardTerm L α -> GuardTerm L α
deriving Repr

inductive ValueTerm (I L α : Type*) where
  | bot : ValueTerm I L α
  | top : ValueTerm I L α
  | const : α -> ValueTerm I L α
  | ref : I -> ValueTerm I L α
  | lower : L -> ValueTerm I L α
  | lowerPrime : L -> ValueTerm I L α
  | meet : ValueTerm I L α -> ValueTerm I L α -> ValueTerm I L α
  | join : ValueTerm I L α -> ValueTerm I L α -> ValueTerm I L α
  | cond :
      GuardTerm L α -> ValueTerm I L α -> ValueTerm I L α ->
        ValueTerm I L α
  | select : GuardTerm L α -> ValueTerm I L α -> ValueTerm I L α
  | revise :
      GuardTerm L α -> ValueTerm I L α -> ValueTerm I L α ->
        ValueTerm I L α
deriving Repr

structure TableRow (I L α : Type*) where
  guard : GuardTerm L α
  value : ValueTerm I L α
deriving Repr

structure TableExpr (I L α : Type*) where
  rows : List (TableRow I L α)
  default : ValueTerm I L α
deriving Repr

def evalGuard {L α : Type*} [CompleteBooleanAlgebra α]
    (lower : LowerEnv L α) : GuardTerm L α -> α
  | .bot => ⊥
  | .top => ⊤
  | .const v => v
  | .lower l => lower l
  | .lowerPrime l => (lower l)ᶜ
  | .meet a b => evalGuard lower a ⊓ evalGuard lower b
  | .join a b => evalGuard lower a ⊔ evalGuard lower b

def guardedChoice {α : Type*} [CompleteBooleanAlgebra α]
    (guard thenValue elseValue : α) : α :=
  (guard ⊓ thenValue) ⊔ (guardᶜ ⊓ elseValue)

def fixedSelect {α : Type*} [CompleteBooleanAlgebra α]
    (guard value : α) : α :=
  guard ⊓ value

def fixedRevision {α : Type*} [CompleteBooleanAlgebra α]
    (guard replacement old : α) : α :=
  guardedChoice guard replacement old

def evalValue {I L α : Type*} [CompleteBooleanAlgebra α]
    (lower : LowerEnv L α) (s : State I α) : ValueTerm I L α -> α
  | .bot => ⊥
  | .top => ⊤
  | .const v => v
  | .ref i => s i
  | .lower l => lower l
  | .lowerPrime l => (lower l)ᶜ
  | .meet a b => evalValue lower s a ⊓ evalValue lower s b
  | .join a b => evalValue lower s a ⊔ evalValue lower s b
  | .cond g a b =>
      guardedChoice (evalGuard lower g)
        (evalValue lower s a)
        (evalValue lower s b)
  | .select g a =>
      fixedSelect (evalGuard lower g) (evalValue lower s a)
  | .revise g replacement old =>
      fixedRevision (evalGuard lower g)
        (evalValue lower s replacement)
        (evalValue lower s old)

def evalRows {I L α : Type*} [CompleteBooleanAlgebra α]
    (lower : LowerEnv L α) (s : State I α) :
    List (TableRow I L α) -> ValueTerm I L α -> α
  | [], default => evalValue lower s default
  | row :: rows, default =>
      guardedChoice (evalGuard lower row.guard)
        (evalValue lower s row.value)
        (evalRows lower s rows default)

def denoteTable {I L α : Type*} [CompleteBooleanAlgebra α]
    (lower : LowerEnv L α) (s : State I α)
    (table : TableExpr I L α) : α :=
  evalRows lower s table.rows table.default

def updateTables {I L α : Type*} [CompleteBooleanAlgebra α]
    (lower : LowerEnv L α) (body : I -> TableExpr I L α) :
    State I α -> State I α :=
  fun s i => denoteTable lower s (body i)

def OmegaContinuous {I α : Type*} [CompleteLattice α]
    (F : State I α -> State I α) : Prop :=
  forall X : Nat -> State I α,
    (forall n, X n <= X (n + 1)) ->
      F (⨆ n, X n) = ⨆ n, F (X n)

theorem evalValue_mono {I L α : Type*} [CompleteBooleanAlgebra α]
    (lower : LowerEnv L α) {s t : State I α} (hst : s <= t) :
    forall e : ValueTerm I L α, evalValue lower s e <= evalValue lower t e
  | .bot => by simp [evalValue]
  | .top => by simp [evalValue]
  | .const _ => by simp [evalValue]
  | .ref i => hst i
  | .lower _ => by simp [evalValue]
  | .lowerPrime _ => by simp [evalValue]
  | .meet a b =>
      inf_le_inf (evalValue_mono lower hst a) (evalValue_mono lower hst b)
  | .join a b =>
      sup_le_sup (evalValue_mono lower hst a) (evalValue_mono lower hst b)
  | .cond g a b => by
      simp only [evalValue, guardedChoice]
      exact sup_le_sup
        (inf_le_inf le_rfl (evalValue_mono lower hst a))
        (inf_le_inf le_rfl (evalValue_mono lower hst b))
  | .select g a => by
      simp only [evalValue, fixedSelect]
      exact inf_le_inf le_rfl (evalValue_mono lower hst a)
  | .revise g replacement old => by
      simp only [evalValue, fixedRevision, guardedChoice]
      exact sup_le_sup
        (inf_le_inf le_rfl (evalValue_mono lower hst replacement))
        (inf_le_inf le_rfl (evalValue_mono lower hst old))

theorem evalRows_mono {I L α : Type*} [CompleteBooleanAlgebra α]
    (lower : LowerEnv L α) {s t : State I α} (hst : s <= t) :
    forall (rows : List (TableRow I L α)) (default : ValueTerm I L α),
      evalRows lower s rows default <= evalRows lower t rows default
  | [], default => evalValue_mono lower hst default
  | row :: rows, default => by
      simp only [evalRows, guardedChoice]
      exact sup_le_sup
        (inf_le_inf le_rfl (evalValue_mono lower hst row.value))
        (inf_le_inf le_rfl (evalRows_mono lower hst rows default))

theorem updateTables_mono {I L α : Type*} [CompleteBooleanAlgebra α]
    (lower : LowerEnv L α) (body : I -> TableExpr I L α) :
    Monotone (updateTables lower body) := by
  intro s t hst i
  exact evalRows_mono lower hst (body i).rows (body i).default

theorem evalValue_chain_mono {I L α : Type*} [CompleteBooleanAlgebra α]
    (lower : LowerEnv L α)
    (X : Nat -> State I α)
    (hchain : forall n, X n <= X (n + 1))
    (e : ValueTerm I L α) :
    Monotone fun n => evalValue lower (X n) e := by
  exact monotone_nat_of_le_succ fun n => evalValue_mono lower (hchain n) e

theorem evalValue_iSup_of_chain {I L α : Type*} [CompleteBooleanAlgebra α]
    (lower : LowerEnv L α)
    (X : Nat -> State I α)
    (hchain : forall n, X n <= X (n + 1)) :
    forall e : ValueTerm I L α,
      evalValue lower (⨆ n, X n) e =
        ⨆ n, evalValue lower (X n) e
  | .bot => by simp [evalValue]
  | .top => by simp only [evalValue]; rw [iSup_const]
  | .const v => by simp only [evalValue]; rw [iSup_const]
  | .ref i => by simp [evalValue]
  | .lower l => by simp only [evalValue]; rw [iSup_const]
  | .lowerPrime l => by simp only [evalValue]; rw [iSup_const]
  | .meet a b => by
      simp only [evalValue]
      rw [evalValue_iSup_of_chain lower X hchain a,
        evalValue_iSup_of_chain lower X hchain b]
      exact (iSup_inf_of_monotone
        (evalValue_chain_mono lower X hchain a)
        (evalValue_chain_mono lower X hchain b)).symm
  | .join a b => by
      simp only [evalValue]
      rw [evalValue_iSup_of_chain lower X hchain a,
        evalValue_iSup_of_chain lower X hchain b]
      rw [← iSup_sup_eq]
  | .cond g a b => by
      simp only [evalValue, guardedChoice]
      rw [evalValue_iSup_of_chain lower X hchain a,
        evalValue_iSup_of_chain lower X hchain b]
      rw [inf_iSup_eq, inf_iSup_eq]
      rw [← iSup_sup_eq]
  | .select g a => by
      simp only [evalValue, fixedSelect]
      rw [evalValue_iSup_of_chain lower X hchain a]
      rw [inf_iSup_eq]
  | .revise g replacement old => by
      simp only [evalValue, fixedRevision, guardedChoice]
      rw [evalValue_iSup_of_chain lower X hchain replacement,
        evalValue_iSup_of_chain lower X hchain old]
      rw [inf_iSup_eq, inf_iSup_eq]
      rw [← iSup_sup_eq]

theorem evalRows_iSup_of_chain {I L α : Type*} [CompleteBooleanAlgebra α]
    (lower : LowerEnv L α)
    (X : Nat -> State I α)
    (hchain : forall n, X n <= X (n + 1)) :
    forall (rows : List (TableRow I L α)) (default : ValueTerm I L α),
      evalRows lower (⨆ n, X n) rows default =
        ⨆ n, evalRows lower (X n) rows default
  | [], default => evalValue_iSup_of_chain lower X hchain default
  | row :: rows, default => by
      simp only [evalRows, guardedChoice]
      rw [evalValue_iSup_of_chain lower X hchain row.value,
        evalRows_iSup_of_chain lower X hchain rows default]
      rw [inf_iSup_eq, inf_iSup_eq]
      rw [← iSup_sup_eq]

theorem updateTables_omegaContinuous {I L α : Type*}
    [CompleteBooleanAlgebra α]
    (lower : LowerEnv L α) (body : I -> TableExpr I L α) :
    OmegaContinuous (updateTables lower body) := by
  intro X hchain
  funext i
  simp only [updateTables, denoteTable, iSup_apply]
  exact evalRows_iSup_of_chain lower X hchain (body i).rows (body i).default

def approx {I α : Type*} [CompleteLattice α]
    (F : State I α -> State I α) : Nat -> State I α
  | 0 => ⊥
  | n + 1 => F (approx F n)

theorem approx_chain {I α : Type*} [CompleteLattice α]
    {F : State I α -> State I α} (hmono : Monotone F) :
    forall n, approx F n <= approx F (n + 1)
  | 0 => bot_le
  | n + 1 => hmono (approx_chain hmono n)

theorem iSup_shift_eq_of_chain {α : Type*} [CompleteLattice α]
    (X : Nat -> α) (hchain : forall n, X n <= X (n + 1)) :
    (⨆ n, X (n + 1)) = ⨆ n, X n := by
  apply le_antisymm
  · exact iSup_le fun n => le_iSup (fun m => X m) (n + 1)
  · apply iSup_le
    intro n
    cases n with
    | zero =>
        exact (hchain 0).trans (le_iSup (fun m => X (m + 1)) 0)
    | succ n =>
        exact le_iSup (fun m => X (m + 1)) n

def omegaSup {I α : Type*} [CompleteLattice α]
    (F : State I α -> State I α) : State I α :=
  ⨆ n, approx F n

theorem safe_table_update_fixed {I L α : Type*}
    [CompleteBooleanAlgebra α]
    (lower : LowerEnv L α) (body : I -> TableExpr I L α) :
    let F := updateTables lower body
    F (omegaSup F) = omegaSup F := by
  intro F
  have hmono : Monotone F := updateTables_mono lower body
  have hcont : OmegaContinuous F := updateTables_omegaContinuous lower body
  unfold omegaSup
  rw [hcont (approx F) (approx_chain hmono)]
  exact iSup_shift_eq_of_chain (approx F) (approx_chain hmono)

theorem v554_safe_table_select_revision_receipt {I L α : Type*}
    [CompleteBooleanAlgebra α]
    (lower : LowerEnv L α) (body : I -> TableExpr I L α) :
    Monotone (updateTables lower body) /\
      OmegaContinuous (updateTables lower body) /\
      (let F := updateTables lower body
       F (omegaSup F) = omegaSup F) := by
  constructor
  · exact updateTables_mono lower body
  constructor
  · exact updateTables_omegaContinuous lower body
  · exact safe_table_update_fixed lower body

end SafeTableSyntaxWithSelectRevision
