import Mathlib.Order.BooleanAlgebra.Basic

/-!
A decision procedure for finite conjunctions of guarded clauses over a single
Boolean algebra. Zero tests must be decidable to execute the algorithm.
-/
namespace GuardedWitness

variable {α : Type*} [BooleanAlgebra α]

abbrev Clause (α : Type*) := α × α

def Holds (x : α) (c : Clause α) : Prop := x ⊓ c.1 = ⊥ ∨ x ⊓ c.2 ≠ ⊥

def Feasible (b : α) (cs : List (Clause α)) (x : α) : Prop :=
  x ≤ b ∧ ∀ c ∈ cs, Holds x c

theorem le_complement_iff {x y : α} : x ≤ yᶜ ↔ x ⊓ y = ⊥ :=
  le_compl_iff_disjoint_right.trans disjoint_iff

/-- Closing a dead positive branch cannot lose a feasible witness. -/
theorem preserve {x b : α} {c : Clause α} (hx : x ≤ b)
    (hc : Holds x c) (dead : b ⊓ c.2 = ⊥) : x ≤ b ⊓ c.1ᶜ := by
  have impossible : x ⊓ c.2 = ⊥ := bot_unique (dead ▸ inf_le_inf_right c.2 hx)
  exact le_inf hx (le_complement_iff.mpr (hc.resolve_right (fun h => h impossible)))

/-- A stable upper bound satisfies every guard. -/
theorem stable_holds {b : α} {cs : List (Clause α)}
    (stable : ∀ c ∈ cs, b ⊓ c.2 = ⊥ → b ≤ c.1ᶜ) :
    ∀ c ∈ cs, Holds b c := by
  intro c hc
  by_cases h : b ⊓ c.2 = ⊥
  · exact Or.inl (le_complement_iff.mp (stable c hc h))
  · exact Or.inr h

variable [DecidableEq α]

/-- Find a dead positive branch and discharge it by shrinking the bound.
The clause remains true at every future smaller bound, so it is removed. -/
def solve : Nat → α → List (Clause α) → α
  | 0, b, _ => b
  | n + 1, b, cs =>
      match cs.find? (fun c => decide (b ⊓ c.2 = ⊥)) with
      | none => b
      | some c => solve n (b ⊓ c.1ᶜ) (cs.erase c)

/-- One unit of fuel per clause suffices, even in an infinite Boolean algebra. -/
theorem greatest (n : Nat) (b : α) (cs : List (Clause α)) (fuel : cs.length ≤ n) :
    Feasible b cs (solve n b cs) ∧ ∀ x, Feasible b cs x → x ≤ solve n b cs := by
  induction n generalizing b cs with
  | zero =>
    have empty : cs = [] := List.length_eq_zero_iff.mp (Nat.eq_zero_of_le_zero fuel)
    subst cs
    exact ⟨⟨le_rfl, by simp⟩, fun _ hx => hx.1⟩
  | succ n ih =>
    simp only [solve]
    split
    next h =>
      refine ⟨⟨le_rfl, ?_⟩, fun _ hx => hx.1⟩
      intro c hc
      exact Or.inr (by simpa using (List.find?_eq_none.mp h c hc))
    next c h =>
      have member := List.mem_of_find?_eq_some h
      have dead : b ⊓ c.2 = ⊥ := by simpa using List.find?_some h
      have short : (cs.erase c).length ≤ n := by
        rw [List.length_erase_of_mem member]
        omega
      obtain ⟨valid, dominates⟩ := ih (b ⊓ c.1ᶜ) (cs.erase c) short
      refine ⟨⟨valid.1.trans inf_le_left, ?_⟩, ?_⟩
      · intro d hd
        by_cases same : d = c
        · subst d
          exact Or.inl (le_complement_iff.mp (valid.1.trans inf_le_right))
        · exact valid.2 d ((List.mem_erase_of_ne same).mpr hd)
      · intro x hx
        exact dominates x ⟨preserve hx.1 (hx.2 c member) dead,
          fun d hd => hx.2 d (List.mem_of_mem_erase hd)⟩

/-- Every monotone additional requirement can be checked on this one witness.
The starting bound is precisely the equation x ⊓ y = ⊥. -/
theorem eliminate (y : α) (cs : List (Clause α)) (P : α → Prop)
    (upward : ∀ ⦃x z : α⦄, x ≤ z → P x → P z) :
    (∃ x, x ⊓ y = ⊥ ∧ (∀ c ∈ cs, Holds x c) ∧ P x) ↔
      P (solve cs.length yᶜ cs) := by
  obtain ⟨valid, dominates⟩ := greatest cs.length yᶜ cs le_rfl
  constructor
  · rintro ⟨x,hxy,hcs,hp⟩
    exact upward (dominates x ⟨le_complement_iff.mpr hxy,hcs⟩) hp
  · intro hp
    exact ⟨_,le_complement_iff.mp valid.1,valid.2,hp⟩

theorem nonzero (y : α) (cs : List (Clause α)) :
    (∃ x, x ⊓ y = ⊥ ∧ (∀ c ∈ cs, Holds x c) ∧ x ≠ ⊥) ↔
      solve cs.length yᶜ cs ≠ ⊥ := by
  apply eliminate
  intro x z h hx hz
  exact hx (bot_unique (hz ▸ h))

#print axioms preserve
#print axioms stable_holds
#print axioms greatest
#print axioms eliminate
#print axioms nonzero

end GuardedWitness
