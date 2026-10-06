from pathlib import Path
import subprocess, shlex, os, json, argparse
root=Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('--source',default='direct-memoryless.cpp');ap.add_argument('--tree',type=Path,required=True);ap.add_argument('--tag',required=True);ap.add_argument('--single-step',action='store_true');args=ap.parse_args()
c=args.tree.resolve()
f=c/'build/release/tests/integration/CMakeFiles/test_integration-satisfiability6.dir'
flags={k.strip():shlex.split(v.strip().replace('\\#','#')) for line in (f/'flags.make').read_text().splitlines() if ' = ' in line for k,v in [line.split(' = ',1)]}
link=shlex.split((f/'link.txt').read_text());cc=link[0]
obj=root/('direct-'+args.tag+'.o');exe=root/('direct-'+args.tag)
compile=[cc, *(['-DHAS_SINGLE_STEP'] if args.single_step else []),*flags['CXX_DEFINES'],*flags['CXX_INCLUDES'],*flags['CXX_FLAGS'],'-c',str(root/args.source),'-o',str(obj)]
for i,x in enumerate(link):
 if x.endswith('test_integration-satisfiability6.cpp.o'):link[i]=str(obj)
 if x=='../../test_integration-satisfiability6':link[i]=str(exe)
(root/('direct-'+args.tag+'-commands.json')).write_text(json.dumps([compile,link],indent=2)+'\n')
env=os.environ.copy();env['SDKROOT']='/Library/Developer/CommandLineTools/SDKs/MacOSX.sdk'
subprocess.run(compile,check=True,cwd=c,env=env)
subprocess.run(link,check=True,cwd=c/'build/release/tests/integration',env=env)
