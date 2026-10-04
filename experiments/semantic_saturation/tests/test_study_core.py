import unittest
import engine as E
from study_core import optimize,emitted_cost
from typed_parser import parse_emitted,TypedParseError
from native_oracle import typed_render
from generate_corpus import make
from checked_registry import recursive_quotient,validate_context,signature
class ExpandedCoreTests(unittest.TestCase):
 def test_recursive_all_class_members(self):
  ctx=E.Context((('a','tau'),('b','tau')),V=('a','b'));a,b=('var','a'),('var','b')
  z=('or',a,('zero',));root=('and',('not',('not',a)),b);alt=('and',z,b)
  pairs=[E.CheckedPair(root,alt,ctx.key),E.CheckedPair(z,a,ctx.key)]
  x,_=recursive_quotient(root,ctx,pairs);y,_=optimize(root,ctx,pairs,rewrites=False)
  self.assertEqual(x,('and',a,b));self.assertEqual(emitted_cost(x,ctx),emitted_cost(y,ctx))
 def test_roundtrip_development(self):
  for c in make('dev'):
   ctx=E.Context(tuple((x,'tau') for x in c.free),V=c.free)
   self.assertEqual(c.original,parse_emitted(typed_render(c.original,ctx),c.free))
 def test_typed_parser_fails_closed(self):
  for text in ['a','(a : sbf)','(a : tau);','(a : tau) T','ex a : tau ((a : tau))','((a : tau) = 1)']:
   with self.subTest(text=text):
    with self.assertRaises(TypedParseError):parse_emitted(text,('a',))
 def test_context_boundaries(self):
  for kw in [{'T':'trivial'},{'temporal':'one-step'},{'K':('0','1','c')},{'V':('a','a')}]:
   args={'terms':(('a','tau'),),'V':('a',)};args.update(kw)
   with self.assertRaises(ValueError):validate_context(E.Context(**args))
 def test_pure_term_eight_variable_signature(self):
  ctx=E.Context(tuple((x,'tau') for x in 'abcdefgh'),V=tuple('abcdefgh'))
  sig,r=signature(('var','a'),ctx);self.assertEqual(len(sig[1]),256)
if __name__=='__main__':unittest.main()
