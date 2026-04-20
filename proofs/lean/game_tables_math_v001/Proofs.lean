/-!
# Game tables math v001

Bounded finite-game checker kernel for a Tau-style table feature.

The checked theorem is exact for a finite listed surface. It does not claim
mixed strategies, continuous action spaces, unbounded games, or full mechanism
design.
-/

namespace GameTablesMathV001

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

theorem profitable_deviation_refutes_br {Player Profile : Type}
    (g : ListedGame Player Profile) (i : Player) (p q : Profile)
    (hmem : q ∈ g.deviations i p)
    (hallowed : g.allowed q = true)
    (hgt : g.payoff i p < g.payoff i q) :
    brCheck g i p ≠ true := by
  intro hcheck
  have hbr : BestResponse g i p := (brCheck_true_iff g i p).mp hcheck
  have hle : g.payoff i q ≤ g.payoff i p := hbr q hmem hallowed
  exact Nat.not_lt_of_ge hle hgt

inductive AgentAction where
  | contribute
  | extract
  | exit
  deriving DecidableEq, Repr

inductive ProtocolAction where
  | reward
  | tax
  | quarantine
  deriving DecidableEq, Repr

structure Profile where
  agent : AgentAction
  protocol : ProtocolAction
  deriving DecidableEq, Repr

inductive Player where
  | agent
  deriving DecidableEq, Repr

def agentPayoff : Profile → Nat
  | ⟨.contribute, .reward⟩ => 42
  | ⟨.extract, .reward⟩ => 31
  | ⟨.exit, .reward⟩ => 10
  | ⟨.contribute, .tax⟩ => 25
  | ⟨.extract, .tax⟩ => 20
  | ⟨.exit, .tax⟩ => 10
  | ⟨.contribute, .quarantine⟩ => 12
  | ⟨.extract, .quarantine⟩ => 0
  | ⟨.exit, .quarantine⟩ => 10

def protocolSafe : Profile → Bool
  | ⟨.extract, .reward⟩ => false
  | _ => true

def desiredContribution : Profile → Bool
  | ⟨.contribute, .reward⟩ => true
  | _ => false

def agentDeviationProfiles (p : Profile) : List Profile :=
  [⟨.contribute, p.protocol⟩, ⟨.extract, p.protocol⟩, ⟨.exit, p.protocol⟩]

def toyGame : ListedGame Player Profile where
  players := [.agent]
  deviations := fun
    | .agent, p => agentDeviationProfiles p
  allowed := protocolSafe
  payoff := fun
    | .agent, p => agentPayoff p

def targetProfile : Profile :=
  ⟨.contribute, .reward⟩

example : safeNashCheck toyGame protocolSafe desiredContribution targetProfile = true := by
  native_decide

theorem targetProfile_safe_nash :
    SafeNash toyGame protocolSafe desiredContribution targetProfile :=
  (safeNashCheck_true_iff toyGame protocolSafe desiredContribution targetProfile).mp
    (by native_decide)

def badExtractRewardProfile : Profile :=
  ⟨.extract, .reward⟩

example : safeNashCheck toyGame protocolSafe desiredContribution badExtractRewardProfile = false := by
  native_decide

def allToyProfiles : List Profile :=
  [ ⟨.contribute, .reward⟩
  , ⟨.extract, .reward⟩
  , ⟨.exit, .reward⟩
  , ⟨.contribute, .tax⟩
  , ⟨.extract, .tax⟩
  , ⟨.exit, .tax⟩
  , ⟨.contribute, .quarantine⟩
  , ⟨.extract, .quarantine⟩
  , ⟨.exit, .quarantine⟩
  ]

example :
    existsSafeNashCheck toyGame protocolSafe desiredContribution allToyProfiles = true := by
  native_decide

theorem listed_toy_has_safe_nash :
    ∃ p, p ∈ allToyProfiles ∧ SafeNash toyGame protocolSafe desiredContribution p :=
  (existsSafeNashCheck_true_iff toyGame protocolSafe desiredContribution allToyProfiles).mp
    (by native_decide)

end ListedGame

end GameTablesMathV001
