# NOTES
Oeffentliches Befund-Journal. Keine Interna (siehe AGENTS.md, Hygiene).

## Erhebungsaufträge an upstream-scout (aus D-002, für upstream-api.md)
- Komponenten-Definition: exakte Felder/Abrechnungsarten, Verhalten von
  waldur_site_load_components bei unvollständigen Angaben (CON-040)
- Plan-/Preis-Mechanik: wo Preise gepflegt werden, API dafür (CON-041)
- Ressourcen-Metadaten: Feld/Endpoint, Größenlimits, Secret-geeigneter
  Mechanismus für Credentials (CON-050/053)
- Usage-Report: Endpoint, Verhalten bei unbekannter Komponente —
  Fehler oder stilles Verwerfen? (entscheidet Testbarkeit von CON-051)

## Erhebungsaufträge aus D-003/D-004
- IONOS Object Storage: Conditional Writes (If-None-Match) für
  OpenTofu use_lockfile unterstützt? (entscheidet State-Backend)
- Site Agent: Order-Verarbeitung parallel oder seriell? Timeouts bei
  20–30-min-Läufen? (entscheidet OpenTofu-sync vs. entkoppelt)
- Crossplane-Provider-Reife für IONOS und STACKIT
- Je Provider: Kontingent-Abfrage-API ja/nein + Fehlercodes bei
  Überschreitung (docs/providers/, Limit-Abschnitte)
- Waldur: Komponenten-Min/Max je Order — Mechanik; gibt es aggregierte
  Kapazität je Offering bzw. Projekt-Quotas? (CON-072-Umsetzung)
