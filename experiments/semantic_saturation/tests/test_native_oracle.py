import unittest
from native_oracle import exact_truth

class NativeVerdictTests(unittest.TestCase):
    def record(self,**changes):
        r={'timed_out':False,'returncode':0,'stderr':'','stdout':'%1: T\n\n'}
        r.update(changes);return r
    def test_exit_zero_with_error_is_unknown(self):
        self.assertEqual(exact_truth(self.record(stderr='Syntax Error',stdout='\n')),'UNKNOWN')
        self.assertEqual(exact_truth(self.record(stderr='Syntax Error')),'UNKNOWN')
    def test_incomplete_or_extra_transcript_fails_closed(self):
        for s in ['', '%1: T\n%2: F', 'diagnostic\n%1: T']:
            self.assertEqual(exact_truth(self.record(stdout=s)),'UNKNOWN')
    def test_false_timeout_and_nonzero_are_distinct(self):
        self.assertEqual(exact_truth(self.record(stdout='%1: F')),'F')
        self.assertEqual(exact_truth(self.record(timed_out=True)),'UNKNOWN')
        self.assertEqual(exact_truth(self.record(returncode=1)),'UNKNOWN')
    def test_exact_truth_only(self):
        self.assertEqual(exact_truth(self.record()),'T')

if __name__=='__main__':unittest.main()
