# IONOS Cloud (`ionoscloud`)
- Request-basiert: jede Mutation liefert eine Request-URL; Status
  (QUEUED/RUNNING/DONE/FAILED) pollen. FAILED muss als Order-Fehler in
  Waldur sichtbar werden.
- Virtual-Data-Center-Konzept: VDC pro Waldur-Projekt oder global ist
  eine EXPLIZITE Config-Entscheidung, keine stille im Code.
- Vor Implementierungsstart: SDK-Semantik gegen echten Account
  verifizieren (Phase 2 nicht ohne Grund).

## Limits (D-004)
- Vertrags-Kontingente (Cores, RAM, VMs je Vertrag): vorhanden;
  nach bisherigem Stand über die Contract-API abfragbar — ZU ERHEBEN
  (Endpoint, Felder, ob Auslastung mitgeliefert wird).
- Skalierungsdecke: Kontingent je Vertrag ist Vertragsverhandlung mit
  Vorlauf; ggf. Sharding über mehrere Verträge als späterer
  Decision-Punkt.
