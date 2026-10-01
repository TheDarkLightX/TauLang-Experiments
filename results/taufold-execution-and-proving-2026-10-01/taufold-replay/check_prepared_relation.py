#!/usr/bin/env python3
"""Compare a prepared checker executable with saved original-source outputs."""
import argparse,hashlib,json,subprocess,tempfile
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('binary',type=Path);p.add_argument('vectors',type=Path);p.add_argument('--output',type=Path,required=True)
a=p.parse_args();data=json.loads(a.vectors.read_text());assert len(data['inputs'])==len(data['outputs'])==1992
with tempfile.TemporaryDirectory(prefix='taufold-relation-') as temp:
    path=Path(temp)/'inputs.json'
    for offset in range(0,len(data['inputs']),100):
        path.write_text(json.dumps(data['inputs'][offset:offset+100]))
        output=subprocess.check_output([str(a.binary.resolve()),'relation',str(path)],text=True)
        assert json.loads(output)==data['outputs'][offset:offset+100]
    for value in [1<<32,1<<64,1<<127]:
        row=data['inputs'][0].copy();row[82]=value
        path.write_text(json.dumps([row]))
        result=subprocess.run([str(a.binary.resolve()),'relation',str(path)],capture_output=True,text=True)
        assert result.returncode!=0,'Out-of-range public input was accepted'
report={'status':'passed','vectors':len(data['inputs']),'out_of_range_rejections':3,
        'binary_sha256':hashlib.sha256(a.binary.read_bytes()).hexdigest(),
        'vectors_sha256':hashlib.sha256(a.vectors.read_bytes()).hexdigest()}
a.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
