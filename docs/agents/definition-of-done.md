# Definition of Done (Langform, gilt in allen Repos)

Ein Task ist erst fertig, wenn dieser Selbstbericht abgegeben ist:

1. **Annahmen**: Welche Annahmen über Upstream-Interfaces,
   Provider-API-Verhalten und Config stecken drin? Welche wurden
   durch Lesen des Referenz-Codes bzw. Testlauf verifiziert, welche
   nur unterstellt?
2. **Negativfall**: Welche Eingabe/Reihenfolge bricht die Lösung?
   Wurde sie als Test kodiert?
3. **Wiederholung**: Zweiter und dritter Lauf derselben Order
   getestet? Teilweise abgebrochener Zustand?
4. **Kollision**: Zwei Orders auf denselben Namen/dieselbe VMID?
5. **Stille Entscheidungen**: Wo wählt der Code aus mehreren
   Möglichkeiten, ohne dass die Regel in Config oder Doku steht?
   Entweder konfigurierbar machen oder dokumentieren.
6. **Gemessen statt geschätzt**: Behauptungen über API-Verhalten
   (Feldnamen, Statuswerte) gegen SDK-Quelltext oder echten
   API-Response geprüft, nicht aus Trainingsgedächtnis übernommen.
7. **Fehlerpfad**: Schlägt der neue Codepfad sichtbar fehl
   (Waldur-Order-State), oder sieht Fehlschlag wie Erfolg aus?
8. **Ehrliche Bilanz**: Explizit sagen, was ausgeführt/getestet
   wurde, was ungetestet bleibt, welche Restrisiken offen sind.
   Nichts als verifiziert bezeichnen, was nicht gelaufen ist.

Befunde — auch unbequeme, auch solche, die frühere eigene Arbeit
infrage stellen — gehören unaufgefordert in die Antwort und, wenn
dauerhaft relevant, nach NOTES.md.
