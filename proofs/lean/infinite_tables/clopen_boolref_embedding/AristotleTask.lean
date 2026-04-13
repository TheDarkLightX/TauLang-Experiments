/-!
# Aristotle packet A/B/C: Clopen embedding into completed reference semantics

This is a self-contained proof packet for the infinite TABA table semantics
stack.

`Clopen` is the finite executable lane. `BoolRef` is the completed reference
carrier, represented extensionally as stream predicates. The packet proves the
finite lane embeds into the completed carrier and preserves Boolean operations.
It also proves that the completed carrier can express `EventuallyOne`, while
finite clopens cannot.

Fill the sorries without weakening statements. Do not add axioms, unsafe
definitions, new assumptions, or theorem-statement changes.
-/

set_option autoImplicit false

namespace AristotleClopenBoolRef

def Stream := Nat -> Bool
def BoolRef := Stream -> Prop

def RefEq (X Y : BoolRef) : Prop :=
  forall s : Stream, X s <-> Y s

def emptyRef : BoolRef := fun _ => False
def fullRef : BoolRef := fun _ => True
def interRef (X Y : BoolRef) : BoolRef := fun s => X s /\ Y s
def unionRef (X Y : BoolRef) : BoolRef := fun s => X s \/ Y s
def complRef (X : BoolRef) : BoolRef := fun s => Not (X s)
def iUnionRef (X : Nat -> BoolRef) : BoolRef := fun s => exists n, X n s

structure Clopen where
  fn : Stream -> Bool
  depth : Nat
  fin_support :
    forall s t, (forall i, i < depth -> s i = t i) -> fn s = fn t

namespace Clopen

def equiv (a b : Clopen) : Prop :=
  forall s : Stream, a.fn s = b.fn s

def bot : Clopen where
  fn := fun _ => false
  depth := 0
  fin_support := by
    intro s t h
    rfl

def top : Clopen where
  fn := fun _ => true
  depth := 0
  fin_support := by
    intro s t h
    rfl

def inf (a b : Clopen) : Clopen where
  fn := fun s => a.fn s && b.fn s
  depth := max a.depth b.depth
  fin_support := by
    intro s t h
    have ha : a.fn s = a.fn t := by
      apply a.fin_support
      intro i hi
      exact h i (Nat.lt_of_lt_of_le hi (Nat.le_max_left a.depth b.depth))
    have hb : b.fn s = b.fn t := by
      apply b.fin_support
      intro i hi
      exact h i (Nat.lt_of_lt_of_le hi (Nat.le_max_right a.depth b.depth))
    simp [ha, hb]

def sup (a b : Clopen) : Clopen where
  fn := fun s => a.fn s || b.fn s
  depth := max a.depth b.depth
  fin_support := by
    intro s t h
    have ha : a.fn s = a.fn t := by
      apply a.fin_support
      intro i hi
      exact h i (Nat.lt_of_lt_of_le hi (Nat.le_max_left a.depth b.depth))
    have hb : b.fn s = b.fn t := by
      apply b.fin_support
      intro i hi
      exact h i (Nat.lt_of_lt_of_le hi (Nat.le_max_right a.depth b.depth))
    simp [ha, hb]

def compl (a : Clopen) : Clopen where
  fn := fun s => not (a.fn s)
  depth := a.depth
  fin_support := by
    intro s t h
    have ha : a.fn s = a.fn t := a.fin_support s t h
    simp [ha]

end Clopen

def embedClopen (c : Clopen) : BoolRef :=
  fun s => c.fn s = true

theorem embed_equiv_iff (a b : Clopen) :
    Clopen.equiv a b <-> RefEq (embedClopen a) (embedClopen b) := by
  constructor
  · intro h s
    constructor
    · intro hs
      unfold embedClopen at hs ⊢
      rw [h s] at hs
      exact hs
    · intro hs
      unfold embedClopen at hs ⊢
      rw [← h s] at hs
      exact hs
  · intro h s
    have hs := h s
    cases ha : a.fn s <;> cases hb : b.fn s <;>
      simp [embedClopen, ha, hb] at hs ⊢

theorem embed_bot :
    RefEq (embedClopen Clopen.bot) emptyRef := by
  intro s
  simp [embedClopen, Clopen.bot, emptyRef]

theorem embed_top :
    RefEq (embedClopen Clopen.top) fullRef := by
  intro s
  simp [embedClopen, Clopen.top, fullRef]

theorem embed_inf (a b : Clopen) :
    RefEq (embedClopen (Clopen.inf a b))
      (interRef (embedClopen a) (embedClopen b)) := by
  intro s
  simp [embedClopen, Clopen.inf, interRef]

theorem embed_sup (a b : Clopen) :
    RefEq (embedClopen (Clopen.sup a b))
      (unionRef (embedClopen a) (embedClopen b)) := by
  intro s
  simp [embedClopen, Clopen.sup, unionRef]

theorem embed_compl (a : Clopen) :
    RefEq (embedClopen (Clopen.compl a))
      (complRef (embedClopen a)) := by
  intro s
  cases h : a.fn s <;> simp [embedClopen, Clopen.compl, complRef, h]

def EventuallyOne (s : Stream) : Prop :=
  exists n : Nat, s n = true

def eventuallyOneRef : BoolRef :=
  fun s => EventuallyOne s

def oneAtCylinder (n : Nat) : BoolRef :=
  fun s => s n = true

theorem eventuallyOne_eq_iUnion_cylinders :
    RefEq eventuallyOneRef (iUnionRef oneAtCylinder) := by
  intro s
  constructor
  · intro h
    exact h
  · intro h
    exact h

def allFalse : Stream :=
  fun _ => false

def oneAt (n : Nat) : Stream :=
  fun i => decide (i = n)

theorem allFalse_not_eventuallyOne :
    Not (EventuallyOne allFalse) := by
  intro h
  rcases h with ⟨n, hn⟩
  cases hn

theorem oneAt_eventuallyOne (n : Nat) :
    EventuallyOne (oneAt n) := by
  exact ⟨n, by simp [oneAt]⟩

theorem allFalse_agrees_with_oneAt_before (n i : Nat) (hi : i < n) :
    allFalse i = oneAt n i := by
  have hne : i ≠ n := Nat.ne_of_lt hi
  simp [allFalse, oneAt, hne]

theorem no_clopen_represents_eventuallyOne :
    Not (exists c : Clopen,
      forall s : Stream, c.fn s = true <-> EventuallyOne s) := by
  intro h
  rcases h with ⟨c, hc⟩
  have hFalse : c.fn allFalse ≠ true := by
    intro ht
    exact allFalse_not_eventuallyOne ((hc allFalse).mp ht)
  have hOneTrue : c.fn (oneAt c.depth) = true := by
    exact (hc (oneAt c.depth)).mpr (oneAt_eventuallyOne c.depth)
  have hAgree :
      forall i, i < c.depth -> allFalse i = oneAt c.depth i := by
    intro i hi
    exact allFalse_agrees_with_oneAt_before c.depth i hi
  have hSame : c.fn allFalse = c.fn (oneAt c.depth) :=
    c.fin_support allFalse (oneAt c.depth) hAgree
  rw [hSame] at hFalse
  exact hFalse hOneTrue

theorem eventuallyOne_not_in_embedClopen_range :
    Not (exists c : Clopen, RefEq (embedClopen c) eventuallyOneRef) := by
  intro h
  rcases h with ⟨c, hc⟩
  apply no_clopen_represents_eventuallyOne
  exact ⟨c, hc⟩

theorem packet_abc_receipt :
    RefEq (embedClopen Clopen.bot) emptyRef
      /\ RefEq (embedClopen Clopen.top) fullRef
      /\ RefEq eventuallyOneRef (iUnionRef oneAtCylinder)
      /\ Not (exists c : Clopen, RefEq (embedClopen c) eventuallyOneRef) := by
  constructor
  · exact embed_bot
  constructor
  · exact embed_top
  constructor
  · exact eventuallyOne_eq_iUnion_cylinders
  · exact eventuallyOne_not_in_embedClopen_range

end AristotleClopenBoolRef
