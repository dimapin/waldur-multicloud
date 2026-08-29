# AGENTS.md — waldur-multicloud (Meta-Repo)

> **Status: EXPERIMENT.** Dieses Projekt läuft als öffentlicher Versuch.
> Ob und wie es weitergeführt wird, ist nicht entschieden. Keine
> Produktionsnutzung. Kein offizielles Waldur-Projekt.

## Zweck dieses Repos

Schaufenster und Koordinationspunkt des Multi-Cloud-Experiments:
Waldur-Site-Agent-Plugins für mehrere Provider, entwickelt in einem
Multi-Agenten-Workflow. Hier liegt alles, was repo-übergreifend gilt;
Provider-Code liegt in den Provider-Repos.

## Repo-Landschaft

| Repo | Inhalt | Status |
|---|---|---|
| `waldur-multicloud` (dieses) | Contract, Testkit, Rollen-Kanon, Workflow, Demo-Deployment | aktiv |
| `waldur-site-agent-hcloud` | Hetzner-Cloud-Plugin | Phase 1 |
| `waldur-site-agent-proxmox` | Proxmox-VE-Plugin | Phase 1 |
| `waldur-site-agent-ionos` | IONOS-Cloud-Plugin | Phase 2, Stub |
| `waldur-site-agent-stackit` | STACKIT-Plugin | später |

Neue Provider entstehen durch Kopie des Template-Verzeichnisses
(`waldur-site-agent-template/` bzw. GitHub-Template-Repo), nicht durch
Nachbau aus dem Gedächtnis.

## Was hier liegt und welche Regeln gelten

### docs/contracts/ — die Interface-Wahrheit
- Wird ausschließlich vom Subagenten `upstream-scout` geschrieben
  (Rollendefinition unter `.claude/agents/`).
- Jede Aussage trägt Fundstelle: Datei + Zeilen + Upstream-Commit.
- Änderungen werden als Git-Tag versioniert (`contract-vN`).
  Provider-Repos pinnen diesen Tag; ein Contract-Update ist damit
  immer sichtbar: 1 MR hier, danach je 1 MR pro Provider-Repo.

### testkit/ — installierbares Paket mit Contract-Tests
- Enthält die provider-übergreifenden Contract-Tests und gemeinsame
  Fixtures. Exklusiver Besitzer ist die Rolle `test-engineer`;
  Implementer-Änderungen hier sind ein Sperr-Befund im Review
  (technisch abgesichert via CODEOWNERS).
- Provider-Repos konsumieren das Testkit als uv-Git-Dependency,
  gepinnt auf einen Tag dieses Repos — nie auf `main`.
- Bewusst dünn halten: gemeinsame Slug-/Tag-Konventionen,
  Retry-Helfer, Testbasis. KEINE Abstraktionsschicht über den
  Waldur-Basisklassen (Begründung: die Basisklassen SIND die
  Multi-Cloud-Abstraktion; eine zweite Ebene müsste jeden
  Upstream-Change doppelt nachziehen).

### docs/agents/ — kanonische Rollendefinitionen
- Herstellerneutrale Quelle der Wahrheit für die vier Rollen
  (upstream-scout, provider-implementer, test-engineer,
  code-reviewer). Die `.claude/agents/`-Dateien hier und in den
  Provider-Repos sind Kopien mit Claude-Code-Frontmatter.
- Sync-Regel: Rollenänderung zuerst hier, dann in die Wrapper
  kopieren. Wer einen Wrapper direkt ändert, erzeugt stille Drift —
  der Reviewer prüft das stichprobenartig.

### docs/providers/ — Provider-Eigenheiten
- Eine Datei pro Provider (API-Semantik, Async-Muster, Fallstricke).
  Provider-Repos vendorn "ihre" Datei als docs/PROVIDER_NOTES.md.

## Upstream-Verankerung

- Core-Paket: `waldur-site-agent` von PyPI, Serie 1.x (MIT,
  Python ≥3.9). In allen Repos exakt pinnen. Bei jedem Versions-Bump:
  upstream-scout laufen lassen und Basisklassen-Diff gegen den
  Contract prüfen, BEVOR ein Provider-Repo die neue Version zieht.
  (1.x heißt SemVer-Versprechen, nicht SemVer-Garantie —
  der Diff-Check bleibt Pflicht.)
- Referenz-Klon für den Scout: /tmp/waldur-site-agent-ref, read-only.

## Public-Repo-Hygiene (nicht verhandelbar)

Dieses Repo und alle Provider-Repos sind öffentlich. Daraus folgt:

1. **NOTES.md ist öffentlich.** Keine internen Hostnamen, Endpoints,
   Organisations- oder Projektnamen, keine Kundenbezüge — nirgendwo,
   auch nicht in Commit-Messages oder Configs. Beispielwerte sind
   erkennbar fiktiv (example.invalid, PLACEHOLDER).
2. **Secret Scanning + Push Protection** sind vor dem ersten Commit
   aktiv. Ein doch gepushtes Secret gilt als kompromittiert und wird
   rotiert — Historie umschreiben reicht nicht.
3. **E2E-Tests mit echten Provider-Credentials** laufen NIE auf
   Fork-PRs. Nur `workflow_dispatch` auf geschütztem Branch mit
   Environment-Secrets. Kein `pull_request_target` mit Checkout von
   Fremdcode.
4. **Lizenz MIT** (kompatibel zu Upstream), LICENSE-Datei in jedem
   Repo. README trägt den Experiment-Disclaimer und den Hinweis
   "Community-Projekt, nicht mit Waldur/OpenNode affiliiert".

## Kommandos

```bash
uv sync --all-packages
uv run pytest             # Testkit-Tests
uvx prek run --all-files  # Format + Lint
```

CI: GitHub Actions (.github/workflows/ci.yml) führt exakt dieselben
Kommandos aus. Was lokal grün ist, muss in CI grün sein — Divergenz
zwischen beiden ist ein eigener Befund.

## Definition of Done (Kurzform, gilt in allen Repos)

Vor "fertig" berichtet jede Rolle: (1) unverifizierte Annahmen,
(2) der Negativfall, der am ehesten bricht, (3) Verhalten bei
Wiederholung/abgebrochenem Zustand, (4) Kollisionen, (5) stille
Entscheidungen, (6) gemessen statt geschätzt (SDK-Quelltext/echte
Responses statt Gedächtnis), (7) Sichtbarkeit des Fehlerpfads,
(8) gefundene Fehler als Klasse behandelt, (9) ehrliche Bilanz:
ausgeführt vs. ungetestet vs. Restrisiko. Langform in
docs/agents/definition-of-done.md.

## Verbote

- Keine API-Signaturen oder Endpunkte aus dem Gedächtnis erfinden.
- Keine Secrets in Code, Configs, Tests, Historie.
- Kein `git push --force` auf main, keine Releases ohne Auftrag.
- Referenz-Klon read-only.
- Contract und Testkit werden nur aus diesem Repo geändert, nie aus
  einem Provider-Repo heraus.
