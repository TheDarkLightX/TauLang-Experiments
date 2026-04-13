# License and Use Boundary

This repository is an independent research repository. It should not contain Tau Language source code, Tau Language binaries, or vendored copies of IDNI components.

## Conservative Rule

Use this repo for:

- original notes and tutorials
- original Tau example programs
- Lean proof artifacts
- benchmark harnesses
- scripts that clone Tau from the official source
- minimal patch files for reproducible research

Do not use this repo for:

- redistributing Tau Language source code
- redistributing Tau Language binaries
- publishing a modified Tau fork without explicit permission
- claiming this repo changes Tau's license

## Why

The Tau Language license grants free use for several cases, including educational use, research purposes, and non-commercial use. It also states that the permitted instances do not include redistribution of the Product or portions of it.

Therefore this repo should point users to the official Tau Language repository:

```text
https://github.com/IDNI/tau-lang
```

and apply patches locally after the user obtains Tau under IDNI's license.

## Safer Public Workflow

```text
official Tau checkout
  + patch files from this repo
  + independent proofs and benchmark harnesses
  = reproducible research without redistributing Tau
```

For substantial Tau changes, prefer an upstream pull request or written permission from IDNI.
