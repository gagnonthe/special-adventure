# playscore_to_musicxml

Petit utilitaire Python pour extraire un fichier MusicXML depuis un fichier `.playscore` (archive ZIP contenant au moins `doc.xml` or `doc.mid`).

Fonctionnement
- Si `doc.xml` présent et semblant être du MusicXML (tag racine `score-partwise`, `score-timewise` ou `score`), il est extrait tel quel en sortie.
- Sinon si `doc.mid` est présent, le script tente une conversion MIDI -> MusicXML via la librairie `music21`.

Limitations
- Si l'archive contient uniquement des images scannées (pages JPEG/PNG), l'OCR musical (conversion image -> MusicXML) n'est pas implémenté ici.

Installation (PowerShell, Windows)
```powershell
python -m venv .venv ; .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Exemples d'utilisation
```powershell
# extraction automatique du nom de sortie (154.musicxml)
python playscore_to_musicxml.py 'C:\Users\lucaspereiradealmeid\Downloads\154.playscore'

# ou spécifier explicitement le fichier de sortie
python playscore_to_musicxml.py 'C:\path\to\file.playscore' 'C:\path\to\out.musicxml'
```

Dépannage
- Si la conversion MIDI échoue, vérifiez que `music21` est installé et que le MIDI lui-même est valide.
- Si `doc.xml` est présent mais n'est pas MusicXML, examinez-le avec un éditeur de texte pour déterminer son format.

Améliorations possibles
- Supporter l'OCR musical (Audiveris ou services commerciaux) pour convertir les images scannées en MusicXML.
- Gérer plus finement les namespaces XML et les encodages.
