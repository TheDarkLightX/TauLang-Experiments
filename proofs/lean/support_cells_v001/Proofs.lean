import Std

/-! Finite support refinement for atomless Boolean subalgebras of sets.
The carrier consists of predicates on X belonging to a family closed under
Boolean operations. The only atomless hypothesis is proper nonempty splitting.
-/

namespace SupportCells

structure AtomlessField (X : Type) where
  member : (X → Prop) → Prop
  empty_mem : member (fun _ => False)
  full_mem : member (fun _ => True)
  union_mem : ∀ {p q}, member p → member q → member (fun x => p x ∨ q x)
  inter_mem : ∀ {p q}, member p → member q → member (fun x => p x ∧ q x)
  compl_mem : ∀ {p}, member p → member (fun x => ¬ p x)
  split : ∀ {p}, member p → (∃ x, p x) →
    ∃ q, member q ∧ (∀ x, q x → p x) ∧
      (∃ x, q x) ∧ (∃ x, p x ∧ ¬ q x)

def support {X I : Type} (label : X → I) (i : I) : Prop :=
  ∃ x, label x = i

def childSupport {X I : Type} (label : X → I) (q : X → Prop)
    (i : I) (b : Bool) : Prop :=
  ∃ x, label x = i ∧ if b then q x else ¬ q x

def Legal {X I : Type} (label : X → I) (r : I → Bool → Prop) : Prop :=
  ∀ i, support label i ↔ r i false ∨ r i true

theorem child_support_legal {X I : Type} (label : X → I) (q : X → Prop) :
    Legal label (childSupport label q) := by
  classical
  intro i
  constructor
  · rintro ⟨x, hx⟩
    by_cases hq : q x
    · exact Or.inr ⟨x, hx, hq⟩
    · exact Or.inl ⟨x, hx, hq⟩
  · intro h
    rcases h with ⟨x, hx, _⟩ | ⟨x, hx, _⟩ <;> exact ⟨x, hx⟩

theorem finite_union_member {X I : Type} (A : AtomlessField X)
    (is : List I) (p : I → X → Prop) (hp : ∀ i, A.member (p i)) :
    A.member (fun x => ∃ i, i ∈ is ∧ p i x) := by
  induction is with
  | nil => simpa using A.empty_mem
  | cons i is ih =>
    have h := A.union_mem (hp i) ih
    simpa only [List.mem_cons, exists_eq_or_imp, or_and_right,
      exists_or, exists_eq_left] using h

/-- A prescribed pair of child-occupancy bits can be realized inside one cell.
The split hypothesis is used only when both children are required. -/
theorem realize_one_cell {X I : Type} (A : AtomlessField X)
    (label : X → I) (i : I) (hm : A.member (fun x => label x = i))
    (r : I → Bool → Prop) (legal : Legal label r) :
    ∃ q, A.member q ∧ (∀ x, q x → label x = i) ∧
      ((∃ x, q x) ↔ r i true) ∧
      ((∃ x, label x = i ∧ ¬ q x) ↔ r i false) := by
  classical
  by_cases ht : r i true
  · by_cases hf : r i false
    · obtain ⟨q, hqm, hsub, hpos, hneg⟩ :=
        A.split hm ((legal i).mpr (Or.inr ht))
      exact ⟨q, hqm, hsub, ⟨fun _ => ht, fun _ => hpos⟩,
        ⟨fun _ => hf, fun _ => hneg⟩⟩
    · refine ⟨(fun x => label x = i), hm, (fun _ h => h), ?_, ?_⟩
      · exact ⟨fun _ => ht, fun _ => (legal i).mpr (Or.inr ht)⟩
      · simp [hf]
  · refine ⟨(fun _ => False), A.empty_mem, (fun _ h => h.elim), ?_, ?_⟩
    · simp [ht]
    · simp only [not_false_eq_true, and_true]
      constructor
      · intro h
        exact ((legal i).mp h).resolve_right ht
      · intro hf
        exact (legal i).mpr (Or.inl hf)

/-- Every legal finite support refinement is realized by one carrier element.
This proves finite gluing from individual atomless splits, rather than
assuming a refinement-completeness law. -/
theorem realize_refinement {X I : Type} (A : AtomlessField X)
    (is : List I) (complete : ∀ i, i ∈ is)
    (label : X → I) (hm : ∀ i, A.member (fun x => label x = i))
    (r : I → Bool → Prop) (legal : Legal label r) :
    ∃ q, A.member q ∧ ∀ i b, childSupport label q i b ↔ r i b := by
  classical
  have hex := fun i => realize_one_cell A label i (hm i) r legal
  let p : I → X → Prop := fun i => Classical.choose (hex i)
  have pm : ∀ i, A.member (p i) := fun i => (Classical.choose_spec (hex i)).1
  have sub : ∀ i x, p i x → label x = i :=
    fun i => (Classical.choose_spec (hex i)).2.1
  have pos : ∀ i, (∃ x, p i x) ↔ r i true :=
    fun i => (Classical.choose_spec (hex i)).2.2.1
  have neg : ∀ i, (∃ x, label x = i ∧ ¬ p i x) ↔ r i false :=
    fun i => (Classical.choose_spec (hex i)).2.2.2
  let q : X → Prop := fun x => ∃ i, i ∈ is ∧ p i x
  have hq : A.member q := finite_union_member A is p pm
  have local_q : ∀ i x, label x = i → (q x ↔ p i x) := by
    intro i x hxi
    constructor
    · rintro ⟨j, _, hpj⟩
      have hji : j = i := (sub j x hpj).symm.trans hxi
      simpa only [hji] using hpj
    · intro hpi
      exact ⟨i, complete i, hpi⟩
  refine ⟨q, hq, ?_⟩
  intro i b
  cases b with
  | false =>
    change (∃ x, label x = i ∧ ¬ q x) ↔ r i false
    rw [← neg i]
    constructor
    · rintro ⟨x, hx, hqx⟩
      exact ⟨x, hx, fun hpx => hqx ((local_q i x hx).mpr hpx)⟩
    · rintro ⟨x, hx, hpx⟩
      exact ⟨x, hx, fun hqx => hpx ((local_q i x hx).mp hqx)⟩
  | true =>
    change (∃ x, label x = i ∧ q x) ↔ r i true
    rw [← pos i]
    constructor
    · rintro ⟨x, hx, hqx⟩
      exact ⟨x, (local_q i x hx).mp hqx⟩
    · rintro ⟨x, hpx⟩
      have hx := sub i x hpx
      exact ⟨x, hx, (local_q i x hx).mpr hpx⟩

abbrev Val (n : Nat) := Fin n → Bool
abbrev Env (X : Type) (n : Nat) := Fin n → X → Prop

def extend {Y : Type} {n : Nat} (head : Y) (tail : Fin n → Y) :
    Fin (n + 1) → Y := Fin.cases head tail

theorem extend_eta {Y : Type} {n : Nat} (v : Fin (n + 1) → Y) :
    extend (v 0) (fun i => v i.succ) = v := by
  funext i
  exact Fin.cases rfl (fun _ => rfl) i

def allVal : (n : Nat) → List (Val n)
  | 0 => [fun i => Fin.elim0 i]
  | n + 1 => (allVal n).flatMap fun v => [extend false v, extend true v]

theorem allVal_complete (n : Nat) (v : Val n) : v ∈ allVal n := by
  induction n with
  | zero =>
    have h : v = (fun i => Fin.elim0 i) := funext (fun i => Fin.elim0 i)
    simp [allVal, h]
  | succ n ih =>
    apply List.mem_flatMap.mpr
    refine ⟨(fun i => v i.succ), ih _, ?_⟩
    have he := extend_eta v
    cases hb : v 0 <;> simp_all

noncomputable def label {X : Type} {n : Nat} (e : Env X n) (x : X) : Val n :=
  fun i => @decide (e i x) (Classical.propDecidable _)

theorem cell_member {X : Type} (A : AtomlessField X) (n : Nat)
    (e : Env X n) (he : ∀ i, A.member (e i)) (v : Val n) :
    A.member (fun x => label e x = v) := by
  induction n with
  | zero =>
    have hc : (fun x => label e x = v) = (fun _ => True) := by
      funext x
      apply propext
      simp only [funext_iff]
      exact ⟨fun _ => True.intro, fun _ i => Fin.elim0 i⟩
    rw [hc]
    exact A.full_mem
  | succ n ih =>
    let tail : Env X n := fun i => e i.succ
    let tv : Val n := fun i => v i.succ
    have ht := ih tail (fun i => he i.succ) tv
    have hc : (fun x => label e x = v) =
        (fun x => (if v 0 then e 0 x else ¬ e 0 x) ∧ label tail x = tv) := by
      funext x
      apply propext
      simp only [funext_iff, Fin.forall_fin_succ]
      cases hb : v 0 <;> simp [label, tail, tv]
    rw [hc]
    cases hb : v 0
    · simpa only [hb, Bool.false_eq_true, ↓reduceIte] using A.inter_mem (A.compl_mem (he 0)) ht
    · simpa only [hb, ↓reduceIte] using A.inter_mem (he 0) ht

inductive Term (n : Nat) where
  | var : Fin n → Term n
  | zero : Term n
  | one : Term n
  | neg : Term n → Term n
  | meet : Term n → Term n → Term n
  | join : Term n → Term n → Term n
  deriving Repr

def Term.bits {n : Nat} (v : Val n) : Term n → Bool
  | .var i => v i
  | .zero => false
  | .one => true
  | .neg a => !a.bits v
  | .meet a b => a.bits v && b.bits v
  | .join a b => a.bits v || b.bits v

def Term.sets {X : Type} {n : Nat} (e : Env X n) : Term n → X → Prop
  | .var i => e i
  | .zero => fun _ => False
  | .one => fun _ => True
  | .neg a => fun x => ¬a.sets e x
  | .meet a b => fun x => a.sets e x ∧ b.sets e x
  | .join a b => fun x => a.sets e x ∨ b.sets e x

theorem term_pointwise {X : Type} {n : Nat} (e : Env X n)
    (t : Term n) (x : X) : t.sets e x ↔ t.bits (label e x) = true := by
  induction t with
  | var i => simp [Term.sets, Term.bits, label]
  | zero => simp [Term.sets, Term.bits]
  | one => simp [Term.sets, Term.bits]
  | neg a ih => simpa [Term.sets, Term.bits] using not_congr ih
  | meet a b ia ib => simp [Term.sets, Term.bits, ia, ib]
  | join a b ia ib => simp [Term.sets, Term.bits, ia, ib]

theorem term_eq_support {X : Type} {n : Nat} (e : Env X n)
    (a b : Term n) :
    a.sets e = b.sets e ↔
      ∀ v, support (label e) v → a.bits v = b.bits v := by
  constructor
  · intro h v ⟨x, hx⟩
    rw [← hx, Bool.eq_iff_iff, ← term_pointwise, ← term_pointwise, h]
  · intro h
    funext x
    apply propext
    rw [term_pointwise, term_pointwise, h (label e x) ⟨x, rfl⟩]

inductive Formula : Nat → Type where
  | eq {n} : Term n → Term n → Formula n
  | neg {n} : Formula n → Formula n
  | conj {n} : Formula n → Formula n → Formula n
  | disj {n} : Formula n → Formula n → Formula n
  | ex {n} : Formula (n + 1) → Formula n
  | all {n} : Formula (n + 1) → Formula n
  deriving Repr

def Formula.setSat {X : Type} (A : AtomlessField X) :
    {n : Nat} → Env X n → Formula n → Prop
  | _, e, .eq a b => a.sets e = b.sets e
  | _, e, .neg f => ¬f.setSat A e
  | _, e, .conj f g => f.setSat A e ∧ g.setSat A e
  | _, e, .disj f g => f.setSat A e ∨ g.setSat A e
  | _, e, .ex f => ∃ q, A.member q ∧ f.setSat A (extend q e)
  | _, e, .all f => ∀ q, A.member q → f.setSat A (extend q e)

def Refines {n : Nat} (s : Val n → Prop) (r : Val (n + 1) → Prop) : Prop :=
  ∀ v, s v ↔ r (extend false v) ∨ r (extend true v)

def Formula.supportSat : {n : Nat} → (Val n → Prop) → Formula n → Prop
  | _, s, .eq a b => ∀ v, s v → a.bits v = b.bits v
  | _, s, .neg f => ¬f.supportSat s
  | _, s, .conj f g => f.supportSat s ∧ g.supportSat s
  | _, s, .disj f g => f.supportSat s ∨ g.supportSat s
  | _, s, .ex f => ∃ r, Refines s r ∧ f.supportSat r
  | _, s, .all f => ∀ r, Refines s r → f.supportSat r

theorem support_extend {X : Type} {n : Nat} (e : Env X n)
    (q : X → Prop) (v : Val n) (b : Bool) :
    support (label (extend q e)) (extend b v) ↔ childSupport (label e) q v b := by
  simp only [support, childSupport, funext_iff, Fin.forall_fin_succ]
  cases b <;> simp [label, extend, and_comm] <;> rfl

theorem actual_refines {X : Type} {n : Nat} (e : Env X n) (q : X → Prop) :
    Refines (support (label e)) (support (label (extend q e))) := by
  intro v
  rw [support_extend, support_extend]
  exact child_support_legal (label e) q v

theorem support_refinement_exists {X : Type} {n : Nat} (A : AtomlessField X)
    (e : Env X n) (he : ∀ i, A.member (e i)) (r : Val (n + 1) → Prop)
    (hr : Refines (support (label e)) r) :
    ∃ q, A.member q ∧ support (label (extend q e)) = r := by
  have hlegal : Legal (label e) (fun v b => r (extend b v)) := hr
  obtain ⟨q, hq, hh⟩ := realize_refinement A (allVal n) (allVal_complete n)
    (label e) (cell_member A n e he) (fun v b => r (extend b v)) hlegal
  refine ⟨q, hq, ?_⟩
  funext w
  apply propext
  have hw := extend_eta w
  rw [← hw, support_extend]
  exact hh _ _

/-- Exactness for every well-scoped first-order formula over the set algebra.
Both quantifiers range over every member of the algebra, not a finite sample. -/
theorem formula_support_exact {X : Type} (A : AtomlessField X)
    {n : Nat} (f : Formula n) (e : Env X n) (he : ∀ i, A.member (e i)) :
    f.setSat A e ↔ f.supportSat (support (label e)) := by
  induction f with
  | eq a b => exact term_eq_support e a b
  | neg f ih => exact not_congr (ih e he)
  | conj f g ihf ihg => exact and_congr (ihf e he) (ihg e he)
  | disj f g ihf ihg => exact or_congr (ihf e he) (ihg e he)
  | @ex n f ih =>
    constructor
    · rintro ⟨q, hq, hf⟩
      exact ⟨support (label (extend q e)), actual_refines e q,
        (ih (extend q e) (Fin.cases hq he)).mp hf⟩
    · rintro ⟨r, hr, hf⟩
      obtain ⟨q, hq, hqr⟩ := support_refinement_exists A e he r hr
      refine ⟨q, hq, (ih (extend q e) (Fin.cases hq he)).mpr ?_⟩
      rwa [hqr]
  | @all n f ih =>
    constructor
    · intro hf r hr
      obtain ⟨q, hq, hqr⟩ := support_refinement_exists A e he r hr
      have hh := (ih (extend q e) (Fin.cases hq he)).mp (hf q hq)
      rwa [hqr] at hh
    · intro hf q hq
      exact (ih (extend q e) (Fin.cases hq he)).mpr
        (hf _ (actual_refines e q))

def valDecEq : (n : Nat) → DecidableEq (Val n)
  | 0 => fun _ _ => isTrue (funext fun i => Fin.elim0 i)
  | n + 1 => fun a b =>
    match (inferInstance : Decidable (a 0 = b 0)),
        valDecEq n (fun i => a i.succ) (fun i => b i.succ) with
    | isTrue hh, isTrue ht => isTrue (by
        rw [← extend_eta a, ← extend_eta b, hh, ht])
    | isFalse hh, _ => isFalse (fun h => hh (congrFun h 0))
    | _, isFalse ht => isFalse (fun h => ht (funext fun i => congrFun h i.succ))

instance {n : Nat} : DecidableEq (Val n) := valDecEq n

def enumFunctions {I : Type} [DecidableEq I] : List I → List (I → Bool)
  | [] => [fun _ => false]
  | a :: xs => (enumFunctions xs).flatMap fun f =>
    [(fun i => if i = a then false else f i),
     (fun i => if i = a then true else f i)]

theorem enumFunctions_covers {I : Type} [DecidableEq I]
    (xs : List I) (g : I → Bool) :
    ∃ f, f ∈ enumFunctions xs ∧ ∀ i, i ∈ xs → f i = g i := by
  induction xs with
  | nil => exact ⟨(fun _ => false), by simp [enumFunctions], by simp⟩
  | cons a xs ih =>
    obtain ⟨f, hf, hh⟩ := ih
    refine ⟨(fun i => if i = a then g a else f i), ?_, ?_⟩
    · apply List.mem_flatMap.mpr
      refine ⟨f, hf, ?_⟩
      cases hg : g a <;> simp
    · intro i hi
      by_cases hia : i = a
      · simp [hia]
      · have him : i ∈ xs := (List.mem_cons.mp hi).resolve_left hia
        simp [hia, hh i him]

def allSupport (n : Nat) : List (Val n → Bool) := enumFunctions (allVal n)

theorem allSupport_complete (n : Nat) (s : Val n → Bool) :
    s ∈ allSupport n := by
  obtain ⟨f, hf, hh⟩ := enumFunctions_covers (allVal n) s
  have hfs : f = s := funext fun i => hh i (allVal_complete n i)
  simpa only [hfs] using hf

def refinesB {n : Nat} (s : Val n → Bool) (r : Val (n + 1) → Bool) : Bool :=
  (allVal n).all fun v => s v == (r (extend false v) || r (extend true v))

theorem refinesB_exact {n : Nat} (s : Val n → Bool) (r : Val (n + 1) → Bool) :
    refinesB s r = true ↔ Refines (fun v => s v = true) (fun v => r v = true) := by
  simp only [refinesB, List.all_eq_true, beq_iff_eq, Refines]
  constructor
  · intro h v
    rw [h v (allVal_complete n v)]
    simp
  · intro h v _
    apply Bool.eq_iff_iff.mpr
    simpa using h v

def Formula.eval : {n : Nat} → (Val n → Bool) → Formula n → Bool
  | n, s, .eq a b => (allVal n).all fun v => !s v || (a.bits v == b.bits v)
  | _, s, .neg f => !f.eval s
  | _, s, .conj f g => f.eval s && g.eval s
  | _, s, .disj f g => f.eval s || g.eval s
  | n, s, .ex f => (allSupport (n + 1)).any fun r => refinesB s r && f.eval r
  | n, s, .all f => (allSupport (n + 1)).all fun r => !refinesB s r || f.eval r

theorem bool_predicate {I : Type} (p : I → Prop) :
    ∃ b : I → Bool, (fun i => b i = true) = p := by
  classical
  exact ⟨(fun i => decide (p i)), funext (fun i => propext (by simp))⟩

/-- The finite executable evaluator implements the mathematical support semantics.
This enumerates all child supports then filters legal ones; it makes no claim
about the complexity of a separate optimized ternary enumeration. -/
theorem executable_support_exact {n : Nat} (f : Formula n) (s : Val n → Bool) :
    f.eval s = true ↔ f.supportSat (fun v => s v = true) := by
  induction f with
  | eq a b =>
    simp only [Formula.eval, List.all_eq_true, Bool.or_eq_true,
      Bool.not_eq_true', beq_iff_eq, Formula.supportSat]
    constructor
    · intro h v hs
      exact (h v (allVal_complete _ v)).resolve_left (by simp [hs])
    · intro h v _
      cases hs : s v
      · exact Or.inl rfl
      · exact Or.inr (h v hs)
  | neg f ih =>
    simpa only [Formula.eval, Formula.supportSat, Bool.not_eq_true',
      Bool.eq_false_iff] using not_congr (ih s)
  | conj f g ihf ihg =>
    simpa only [Formula.eval, Formula.supportSat, Bool.and_eq_true] using
      and_congr (ihf s) (ihg s)
  | disj f g ihf ihg =>
    simpa only [Formula.eval, Formula.supportSat, Bool.or_eq_true] using
      or_congr (ihf s) (ihg s)
  | @ex n f ih =>
    simp only [Formula.eval, List.any_eq_true, Bool.and_eq_true, Formula.supportSat]
    constructor
    · rintro ⟨r, _, hr, hf⟩
      exact ⟨(fun v => r v = true), (refinesB_exact s r).mp hr, (ih r).mp hf⟩
    · rintro ⟨r, hr, hf⟩
      obtain ⟨b, hb⟩ := bool_predicate r
      refine ⟨b, allSupport_complete _ b, ?_, ?_⟩
      · apply (refinesB_exact s b).mpr
        rwa [hb]
      · apply (ih b).mpr
        rwa [hb]
  | @all n f ih =>
    simp only [Formula.eval, List.all_eq_true, Bool.or_eq_true,
      Bool.not_eq_true', Formula.supportSat]
    constructor
    · intro h r hr
      obtain ⟨b, hb⟩ := bool_predicate r
      have hrb : refinesB s b = true := (refinesB_exact s b).mpr (by rwa [hb])
      have hf := (h b (allSupport_complete _ b)).resolve_left (by simp [hrb])
      have hf' := (ih b).mp hf
      rwa [hb] at hf'
    · intro h r _
      cases hr : refinesB s r
      · exact Or.inl rfl
      · exact Or.inr ((ih r).mpr (h _ ((refinesB_exact s r).mp hr)))

theorem formula_evaluator_exact {X : Type} (A : AtomlessField X)
    {n : Nat} (f : Formula n) (e : Env X n) (he : ∀ i, A.member (e i))
    (s : Val n → Bool) (hs : ∀ v, s v = true ↔ support (label e) v) :
    f.eval s = true ↔ f.setSat A e := by
  have hp : (fun v => s v = true) = support (label e) :=
    funext fun v => propext (hs v)
  rw [executable_support_exact, hp]
  exact (formula_support_exact A f e he).symm

theorem term_signature_transfer {X : Type} {n : Nat} (a b : Term n)
    (same : ∀ v, a.bits v = b.bits v) (e : Env X n) : a.sets e = b.sets e :=
  (term_eq_support e a b).mpr (fun v _ => same v)

theorem support_nonempty {X : Type} [Nonempty X] {n : Nat} (e : Env X n) :
    ∃ v, support (label e) v := by
  obtain ⟨x⟩ := (inferInstance : Nonempty X)
  exact ⟨label e x, x, rfl⟩

/-- Every nonempty support is realized, so a support counterexample is genuine
in every nontrivial atomless set algebra, not merely an over-approximation. -/
theorem all_nonempty_supports_realizable {X : Type} [Nonempty X]
    (A : AtomlessField X) (n : Nat) (s : Val n → Prop) (nonzero : ∃ v, s v) :
    ∃ e : Env X n, (∀ i, A.member (e i)) ∧ support (label e) = s := by
  induction n with
  | zero =>
    let e : Env X 0 := fun i => Fin.elim0 i
    refine ⟨e, (fun i => Fin.elim0 i), ?_⟩
    funext v
    apply propext
    constructor
    · intro _
      obtain ⟨w, hw⟩ := nonzero
      have h : w = v := funext (fun i => Fin.elim0 i)
      rwa [h] at hw
    · intro _
      obtain ⟨x⟩ := (inferInstance : Nonempty X)
      exact ⟨x, funext (fun i => Fin.elim0 i)⟩
  | succ n ih =>
    let parent : Val n → Prop := fun v => s (extend false v) ∨ s (extend true v)
    have hp : ∃ v, parent v := by
      obtain ⟨w, hw⟩ := nonzero
      refine ⟨(fun i => w i.succ), ?_⟩
      have h : s (extend (w 0) (fun i => w i.succ)) := by rwa [extend_eta]
      cases hb : w 0
      · exact Or.inl (by simpa only [hb] using h)
      · exact Or.inr (by simpa only [hb] using h)
    obtain ⟨e, he, hes⟩ := ih parent hp
    have hr : Refines (support (label e)) s := by
      rw [hes]
      intro v
      exact Iff.rfl
    obtain ⟨q, hq, hqs⟩ := support_refinement_exists A e he s hr
    exact ⟨extend q e, Fin.cases hq he, hqs⟩

theorem all_support_equivalence_iff {X : Type} [Nonempty X] (A : AtomlessField X)
    {n : Nat} (f g : Formula n) :
    (∀ s : Val n → Bool, (∃ v, s v = true) → f.eval s = g.eval s) ↔
      (∀ e : Env X n, (∀ i, A.member (e i)) → (f.setSat A e ↔ g.setSat A e)) := by
  constructor
  · intro h e he
    obtain ⟨s, hs⟩ := bool_predicate (support (label e))
    have hp : ∀ v, s v = true ↔ support (label e) v := by
      intro v
      exact Iff.of_eq (congrFun hs v)
    have hn : ∃ v, s v = true := by
      obtain ⟨v, hv⟩ := support_nonempty e
      exact ⟨v, (hp v).mpr hv⟩
    rw [← formula_evaluator_exact A f e he s hp,
      ← formula_evaluator_exact A g e he s hp, h s hn]
  · intro h s hn
    obtain ⟨e, he, hes⟩ := all_nonempty_supports_realizable A n
      (fun v => s v = true) hn
    have hp : ∀ v, s v = true ↔ support (label e) v := by
      intro v
      exact (Iff.of_eq (congrFun hes v)).symm
    apply Bool.eq_iff_iff.mpr
    rw [formula_evaluator_exact A f e he s hp,
      formula_evaluator_exact A g e he s hp]
    exact h e he

def nonemptyB {n : Nat} (s : Val n → Bool) : Bool := (allVal n).any s

def compare {n : Nat} (f g : Formula n) : Bool :=
  (allSupport n).all fun s => !nonemptyB s || (f.eval s == g.eval s)

theorem nonemptyB_exact {n : Nat} (s : Val n → Bool) :
    nonemptyB s = true ↔ ∃ v, s v = true := by
  simp only [nonemptyB, List.any_eq_true]
  exact ⟨fun ⟨v, _, hv⟩ => ⟨v, hv⟩,
    fun ⟨v, hv⟩ => ⟨v, allVal_complete n v, hv⟩⟩

/-- Complete equivalence decision for the proved set-algebra fragment.
The quantifiers on the right range over all parameter assignments in A. -/
theorem compare_exact {X : Type} [Nonempty X] (A : AtomlessField X)
    {n : Nat} (f g : Formula n) : compare f g = true ↔
      ∀ e : Env X n, (∀ i, A.member (e i)) → (f.setSat A e ↔ g.setSat A e) := by
  rw [← all_support_equivalence_iff A f g]
  simp only [compare, List.all_eq_true, Bool.or_eq_true, Bool.not_eq_true', beq_iff_eq]
  constructor
  · intro h s hs
    have hn : nonemptyB s = true := (nonemptyB_exact s).mpr hs
    exact (h s (allSupport_complete n s)).resolve_left (by simp [hn])
  · intro h s _
    cases hn : nonemptyB s
    · exact Or.inl rfl
    · exact Or.inr (h s ((nonemptyB_exact s).mp hn))

theorem proper_element_exists {X : Type} [Nonempty X] (A : AtomlessField X) :
    ∃ q, A.member q ∧ q ≠ (fun _ => False) ∧ q ≠ (fun _ => True) := by
  obtain ⟨x⟩ := (inferInstance : Nonempty X)
  obtain ⟨q, hq, _, ⟨y, hy⟩, ⟨z, _, hz⟩⟩ :=
    A.split A.full_mem (⟨x, True.intro⟩ : ∃ _ : X, True)
  refine ⟨q, hq, ?_, ?_⟩
  · intro h
    simp only [h] at hy
  · intro h
    exact hz (by simp only [h])

def endpoint : Formula 1 := .disj (.eq (.var 0) .zero) (.eq (.neg (.var 0)) .zero)
def properClosed : Formula 0 := .ex (.conj
  (.neg (.eq (.var 0) .zero)) (.neg (.eq (.var 0) .one)))

/-- A full two-cell support is not a two-valued BA-variable assignment. -/
theorem endpoint_full_support_false : endpoint.eval (fun _ => true) = false := by decide

theorem proper_closed_true : properClosed.eval (fun _ => true) = true := by decide

theorem finite_two_element_boundary (x : Bool) : x = false ∨ x = true := by
  cases x <;> simp

theorem endpoint_not_equivalent_true :
    compare endpoint (.eq .zero .zero) = false := by decide

theorem one_way_not_equivalence :
    compare (.eq (.var 0) (.zero : Term 1)) (.eq .zero .zero) = false := by decide

#print axioms realize_refinement
#print axioms term_eq_support
#print axioms cell_member
#print axioms formula_support_exact
#print axioms executable_support_exact
#print axioms formula_evaluator_exact
#print axioms term_signature_transfer
#print axioms all_nonempty_supports_realizable
#print axioms compare_exact
#print axioms proper_element_exists
#print axioms endpoint_full_support_false
#print axioms proper_closed_true
#print axioms finite_two_element_boundary
#print axioms endpoint_not_equivalent_true
#print axioms one_way_not_equivalence

end SupportCells
