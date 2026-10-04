"""Mock-only control: wrapper must clear inherited inconclusive native cache."""
from pathlib import Path
import argparse,hashlib,json,sys
p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();sys.path.insert(0,str(a.source));import checked_registry as R,native_oracle as N,engine as E
n=N.NativeOracle.__new__(N.NativeOracle);n.binary_sha256='MOCK-NOT-NATIVE';n.cache={};n.records=[]
def fake_run(command,label):
 truth='UNKNOWN' if len(n.records)<2 else 'T';r={'truth':truth,'command':command,'label':label,'ordinal':len(n.records)+1,'mock_only':True};n.records.append(r);return r
n.run=fake_run;c=R.CheckedOracle.__new__(R.CheckedOracle);c.native=n;c.profile_key='MOCK-PROFILE';c.cache={};c.requests=[];ctx=E.Context((('a','tau'),),V=('a',))
first=c.check(('T',),('T',),ctx,'first');after_first={'inner_cache_entries':len(n.cache),'wrapper_cache_entries':len(c.cache),'mock_calls':len(n.records)};second=c.check(('T',),('T',),ctx,'second');third=c.check(('T',),('T',),ctx,'third')
checks={'first_unknown':first['status']=='UNKNOWN','first_not_cached':after_first['inner_cache_entries']==after_first['wrapper_cache_entries']==0,'second_retries_both':second['status']=='ACCEPTED' and second['native_processes']==2 and not second['cache_hit'],'third_exact_hit':third['status']=='ACCEPTED' and third['cache_hit'] and third['native_processes']==0,'exact_mock_call_count':len(n.records)==4}
r={'status':'PASS' if all(checks.values()) else 'FAIL','checks':checks,'after_first':after_first,'total_mock_calls':len(n.records),'checked_registry_sha256':hashlib.sha256((a.source/'checked_registry.py').read_bytes()).hexdigest(),'scope':'Mock control flow only; no native execution or native semantic evidence.'};a.out.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2));raise SystemExit(r['status']!='PASS')
