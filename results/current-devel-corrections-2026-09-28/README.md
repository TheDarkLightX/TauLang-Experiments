# Current-devel printing, documentation and macOS build checks

Tau `8b5a61ca98a72f0a2cbece9b1338c7295482bbd3`, parser `5b14b6fde86f16dc52c4c0a953a8a1e53c88f95a`.

[Download the reproduction package](current-devel-reproduction.zip) or read the [build and replay instructions](reproduction/README.md).

The reference build contains an identifier-only rename needed to compile on macOS. The corrected build adds the multi-character conjunction printing correction and search-limit documentation correction. The original unmodified compiler failure is retained. No BDD or arithmetic-elimination patch is included.

The corrected build passes nine printing examples, 48 independent Boolean assignments, four controls and 30 API regression assertions. The configured Release suite passes **2,532/2,533** tests. The remaining constant-size-budget test also fails with the reference binary, with exactly the same nine output values followed by the limit diagnostic. This is not an all-passing suite result. The earlier all-passing report remains a separate historical result for its earlier source revision.

The package also retains two file-input timing observations. These support a contract question, not a claim that the existing interpretation is wrong.

Archive SHA-256: `3413eeaa1a8a4cc4b11e5638c7e61ffe6df974bcae5f8d36bd2372d5a40c13b0`.
