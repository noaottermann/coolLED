import os
import ast

def scan_src_layout():
    # Le chemin standard pour un src-layout
    target_dir = os.path.join("coolledx", "src")
    
    if not os.path.exists(target_dir):
        # Si jamais le sous-dossier porte un autre nom, on cherche dans src/
        if os.path.exists("src"):
            subdirs = os.listdir("src")
            if subdirs:
                target_dir = os.path.join("src", subdirs[0])
            else:
                print("❌ Le dossier 'src' est vide.")
                return
        else:
            print("❌ Dossier 'src' introuvable.")
            return

    print(f"--- Analyse des fichiers dans '{target_dir}/' ---\n")
    
    # On liste récursivement ou directement les fichiers .py
    for root, dirs, files in os.walk(target_dir):
        py_files = [f for f in files if f.endswith('.py')]
        for filename in py_files:
            filepath = os.path.join(root, filename)
            # Afficher le chemin relatif par rapport à src/
            rel_path = os.path.relpath(filepath, "src")
            print(f"📄 Fichier source : {rel_path}")
            
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    node = ast.parse(f.read(), filename=filepath)
                
                classes = [n.name for n in node.body if isinstance(n, ast.ClassDef)]
                functions = [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
                
                if classes:
                    print(f"   🔹 Classes : {', '.join(classes)}")
                if functions:
                    print(f"   🔻 Fonctions : {', '.join(functions)}")
                if not classes and not functions:
                    print("   (Fichier d'initialisation ou constantes)")
                    
            except Exception as e:
                print(f"   ❌ Erreur de lecture : {e}")
            print("-" * 50)

if __name__ == "__main__":
    scan_src_layout()