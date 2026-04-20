/-!
# qNS semantic Boolean algebra v001

This packet proves the finite powerset laws used by the qNS Tau demo.
It models a carrier as predicates `Atom -> Bool`. The C++ experiment stores
the same shape as a bit mask, but this file proves the formula-level semantics,
not the C++ parser or bit operations.
-/

namespace QNSSemanticBAV001

abbrev Carrier (Atom : Type) := Atom → Bool

def bot {Atom : Type} : Carrier Atom := fun _ => false
def top {Atom : Type} : Carrier Atom := fun _ => true
def meet {Atom : Type} (a b : Carrier Atom) : Carrier Atom :=
  fun x => a x && b x
def join {Atom : Type} (a b : Carrier Atom) : Carrier Atom :=
  fun x => a x || b x
def prime {Atom : Type} (a : Carrier Atom) : Carrier Atom :=
  fun x => !a x

def proposed {Atom : Type} (u n : Carrier Atom) : Carrier Atom :=
  meet u n

def eligible {Atom : Type}
    (u n allowed hardReject : Carrier Atom) : Carrier Atom :=
  meet (meet (meet u n) allowed) (prime hardReject)

def autoAccept {Atom : Type}
    (u n allowed review hardReject : Carrier Atom) : Carrier Atom :=
  meet (eligible u n allowed hardReject) (prime review)

def humanReview {Atom : Type}
    (u n allowed review hardReject : Carrier Atom) : Carrier Atom :=
  meet (eligible u n allowed hardReject) review

def symbolicReject {Atom : Type}
    (u n allowed hardReject : Carrier Atom) : Carrier Atom :=
  meet (proposed u n) (join (prime allowed) hardReject)

def partition {Atom : Type}
    (u n allowed review hardReject : Carrier Atom) : Carrier Atom :=
  join
    (join
      (autoAccept u n allowed review hardReject)
      (humanReview u n allowed review hardReject))
    (symbolicReject u n allowed hardReject)

def unsafeLeak {Atom : Type}
    (u n allowed review hardReject : Carrier Atom) : Carrier Atom :=
  meet (autoAccept u n allowed review hardReject) hardReject

theorem auto_accept_no_hard_reject {Atom : Type}
    (u n allowed review hardReject : Carrier Atom) :
    unsafeLeak u n allowed review hardReject = bot := by
  funext x
  cases hu : u x <;> cases hn : n x <;> cases ha : allowed x <;>
    cases hr : review x <;> cases hh : hardReject x <;>
    simp [unsafeLeak, autoAccept, eligible, meet, prime, bot, hu, hn, ha, hr, hh]

theorem auto_and_review_disjoint {Atom : Type}
    (u n allowed review hardReject : Carrier Atom) :
    meet
      (autoAccept u n allowed review hardReject)
      (humanReview u n allowed review hardReject) = bot := by
  funext x
  cases hu : u x <;> cases hn : n x <;> cases ha : allowed x <;>
    cases hr : review x <;> cases hh : hardReject x <;>
    simp [autoAccept, humanReview, eligible, meet, prime, bot, hu, hn, ha, hr, hh]

theorem partition_eq_proposed {Atom : Type}
    (u n allowed review hardReject : Carrier Atom) :
    partition u n allowed review hardReject =
      proposed u n := by
  funext x
  cases hu : u x <;> cases hn : n x <;> cases ha : allowed x <;>
    cases hr : review x <;> cases hh : hardReject x <;>
    simp [
      partition,
      autoAccept,
      humanReview,
      symbolicReject,
      eligible,
      proposed,
      meet,
      join,
      prime,
      hu,
      hn,
      ha,
      hr,
      hh,
    ]

end QNSSemanticBAV001
