# Reference fixes (BSc report → paper)

Each citation was checked against the publisher or an indexer (PMC, ACL Anthology, DOI). Fix the same errors in any other version of the work you circulate.

| Report citation | Problem | Correct reference |
|---|---|---|
| Chen et al. (2024), "generative AI chatbot built with OpenAI API, React.js, Node.js" | Wrong author, and the description is invented. The NEJM AI trial is Therabot, a Dartmouth system, and its paper describes no React/Node stack. Your own link pointed to `2025-heinz.pdf`. | Heinz, M. V. et al. (2025). Randomized Trial of a Generative AI Chatbot for Mental Health Treatment. *NEJM AI* 2(4). doi:10.1056/AIoa2400802 |
| He Y et al. (2023), "XiaoE … microservices architecture" | The reference you gave is a meta-analysis (*JMIR* 2023;25:e43862), not XiaoE. The microservices description isn't in either paper. | He, Y., Yang, L. et al. (2022). Mental Health Chatbot for Young Adults With Depressive Symptoms During the COVID-19 Pandemic: Single-Blind, Three-Arm RCT. *JMIR* 24(11):e40719. doi:10.2196/40719 |
| Gaffney (2020), "web-based anxiety chatbot using Angular and Node.js" | The cited paper is MYLO (2014), a problem-solving program based on Method of Levels therapy. It isn't an anxiety chatbot, and no Angular/Node stack is described. | Gaffney, H., Mansell, W., Edwards, R., Wright, J. (2014). Manage Your Life Online (MYLO)… *Behavioural and Cognitive Psychotherapy* 42(6):731–746 |
| Morris (2022), "Python and Django, custom NLP models" | The paper is from 2018. It repurposes peer-support responses, and no Django stack is described. | Morris, R. R. et al. (2018). Towards an Artificially Empathic Conversational Agent… *JMIR* 20(6):e10148. doi:10.2196/10148 |
| Fulmer (2019) | Published in 2018. | *JMIR Mental Health* 5(4):e64. doi:10.2196/mental.9782 |
| Abd-Alrazaq (2021), *JMIR* 23(7) | The year, volume and DOI don't match: your link is the 2020 paper. That paper reviews effectiveness and safety outcomes, not "database designs and authentication". | Abd-Alrazaq, A. A. et al. (2020). *JMIR* 22(7):e16021. doi:10.2196/16021 |
| Fitzpatrick (2017) | The "doi" field held the journal name. | *JMIR Mental Health* 4(2):e19. doi:10.2196/mental.7785 |
| Woebot "Node.js", Wysa "React Native", Tess "Python backend" | These tech stacks aren't stated in the cited papers. Removed. | n/a |
| Kehinde P.F (2024) | The author name is inverted: the surname is Fadele. | Fadele, K. P. et al. (2024). *Cambridge Prisms: Global Mental Health*. doi:10.1017/gmh.2024.19 |
| Obinna O Oleribe (2021), *Annals of Ibadan Postgraduate Medicine* | Wrong first author and wrong journal. | Soroye, M. O., Oleribe, O. O., Taylor-Robinson, S. D. (2021). *Journal of Multidisciplinary Healthcare* 14:1145–1148. doi:10.2147/JMDH.S309517 |
| Haque M (2023) **and** M D Romael Haque (2023) | The same paper is listed twice. | Haque, M. D. R., Rubya, S. (2023). *JMIR mHealth uHealth* 11:e44838 |
| Coker (2024) **and** TC Health (2024) | The same article is listed twice, and it's a blog. Dropped. | n/a |
| CBS News, Towards Healthcare, Nairametrics, RGA (Farvolden) | News, market-research and industry sources. Dropped from the paper. | n/a |
| 250 vs "fewer than 200" psychiatrists; 50M vs 40M affected | The figures contradict each other. | The paper uses only Fadele 2024 (≈250 psychiatrists for 200M+ people) and Soroye 2021 (WHO's one-in-four estimate). |

## New references added for the paper's framing
Moore et al. 2025 (FAccT), McBain et al. 2025 (*Psychiatric Services*), Weber et al. 2026 (medRxiv preprint), Ji et al. 2021 (IEEE TCSS), Posner et al. 2011 (C-SSRS), Muhammad et al. 2022 (NaijaSenti, LREC), Ajayeoba et al. 2023 (Sniper poisoning case report), WHO 2021, and Nigeria's Criminal Code s.327.

## Before you submit
- Weber et al. is a preprint. Check whether it has since been published, and cite the published version if so.

## Second verification pass (2026-10-16)
Every DOI was re-resolved through the Crossref API (`results/refcheck/crossref.json`). Authors, titles, venues, volumes, issues, pages and years now come from Crossref, and full author lists replace every "and others". Corrections made:
- **Weber et al. 2026:** the first author is *Samantha* Weber (the first draft said "Samuel").
- **Gaffney et al. 2014 (MYLO):** DOI 10.1017/S135246581300060X confirmed and restored.
- **Fadele et al. 2024:** volume 11, article e29, restored.
- **McBain et al. 2025:** *Psychiatric Services* 76(11):944–950.
- **Moore et al. 2025:** FAccT proceedings, pp. 599–627.
- **NaijaSenti:** full author list taken from the ACL Anthology BibTeX.
- **WHO 2021:** confirmed on who.int (ISBN 9789240026643). It's now cited for "77% of suicides occur in LMICs".
- **Haque & Rubya 2023:** no longer cited, because its content couldn't be pinned to a specific claim.

## Other facts checked
- **Helplines:** MANI's 0809 111 6264 is confirmed. The Nigeria Suicide Prevention Initiative's lines end in **6493** (BusinessDay, 2023), but **MindEase's crisis prompt says 0806 210 6492 — wrong by one digit. Fix this in the app.** The paper's content warning now uses SURPIN (0800 078 7746, toll-free, 24 hours; LifeLine International listing), MANI and 112.
- **System description:** checked against the MindEase code. Anonymous JWTs last 7 days, not 24 hours. The response model sees a short window of stored messages. The disclaimer appears in the crisis modal and the system prompt.
- **Dataset authorship:** the test messages were drafted with an AI assistant. The paper now says so, and adds a "Use of AI assistants" statement.
