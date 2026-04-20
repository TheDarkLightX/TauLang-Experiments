/-!
# Aristotle task: profitable-deviation pruning

If a candidate profile has a listed profitable unilateral deviation, it cannot
be a Nash profile. Therefore a finite game-table solver may prune profiles
certified by such evidence without changing whether a safe Nash profile exists.
-/

namespace GameTablesDominancePruning

def anyB {α : Type} : List α → (α → Bool) → Bool
  | [], _ => false
  | x :: xs, p => p x || anyB xs p

theorem anyB_true_iff {α : Type} (xs : List α) (p : α → Bool) :
    anyB xs p = true ↔ ∃ x, x ∈ xs ∧ p x = true := by
  induction xs with
  | nil =>
    simp [anyB]
  | cons x xs ih =>
    constructor
    · intro h
      simp [anyB] at h
      cases h with
      | inl hx =>
        exact ⟨x, by simp, hx⟩
      | inr hxs =>
        obtain ⟨y, hy, hp⟩ := ih.mp hxs
        exact ⟨y, by simp [hy], hp⟩
    · intro h
      obtain ⟨y, hy, hp⟩ := h
      simp [anyB]
      cases hy with
      | head =>
        exact Or.inl hp
      | tail _ hyTail =>
        exact Or.inr (ih.mpr ⟨y, hyTail, hp⟩)

def allB {α : Type} : List α → (α → Bool) → Bool
  | [], _ => true
  | x :: xs, p => p x && allB xs p

theorem allB_true_iff {α : Type} (xs : List α) (p : α → Bool) :
    allB xs p = true ↔ ∀ x, x ∈ xs → p x = true := by
  induction xs with
  | nil =>
    simp [allB]
  | cons x xs ih =>
    constructor
    · intro h y hy
      simp [allB] at h
      cases hy with
      | head =>
        exact h.1
      | tail _ hyTail =>
        exact ih.mp h.2 y hyTail
    · intro h
      simp [allB]
      constructor
      · exact h x (by simp)
      · exact ih.mpr (fun y hy => h y (by simp [hy]))

structure ListedGame (Player Profile : Type) where
  players : List Player
  deviations : Player → Profile → List Profile
  allowed : Profile → Bool
  payoff : Player → Profile → Nat

namespace ListedGame

def deviationOk {Player Profile : Type} (g : ListedGame Player Profile)
    (i : Player) (p q : Profile) : Bool :=
  if g.allowed q then
    decide (g.payoff i q ≤ g.payoff i p)
  else
    true

def BestResponse {Player Profile : Type} (g : ListedGame Player Profile)
    (i : Player) (p : Profile) : Prop :=
  ∀ q, q ∈ g.deviations i p → g.allowed q = true →
    g.payoff i q ≤ g.payoff i p

def Nash {Player Profile : Type} (g : ListedGame Player Profile)
    (p : Profile) : Prop :=
  g.allowed p = true ∧
    ∀ i, i ∈ g.players → BestResponse g i p

def brCheck {Player Profile : Type} (g : ListedGame Player Profile)
    (i : Player) (p : Profile) : Bool :=
  allB (g.deviations i p) (fun q => deviationOk g i p q)

def nashCheck {Player Profile : Type} (g : ListedGame Player Profile)
    (p : Profile) : Bool :=
  g.allowed p && allB g.players (fun i => brCheck g i p)

theorem deviationOk_true_iff {Player Profile : Type}
    (g : ListedGame Player Profile) (i : Player) (p q : Profile) :
    deviationOk g i p q = true ↔
      (g.allowed q = true → g.payoff i q ≤ g.payoff i p) := by
  unfold deviationOk
  cases g.allowed q <;> simp

theorem brCheck_true_iff {Player Profile : Type}
    (g : ListedGame Player Profile) (i : Player) (p : Profile) :
    brCheck g i p = true ↔ BestResponse g i p := by
  unfold brCheck BestResponse
  rw [allB_true_iff]
  constructor
  · intro h q hmem hallowed
    exact (deviationOk_true_iff g i p q).mp (h q hmem) hallowed
  · intro h q hmem
    exact (deviationOk_true_iff g i p q).mpr (h q hmem)

theorem nashCheck_true_iff {Player Profile : Type}
    (g : ListedGame Player Profile) (p : Profile) :
    nashCheck g p = true ↔ Nash g p := by
  unfold nashCheck Nash
  rw [Bool.and_eq_true, allB_true_iff]
  constructor
  · intro h
    exact ⟨h.1, fun i hi => (brCheck_true_iff g i p).mp (h.2 i hi)⟩
  · intro h
    exact ⟨h.1, fun i hi => (brCheck_true_iff g i p).mpr (h.2 i hi)⟩

def SafeNash {Player Profile : Type} (g : ListedGame Player Profile)
    (safe desired : Profile → Bool) (p : Profile) : Prop :=
  Nash g p ∧ safe p = true ∧ desired p = true

def safeNashCheck {Player Profile : Type} (g : ListedGame Player Profile)
    (safe desired : Profile → Bool) (p : Profile) : Bool :=
  nashCheck g p && safe p && desired p

def existsSafeNashCheck {Player Profile : Type} (g : ListedGame Player Profile)
    (safe desired : Profile → Bool) (profiles : List Profile) : Bool :=
  anyB profiles (fun p => safeNashCheck g safe desired p)

theorem safeNashCheck_true_iff {Player Profile : Type}
    (g : ListedGame Player Profile)
    (safe desired : Profile → Bool) (p : Profile) :
    safeNashCheck g safe desired p = true ↔ SafeNash g safe desired p := by
  unfold safeNashCheck SafeNash
  rw [Bool.and_eq_true, Bool.and_eq_true]
  constructor
  · intro h
    exact ⟨(nashCheck_true_iff g p).mp h.1.1, h.1.2, h.2⟩
  · intro h
    exact ⟨⟨(nashCheck_true_iff g p).mpr h.1, h.2.1⟩, h.2.2⟩

theorem existsSafeNashCheck_true_iff {Player Profile : Type}
    (g : ListedGame Player Profile)
    (safe desired : Profile → Bool) (profiles : List Profile) :
    existsSafeNashCheck g safe desired profiles = true ↔
      ∃ p, p ∈ profiles ∧ SafeNash g safe desired p := by
  unfold existsSafeNashCheck
  rw [anyB_true_iff]
  constructor
  · intro h
    obtain ⟨p, hpMem, hpCheck⟩ := h
    exact ⟨p, hpMem, (safeNashCheck_true_iff g safe desired p).mp hpCheck⟩
  · intro h
    obtain ⟨p, hpMem, hpSafe⟩ := h
    exact ⟨p, hpMem, (safeNashCheck_true_iff g safe desired p).mpr hpSafe⟩

def HasProfitableDeviation {Player Profile : Type}
    (g : ListedGame Player Profile) (p : Profile) : Prop :=
  ∃ i q,
    i ∈ g.players ∧ q ∈ g.deviations i p ∧
    g.allowed q = true ∧ g.payoff i p < g.payoff i q

theorem profitable_deviation_not_nash {Player Profile : Type}
    (g : ListedGame Player Profile) (p : Profile)
    (h : HasProfitableDeviation g p) :
    ¬ Nash g p := by
  intro hnash
  obtain ⟨i, q, hi, hq, hallowed, hgt⟩ := h
  have hbr : BestResponse g i p := hnash.2 i hi
  have hle : g.payoff i q ≤ g.payoff i p := hbr q hq hallowed
  exact Nat.not_lt_of_ge hle hgt

theorem profitable_deviation_not_safe_nash {Player Profile : Type}
    (g : ListedGame Player Profile) (safe desired : Profile → Bool)
    (p : Profile)
    (h : HasProfitableDeviation g p) :
    ¬ SafeNash g safe desired p := by
  intro hs
  exact profitable_deviation_not_nash g p h hs.1

end ListedGame

def pruneProfiles {Profile : Type} (profiles : List Profile)
    (bad : Profile → Bool) : List Profile :=
  profiles.filter (fun p => !bad p)

theorem pruneProfiles_preserves_any_good {Profile : Type}
    (profiles : List Profile) (bad good : Profile → Bool)
    (hbad : ∀ p, p ∈ profiles → bad p = true → good p = true → False) :
    anyB (pruneProfiles profiles bad) good = anyB profiles good := by
  have hiff :
      anyB (pruneProfiles profiles bad) good = true ↔
        anyB profiles good = true := by
    rw [anyB_true_iff, anyB_true_iff]
    constructor
    · intro h
      obtain ⟨p, hpMem, hpGood⟩ := h
      have hpOrig : p ∈ profiles := by
        have hpPair : p ∈ profiles ∧ bad p = false := by
          simpa [pruneProfiles] using hpMem
        exact hpPair.1
      exact ⟨p, hpOrig, hpGood⟩
    · intro h
      obtain ⟨p, hpMem, hpGood⟩ := h
      have hpBadFalse : bad p = false := by
        cases hb : bad p with
        | false => rfl
        | true => exact False.elim (hbad p hpMem hb hpGood)
      exact ⟨p, by simp [pruneProfiles, hpMem, hpBadFalse], hpGood⟩
  exact Bool.eq_iff_iff.mpr hiff

theorem prune_profitable_profiles_preserves_safe_search
    {Player Profile : Type}
    (g : ListedGame Player Profile)
    (safe desired : Profile → Bool)
    (profiles : List Profile)
    (bad : Profile → Bool)
    (hbad :
      ∀ p, p ∈ profiles → bad p = true →
        ListedGame.HasProfitableDeviation g p) :
    ListedGame.existsSafeNashCheck g safe desired
        (pruneProfiles profiles bad) =
      ListedGame.existsSafeNashCheck g safe desired profiles := by
  unfold ListedGame.existsSafeNashCheck
  apply pruneProfiles_preserves_any_good
  intro p hpMem hpBad hpGood
  have hpSafe : ListedGame.SafeNash g safe desired p :=
    (ListedGame.safeNashCheck_true_iff g safe desired p).mp hpGood
  exact ListedGame.profitable_deviation_not_safe_nash
    g safe desired p (hbad p hpMem hpBad) hpSafe

end GameTablesDominancePruning
