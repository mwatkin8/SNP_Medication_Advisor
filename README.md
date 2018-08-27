## SNP Medication Advisor

This is a clinico-genomic SMART on FHIR app which uses patient-specific genetic variants (SNPs) to assist care providers in selecting optimal medication regimens. 

![DNA to Meds](/images/SMA.png)

Built using Python and Flask web services, this app provides several unique services:
* SMART-standard web authentication.
* Conversion from VCF to appropriate FHIR resources to represent, store, and access variants in the EHR.
* VMC Allele Identifier generated and added for each variant's Observation resource.
* SNP-specific clinical annotations pulled from PharmGKB and stored in the Observation resources used to represent each variant.
* Formatting and visualization to simplify an otherwise complicated collection of recommendations.
