# IONOS Cloud (`ionoscloud`)
- Request-basiert: jede Mutation liefert eine Request-URL; Status
  (QUEUED/RUNNING/DONE/FAILED) pollen. FAILED muss als Order-Fehler in
  Waldur sichtbar werden.
- Virtual-Data-Center-Konzept: VDC pro Waldur-Projekt oder global ist
  eine EXPLIZITE Config-Entscheidung, keine stille im Code.
- Vor Implementierungsstart: SDK-Semantik gegen echten Account
  verifizieren (Phase 2 nicht ohne Grund).
