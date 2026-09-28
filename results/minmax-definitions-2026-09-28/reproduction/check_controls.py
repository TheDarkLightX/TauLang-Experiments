#!/usr/bin/env python3
"""Record parenthesized counterparts of the definition sat/valid checks."""
import check_definitions as checks
base_cases=checks.cases

def controls():
    result=[]
    for row in base_cases():
        if row['family']!='definition' or '. normalize ' in row['input']:
            continue
        before,after=row['input'].split(' := ',1)
        call,command=after.split('. ',1)
        row['input']=before+' := ('+call+'). '+command
        result.append(row)
    return result

checks.cases=controls
if __name__=='__main__':
    raise SystemExit(checks.main())
