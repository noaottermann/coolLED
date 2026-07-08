import os

def afficher_arborescence(racine, prefixe=""):
    elements = sorted(os.listdir(racine))

    for i, element in enumerate(elements):
        chemin = os.path.join(racine, element)
        dernier = i == len(elements) - 1

        branche = "└── " if dernier else "├── "
        print(prefixe + branche + element)

        if os.path.isdir(chemin):
            nouveau_prefixe = prefixe + ("    " if dernier else "│   ")
            afficher_arborescence(chemin, nouveau_prefixe)

# Dossier à explorer
dossier = ""

print(os.path.basename(dossier) or dossier)
afficher_arborescence(dossier)