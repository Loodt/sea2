# Success Pattern: mechanism — South African freight operations and compliance matching-logic specialist

## Strategy
Expert type "South African freight operations and compliance matching-logic specialist" for mechanism question.
Question: Which minimum data fields and hard constraints must a neutral matching layer encode for South African backhaul moves, including hazmat, reefer, dimensional, bonded-status, and cross-border permit requirements?

## When It Works
- Question type: mechanism
- Converged in 2/5 iterations

## Evidence
- Dispatch: D3
- Question: Q004
- Findings produced: 16
- Iterations: 2/5
- Status: answered

## Key Decisions
Q004 is answerable as a bounded hard-constraint schema, not an open-ended descriptive model. [DERIVED: synthesis from F935-F943] The minimum match layer must encode only legally gating shipment, equipment, operator, driver, document, and route fields, with hazmat, reefer, abnormal-dimension, bonded, and cross-border requirements each mapped to explicit reject conditions. [DERIVED: field-family reduction from permit forms and regulatory text] The strongest source-backed gates are UN/hazard-class and DG document state for hazmat, regime-code plus DAT set-point and tolerance for reefer, laden geometry plus permit/route state for abnormal loads, remover-in-bond plus customs declaration and DA187 state for bonded transit, and vehicle-linked permit scope plus route/border-post, roadworthy, and driver-authority state for cross-border moves. [SOURCE: https://www.transport.gov.za/wp-content/uploads/2024/11/POSTER-industry_responsibilities_dg.pdf] [SOURCE: https://beta.acts.co.za/perishable-products-export-control-act-1983/bn709_53__specification_of_car.php] [SOURCE: https://www.transport.gov.za/wp-content/uploads/2023/02/TRH11_AdministrativeGuidelines-1stEdition2010_Final_.pdf] [SOURCE: https://www.sars.gov.za/customs-and-excise/import-export-and-transit/transit/] [SOURCE: https://www.sars.gov.za/da-187-customs-road-freight-manifest-external-form/] [SOURCE: https://cbrta.co.za/uploads/files/CD-GOODS-TEMP-ANNUAL.pdf] [SOURCE: https://www.cbrta.co.za/uploads/files/CROSS-BORDER-ROAD-TRANSPORT-ACT4-OF-1998_2025-08-21-095837_eyzj.pdf]