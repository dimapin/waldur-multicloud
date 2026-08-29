# Multi-Agenten-Workflow v2 — Vier-Repo-Schnitt, öffentlich auf GitHub

Ersetzt v1 (Monorepo/GitLab). Änderungen gegenüber v1 am Ende.

## Rollen und Orte

| Rolle | läuft in | schreibt |
|---|---|---|
| upstream-scout | Meta-Repo | docs/contracts/ (getaggt `contract-vN`), NOTES.md |
| test-engineer | Meta-Repo (Testkit) + Provider-Repo (acceptance) | testkit/, tests/acceptance/ |
| provider-implementer | genau ein Provider-Repo | Plugin-Code + tests/unit/ |
| code-reviewer | jedes Repo | docs/reviews/ |
| Mensch | überall | Merge-Entscheidung, Contract-Streitfälle |

Parallelität: eine Claude-Code-Session pro Provider-Repo (ersetzt die
Worktrees aus v1). Koordination läuft ausschließlich über getaggte
Artefakte des Meta-Repos — Contract-Tag und Testkit-Tag stehen in
jedem Delegations-Prompt.

## Ablauf pro Arbeitspaket

1. **Contract sicherstellen** (Meta-Repo): Scout läuft bei
   Projektstart und bei jedem Upstream-Versions-Bump. Ergebnis wird
   getaggt. Ohne gültigen Tag startet kein Provider-Paket.
2. **Fan-out**: Implementer (Provider-Repo) und Test-Engineer
   (Testkit/acceptance) erhalten dasselbe Arbeitspaket, denselben
   Contract-Tag — und bleiben gegenseitig blind: Der Test-Engineer
   liest keine Implementierung, der Implementer fasst keine
   Contract-/Acceptance-Tests an.
3. **Zusammenführen**: Provider-Branch zieht den Testkit-Tag,
   Gesamtsuite läuft. Rot ist erwünscht — hier zeigen sich
   Differenzen zwischen Implementierung und unabhängiger Erwartung.
   Streit entscheidet der Contract; ist der unklar → Scout bzw.
   Mensch, nie der Implementer allein.
4. **Review**: code-reviewer prüft den Diff, führt selbst alle Tests
   aus, klassifiziert Befunde (SPERREND/WICHTIG/ANMERKUNG), max. zwei
   Runden, dann Eskalation an den Menschen.
5. **CI + Mensch**: GitHub Actions (identische Kommandos) muss grün
   sein; Merge nur durch den Menschen. CODEOWNERS erzwingt
   Menschen-Review auf testkit/, docs/contracts/ (Meta) und
   tests/acceptance/ (Provider).

## Cross-Repo-Änderungen (der teure Pfad — bewusst so)

Contract- oder Testkit-Änderung = 1 Meta-MR (getaggt) + je 1
Folge-MR pro Provider-Repo, der den neuen Tag pinnt. Reihenfolge
strikt: erst Meta gemerged und getaggt, dann Provider. Ein
Provider-Repo, das einen ungetaggten Meta-Stand referenziert, ist
ein Sperr-Befund im Review.

## CI-Gates (GitHub Actions)

- **ci.yml** (push/PR): `uv sync` → `uvx prek run --all-files` →
  `uv run pytest -m "not e2e"`. Läuft auch für Fork-PRs — enthält
  deshalb keinerlei Secrets.
- **e2e.yml**: NUR `workflow_dispatch`, GitHub-Environment `e2e` mit
  Provider-Credentials, geschützter Branch. Ressourcen tragen
  TTL-Tags; Cleanup sucht per Tag, nicht per im Test gehaltener IDs
  (räumt damit auch nach Abbruch auf). Kein `pull_request_target`.
- E2E ist der einzige Prüfstein gegen die Realität statt gegen das
  Contract-Dokument — vor jedem "Meilenstein erreicht" einmal
  ausführen und das Ergebnis in den Review-Report aufnehmen.

## Grenzen (unverändert gültig, plus zwei neue)

- Implementer und Reviewer sind dasselbe Modell mit anderem Prompt —
  geteilte blinde Flecken. Harte Gegengewichte: konstruierte
  Test-Unabhängigkeit, CI, Mensch.
- Tool-Restriktionen der Subagents sind weich; durchgesetzt wird
  Rollentrennung durch Diff-Sichtung + CODEOWNERS.
- Der Contract bleibt Single Point of Failure — jetzt aber versioniert
  und mit Fundstellenpflicht; E2E prüft gegen die Realität.
- **Neu (Multi-Repo):** Rollen-Wrapper in den Provider-Repos können
  vom Kanon (Meta docs/agents/) driften. Sync-Regel: Änderung zuerst
  im Kanon; Reviewer zieht Stichproben.
- **Neu (öffentlich):** Alles ist sofort öffentlich, auch Fehler und
  NOTES.md. Das ist als Experiment gewollt (nachvollziehbare
  Historie), verlangt aber die Hygiene-Regeln aus AGENTS.md ab dem
  ersten Commit — Git-Historie lässt sich praktisch nicht
  zurückholen.

## Änderungen gegenüber v1 (Korrekturen ausgewiesen)

1. **Upstream ist 1.x auf PyPI, nicht pre-1.0** — v1 behauptete das
   fälschlich. Pinning + Diff-Check bei Bumps bleiben Pflicht,
   die Begründung ist korrigiert.
2. **GitLab-CI → GitHub Actions** (öffentliches GitHub-Hosting).
3. **Monorepo → 4 Repos**; `libs/multicloud-common` ist im Testkit
   des Meta-Repos aufgegangen; Worktrees → Sessions pro Repo.
4. **CODEOWNERS ersetzt die rein prozessuale Schutzregel** für
   Contract-/Acceptance-Tests aus v1.
