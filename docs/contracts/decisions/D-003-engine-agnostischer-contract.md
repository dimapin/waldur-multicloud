# D-003: Engine-agnostische Provisionierungs-Normen + OpenTofu-Anhang
Datum: 2026-08-31 · Status: vorgeschlagen
## Kontext
ionos-k8s soll das bestehende OpenTofu-Standard-Setup (pro Cluster)
wrappen; Crossplane ist realistischer Kandidat (v. a. STACKIT). Der
Contract darf die Engine nicht festschreiben.
## Entscheidung (Vorschlag)
Engine-agnostischer Kern CON-060..063; OpenTofu-Anhang CON-065..067
(Remote State S3-kompatibel, use_lockfile ab OpenTofu 1.10,
Versioning, State-Encryption, Tag-Recovery). Crossplane-Anhang folgt
bei Bedarf als eigener Vorschlag.
## Verworfene Alternativen (und warum)
OpenTofu-Normen als Kern: würde Crossplane/SDK-Backends zu
Pseudo-State-Konstrukten zwingen. Engine-Freiheit ohne Norm: stille
Entscheidungen, nicht testbar.
## Klasse und betroffene IDs
MINOR → contract-v0.3.0 (zusammen mit D-004). Neue IDs, keine
Änderung bestehender.
## Betroffene Repos / Folge-MRs
Testkit (CON-061-Konvergenztests engine-neutral), ionos-Repo.
Offene Prüfpunkte: NOTES.md (Conditional-Write-Support IONOS-S3,
Agent-Nebenläufigkeit, Crossplane-Provider-Reife IONOS/STACKIT).
