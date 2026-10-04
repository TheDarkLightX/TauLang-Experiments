import unittest
from run_study import unique_gate_cold_cost
class AccountingTests(unittest.TestCase):
 def gate(self,n,cold):return {'elapsed_s':.001,'cold_elapsed_s':cold,'native':{'forward':{'binary_sha256':'x','ordinal':n},'reverse':{'binary_sha256':'x','ordinal':n+1}}}
 def test_certificate_cost_deduplicates(self):
  a=self.gate(1,2.);b=self.gate(3,3.)
  self.assertEqual(unique_gate_cold_cost(a,a,b,a),5.)
 def test_inconclusive_computation_is_not_free(self):
  a={'elapsed_s':2.}
  self.assertEqual(unique_gate_cold_cost(a,a),4.)
if __name__=='__main__':unittest.main()
