/-!
# Aristotle task: bounded game table lowering

This project extends the checked finite-game kernel with:

1. first-match row-table lookup,
2. a table-backed listed game constructor,
3. a coverage theorem separating checker correctness from input completeness.

The target is bounded finite game tables for Tau demos, not general game theory.
-/

namespace GameTablesLift

def allB {α : Type} : List α → (α → Bool) → Bool
  | [], _ => true
  | x :: xs, p => p x && allB xs p

def anyB {α : Type} : List α → (α → Bool) → Bool
  | [], _ => false
  | x :: xs, p => p x || anyB xs p

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

end ListedGame

structure RowTable (Key Value : Type) where
  rows : List (Key × Value)
  default : Value

namespace RowTable

def lookupRows [DecidableEq Key] : List (Key × Value) → Value → Key → Value
  | [], default, _ => default
  | (k, v) :: rows, default, key =>
      if k = key then v else lookupRows rows default key

def lookup [DecidableEq Key] (t : RowTable Key Value) (key : Key) : Value :=
  lookupRows t.rows t.default key

def Missing (rows : List (Key × Value)) (key : Key) : Prop :=
  ∀ row, row ∈ rows → row.1 ≠ key

def FirstMatch (t : RowTable Key Value) (key : Key) (value : Value) : Prop :=
  ∃ pref suffix,
    t.rows = pref ++ (key, value) :: suffix ∧ Missing pref key

theorem lookupRows_eq_of_firstMatch [DecidableEq Key]
    (rows : List (Key × Value)) (default : Value) (key : Key) (value : Value)
    (h : ∃ pref suffix,
      rows = pref ++ (key, value) :: suffix ∧ Missing pref key) :
    lookupRows rows default key = value := by
  obtain ⟨pref, suffix, rfl, hmissing⟩ := h
  induction pref with
  | nil =>
    simp [lookupRows]
  | cons row pref ih =>
    have hrow : row.1 ≠ key := hmissing row (by simp)
    have htail : Missing pref key := by
      intro row' hmem
      exact hmissing row' (by simp [hmem])
    cases row with
    | mk k v =>
      simp [lookupRows, hrow, ih htail]

theorem lookup_eq_of_firstMatch [DecidableEq Key]
    (t : RowTable Key Value) (key : Key) (value : Value)
    (h : FirstMatch t key value) :
    lookup t key = value := by
  exact lookupRows_eq_of_firstMatch t.rows t.default key value h

theorem lookupRows_default_of_missing [DecidableEq Key]
    (rows : List (Key × Value)) (default : Value) (key : Key)
    (h : Missing rows key) :
    lookupRows rows default key = default := by
  induction rows with
  | nil =>
    simp [lookupRows]
  | cons row rows ih =>
    have hrow : row.1 ≠ key := h row (by simp)
    have htail : Missing rows key := by
      intro row' hmem
      exact h row' (by simp [hmem])
    cases row with
    | mk k v =>
      simp [lookupRows, hrow, ih htail]

theorem lookup_default_of_missing [DecidableEq Key]
    (t : RowTable Key Value) (key : Key)
    (h : Missing t.rows key) :
    lookup t key = t.default := by
  exact lookupRows_default_of_missing t.rows t.default key h

end RowTable

structure GameTables (Player Profile : Type) where
  players : List Player
  profiles : List Profile
  deviations : Player → Profile → List Profile
  allowedTable : RowTable Profile Bool
  safeTable : RowTable Profile Bool
  desiredTable : RowTable Profile Bool
  payoffTable : Player → RowTable Profile Nat

namespace GameTables

def allowed [DecidableEq Profile] (gt : GameTables Player Profile) : Profile → Bool :=
  RowTable.lookup gt.allowedTable

def safe [DecidableEq Profile] (gt : GameTables Player Profile) : Profile → Bool :=
  RowTable.lookup gt.safeTable

def desired [DecidableEq Profile] (gt : GameTables Player Profile) : Profile → Bool :=
  RowTable.lookup gt.desiredTable

def payoff [DecidableEq Profile] (gt : GameTables Player Profile) :
    Player → Profile → Nat :=
  fun i p => RowTable.lookup (gt.payoffTable i) p

def toListedGame [DecidableEq Profile] (gt : GameTables Player Profile) :
    ListedGame Player Profile where
  players := gt.players
  deviations := gt.deviations
  allowed := allowed gt
  payoff := payoff gt

theorem table_safe_search_true_iff [DecidableEq Profile]
    (gt : GameTables Player Profile) :
    ListedGame.existsSafeNashCheck (toListedGame gt) (safe gt) (desired gt)
        gt.profiles = true ↔
      ∃ p, p ∈ gt.profiles ∧
        ListedGame.SafeNash (toListedGame gt) (safe gt) (desired gt) p := by
  exact ListedGame.existsSafeNashCheck_true_iff
    (toListedGame gt) (safe gt) (desired gt) gt.profiles

def IntendedBestResponse (g : ListedGame Player Profile)
    (IntendedDeviation : Player → Profile → Profile → Prop)
    (i : Player) (p : Profile) : Prop :=
  ∀ q, IntendedDeviation i p q → g.allowed q = true →
    g.payoff i q ≤ g.payoff i p

def IntendedNash (g : ListedGame Player Profile)
    (IntendedPlayer : Player → Prop)
    (IntendedDeviation : Player → Profile → Profile → Prop)
    (p : Profile) : Prop :=
  g.allowed p = true ∧
    ∀ i, IntendedPlayer i → IntendedBestResponse g IntendedDeviation i p

def IntendedSafeNash (g : ListedGame Player Profile)
    (IntendedPlayer : Player → Prop)
    (IntendedDeviation : Player → Profile → Profile → Prop)
    (safe desired : Profile → Bool) (p : Profile) : Prop :=
  IntendedNash g IntendedPlayer IntendedDeviation p ∧
    safe p = true ∧ desired p = true

theorem listed_nash_sound_for_intended
    (g : ListedGame Player Profile)
    (IntendedPlayer : Player → Prop)
    (IntendedDeviation : Player → Profile → Profile → Prop)
    (hplayers : ∀ i, IntendedPlayer i → i ∈ g.players)
    (hdeviations :
      ∀ i p q, IntendedPlayer i → IntendedDeviation i p q →
        q ∈ g.deviations i p)
    (p : Profile)
    (h : ListedGame.Nash g p) :
    IntendedNash g IntendedPlayer IntendedDeviation p := by
  unfold IntendedNash IntendedBestResponse
  constructor
  · exact h.1
  · intro i hi q hdev hallowed
    exact h.2 i (hplayers i hi) q (hdeviations i p q hi hdev) hallowed

theorem listed_safe_search_sound_for_intended [DecidableEq Profile]
    (gt : GameTables Player Profile)
    (IntendedProfile : Profile → Prop)
    (IntendedPlayer : Player → Prop)
    (IntendedDeviation : Player → Profile → Profile → Prop)
    (hprofileSound : ∀ p, p ∈ gt.profiles → IntendedProfile p)
    (hplayers : ∀ i, IntendedPlayer i → i ∈ gt.players)
    (hdeviations :
      ∀ i p q, IntendedPlayer i → IntendedDeviation i p q →
        q ∈ gt.deviations i p)
    (hcheck :
      ListedGame.existsSafeNashCheck (toListedGame gt) (safe gt) (desired gt)
        gt.profiles = true) :
    ∃ p, IntendedProfile p ∧ p ∈ gt.profiles ∧
      IntendedSafeNash (toListedGame gt)
        IntendedPlayer IntendedDeviation (safe gt) (desired gt) p := by
  have hlisted :
      ∃ p, p ∈ gt.profiles ∧
        ListedGame.SafeNash (toListedGame gt) (safe gt) (desired gt) p :=
    (table_safe_search_true_iff gt).mp hcheck
  obtain ⟨p, hpMem, hpSafe⟩ := hlisted
  exact ⟨p, hprofileSound p hpMem, hpMem,
    ⟨listed_nash_sound_for_intended (toListedGame gt)
      IntendedPlayer IntendedDeviation hplayers hdeviations p hpSafe.1,
      hpSafe.2.1, hpSafe.2.2⟩⟩

end GameTables

end GameTablesLift
