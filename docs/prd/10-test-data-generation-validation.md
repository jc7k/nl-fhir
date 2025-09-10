# 10. Test Data Generation & Validation

-   Use **Synthea** synthetic FHIR bundles as ground truth.\
-   Generate natural-language encounter text with ChatGPT based on those
    bundles (20--30 seed examples).\
-   Scale with templates, paraphrasing, abbreviations, negations (\~200
    examples).\
-   Round-trip validation: text → bundle → summary → compare with
    original.

------------------------------------------------------------------------
