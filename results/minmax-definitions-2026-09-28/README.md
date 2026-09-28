# Min/max definition and fallback checks — 28 September 2026

Two additional grammar exclusions preserve built-in min/max calls in definition bodies and explicit fallback values. The comparison retains the earlier operand correction and changes only these two grammar alternatives.

[Build, replay, scope and remaining failures](reproduction/README.md). [Download the reproduction ZIP](minmax-definitions-reproduction.zip).

Archive SHA-256: `817487d9774017b0cf434ddf445cfb96e5abbd96194f1652802bc62f2eb913d8`.

The corrected combination passes 272 API assertions, 10 earlier focused checks, 2,352 exact small-width checks, and 72/128 new definition/fallback checks. The other 56 retain a type diagnostic and are failures, even though their printed Boolean values are correct. Parenthesized controls match those observations exactly.

The configured Release suite passes 2,542/2,543 tests; the existing constant-size-budget failure remains. Source and binary identities, raw observations, complete and separate patches, and a verifier that recomputes acceptance are included. These results make no global correctness or performance claim.
