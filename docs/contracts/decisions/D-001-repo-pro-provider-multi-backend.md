# D-001: Ein Repo pro Provider, mehrere Backends pro Repo
Datum: 2026-08-30 · Status: angenommen
## Kontext
Provider bieten mehrere Service-Klassen (z. B. IONOS: compute, k8s,
dbaas). Kapselungs-Granularität war offen.
## Entscheidung
Ein Repository pro Provider. Innerhalb des Repos ein Backend pro
Service-Klasse (backends/-Paket, je ein Entry-Point, Namensschema
CON-001), gemeinsamer Client für Auth/Polling/Retry.
## Verworfene Alternativen (und warum)
Repo pro Service: dupliziert Client, SDK-Pinning und Provider-Notes;
Repo-Zahl wächst mit Provider × Service. Revisionspunkt: ein Service
mit schweren Sonderabhängigkeiten.
## Klasse und betroffene IDs
MINOR (initial): CON-001, CON-002.
## Betroffene Repos / Folge-MRs
Template (backends/-Struktur), alle Provider-Repos bei Anlage.
