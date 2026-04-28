# Final Project: Taste Tuner 2.0
    Explicitly name your original project (from Modules 1-3) and 
    provide a 2-3 sentence summary of its original goals and capabilities.    
  **Background:**
  On week 7 I developed **Taste Tuner**, a music recommendation system, to simulate algorthims used in industry-leading music apps' recommended playlist systems.
  Version 1 pulls song attributes (particularly *Mood, Genre, Energy, Acousticness*) from a .csv file, takes user text input from a list of predefined attributes, and matches the user with the top 5 songs, ranked by how well they meet the user-set criteria.    

---
## Project Summary
**Taste Tuner 2.0**
### Architecture Overview:
    Architecture Overview: A short explanation of your system diagram.

![Initial plan for system diagram](https://mermaid.ink/img/pako:eNptVNtu4jAQ_RXLzxQVUqDkYSVKC-oK2oqLdrWlDyYZEi-OHdkOLS399x3boSyrfSNmzmXOjP1BE5UCjelGqNckZ9qSyWwlCVk-Lw3oF3Jx8Y0s759XdAxSA5mDgMRyJfFwtZKD9DdLQCZ7YlWWCSBMpsRYDTKzOTGCp6BX9MUT3juuQyCAlGSOz3iAKh2jOZDBk1OaQaKKAmTKvNCjTnJATmaVRsmnvc2V9KSOFiHe42A8R2jtx5KjW73jCSDq7q10SlaRV-BZfjJQu0O4tzdRaluVBzKefrU8ZSWZozac9ZtpVubB_Q60wJpAfCQcTz3fgztcKx0arUsOTu5v1SAU_iU7zEdpH8Z5i8MxehoiD8dkwLUIx1BGXFjQJGGWCZWRNc6DZUGzAMuwntW-huPANVgg2UKzZEuGAYU0RsnMNBOzI0KxFDNyQAP2iB0saiPBWOA6nCxZx4ftzYdIPk-U5jIjdzLj0oX345i8SVyagXM-9JQzN70Zk1vswrm-5Ziq4XZPZtikO67rZyGxhSrJA9Fnm2LqzE6JLf9J8O7nE8rgLggmw3LdVFy4HUV3OYaWcxOaqNUQELbrjPfgjaZEcGO9Wzgxoomjar3xE77FPTdbXhqCZXusGN2gjRFAuvb5KyH8zGvR0c1_NMnEDWyCt8xl6kSnYDVPTL2b9RrXxY-jEVY_bjYCoyeLSjrQd7XGPpelHxX72uTzvUWkZxhPaYNmmqc0trqCBi1AF8x90g9Xt6I2hwJ1Y_yZwoZVAtdkJT8Rhlftl1LFEalVleU03jBh8Kvy-rec4Q0qvk7xxcAxDFUlLY277Y4nofEHfaPxRasTNXv9XtS77lxdXkb9y26D7rEsara73ei614_6V52o1e58Nui7F241u1GnE0XdfrvbciUNCinHoKbhtfOP3ucflGSjBg?type=png)
[Intial decision system diagram Mermaid.live](https://mermaid.ink/img/pako:eNp1VPFv2joQ_ldOlja1Gi0wKG3R0yRKAXUa6gRUml6okEmO4EewI9tpy0r_951taLI3Tfklvnz33ffdnfPKYpUg67JVpp7jNdcWZrdzCfDhAzwY1AY-wcOdCzxE7vwIZ2dfKBKNUGqEKWYYW6Ekhf5Z6vqXT9BL_uMxSgsHRCYS1PWZStMMHz3RnePYG5-KySJ1OFdH5Y7J7KH3_S6aYKy2W5QJ9_T3Ol6jsZpbpcFXIq6Dzr6iOhKfgTJyJal2F3hQEe8chvi87N5oGv1fHuonEeORERzGy8uU2hT5Hkbjg9Uxz2FK1SvY0dhDJYp0vVS-V8_u3ToPo2mVzptchK-LJzKutPdZmuAyEWQWgaCog-uPYGKlhUyrLvqjqASPAljpUlV_FGC9WXQy0zzeELflmUqhDrf0ZtCeBmBvdiAs0_bxkXphXS45mfajaVABA5kKiWXnj3Eh88IaF5z2_2532q8geJEItVght4Wbfh1wu8QkITYDJ2ETeHa6h-EgGgYQDF6cJLcAdRi8o72V4eDouXJy9SpCMeyHEY67VAKTaTThcoOaxncrnmjnhd1RiQmeaR_3FSZhjlblCwn6t-U0h0mWI3oo5zp4yTMuJF-KjGiroMGP75H_KsOwbwqR0VXxgzx5Xu_AroUBP4UwL0rwGgpDDTssGmn2CLA8_UPH3utPIBPGEhDLYgStaBwiJktHQkufl92HZWFLq5icVm5vJjZo6mYjclMn1h0RDm-id6K-yjI_9TCdm3D9fm_St1n0jf4Kbn_qMEarRWzCDXuselCrVUZLB0XutpLq3A-H0f0hOCuky_-qlqFtdO0L8vp--49tCg2kTF95NGY1lmqRsK7VBdbYFvWWuyN7dbg5s2vc4px16TXBFS8yO2dz-UZpOZf_KrU9ZmpVpGvWXfHM0ClovBU81byEuObpviqkZd1Wq-k5WPeVvbDu5efzz-32dbPZvG5dtS87nRrbsW6zc37Rvm603HN9cdG4vHqrsZ--avO80W40LlqdzlW72bpqNdo1homgro3Df9z_zt9-AcBG52M?type=png)

![Initial User Interface flowchart](https://mermaid.ink/img/pako:eNpdlF9v2jAUxb_KlZ8pIgTakodJLdB_WrdqnTRtzR5c55J4OHZkOwWK-O67dlIm9hYr53fPveda3jNhCmQZWymzERW3Hr4vcg1w9ZKzZ0_nPNePXGp4FhZR5-w3nJ19gmv6fYvaIjxJsUYbVK3yEhwqFJ5koch11M73Obsq_nCB2kMZIAeo-avCImeHXAflnJTwxUT9orPWBbcF1NyLSuqSDJZbLvoCYLTa9SYR_Uk1A7t8OXqJHQijvTXKQcM1qqgPxLKTJsGnkUqZN7TgvEVd-gqckkUcaATeQDIaQYM29N779fSY6Ee-hUI66lUgAQlUpgFjYRw-TuUpyZ8svkncwAZlWXnsh0NHaJcl-XX_wId4jg13Od6EfmO8hPY5urauud1RhXklG_fhmXZAR9_Ew23cmAeLwtQ1UrpeGv1B3EbNHWm-oaNFOlA0VyhLS3CwkRQMbhvFdcTAadk06I8d3kX-nvgf1Q58JR14y8WaKiws31C-FEttCq56w_sOSI73KO5KvrahPFGng0IyHAE_uUMwGm63p8XCSr76isxWdFOMDcEuNdpyB1yY1nkpqAdT_Nf1A2E3iMVr1-9nuUZwa9mQlmxUOIaBeq-HLik2YKWVBcu8bXHAarQ1D0e2D6KcURs1LTCjzwJXnCLNWa4PhNFd_GVM_UFa05YVy1ZcOTq1De0FF5KXlv-T0LbQzk2rPcvOL2IJlu3ZlmVnk_HwYprMpmkyng7YjmXJeDKcXIxns2Q2SdPpLL08DNh7NEyG43Q6TWfnkzSZji5HKZXCQlJSj90jEN-Cw18Tg1Hl?type=png)
[User Interface flowchart Mermaid.live](https://mermaid.live/edit#pako:eNpdlM1u2zAQhF9lwbNjSFYkxz4USGznD00bNAWKtuqBodYSa4oUSCq2a_jdu5QUF-5NhObb2Z0leGDCFMjmbK3MVlTcevi6zDXA9c-cvXg657l-4lLDi7CIOme_4OLiA9zQ7zvUFuFZig3aoGqVl-BQofAkC0VuOu3ikLPr4jcXqD2UAXKAmr8qLHJ2zHVQLkgJn0ynX_bWuuC2gJp7UUldksFqx8VQAIxW-8GkQ79TzcCufp68xB6E0d4a5aDhGlWnD8Sql8bBp5FKmTe04LxFXfoKnJJFN1AE3kAcRdCgDb0PfgM9IfqJ76CQjnoVSEAMlWnAWJiEj3N5QvJni28St7BFWVYeh-HQEdpnSX79P_AhnlPDfY63od8uXkKHHF1b19zuqcKiko1790x6oKdvu8NdtzEPFoWpa6R0vTT6nbjrNPek-YKOFulA0VyhLC3BwVZSMLhrFNcdBk7LpkF_6vC-4x-I_1btwVfSgbdcbKjC0vIt5Uux1KbgajB86IH4dI-6XcnXNpQn6nxQiMcR8LM7BNF4tzsvFlby2VdktqabYmwIdqXRlnvgwrTOS0E9mOK_rh8Ju0UsXvt-P8oNgtvIhrRko8IxDDR4PfZJsRErrSzY3NsWR6xGW_NwZIcgyhm1UdMC5_RZ4JpTpDnL9ZEwuos_jKnfSWvasmLzNVeOTm1De8Gl5KXl_yS0LbQL02rP5tlk1tVg8wPbsflFnCbj6WyaTK_SyyhKZlE2YnuSJeNJliVX01kyu0yTeJIeR-xP5xuPsyRNkySbZmk6zWZxMmJYSArsqX8Luifh-Bc-f1Np)

**Summary:**


### Setup
    
     Setup Instructions: Step-by-step directions to run your code.
    
1. Create a virtual environment (optional but recommended):
   ```bash
   python -m venv .venv
   source .venv/bin/activate      # Mac or Linux
   .venv\Scripts\activate         # Windows
   ```
2. Install dependencies
    ```bash
    pip install -r requirements.txt
    ```
3. Run the program
    ```
    python -m src.main
    ```

### Sample Interactions
    Sample Interactions: Include at least 2-3 examples of inputs and the resulting AI outputs to demonstrate the system is functional.
### Design Decisiions
    Design Decisions: Why you built it this way, and what trade-offs you made.
    

### Testing Summary 
    Testing Summary: What worked, what didn't, and what you learned.

### Reflection
    Reflection: What this project taught you about AI and problem-solving.
  
  
