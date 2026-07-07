import importlib
import inspect
import sys

def analyze_module():
    module_name = "coolledx"
    
    print(f"--- Analyse du module '{module_name}' (Python {sys.version.split()[0]}) ---\n")
    
    try:
        # Import dynamique du module
        coolledx = importlib.import_module(module_name)
    except ImportError as e:
        print(f"❌ Impossible d'importer '{module_name}'. Erreur : {e}")
        return

    print("=" * 50)
    print("STRUCTURE DES CLASSES ET MÉTHODES")
    print("=" * 50)

    # Inspecter les membres du module de manière sécurisée
    for name, obj in inspect.getmembers(coolledx):
        # On ignore les variables privées dunder (__xx__)
        if name.startswith('__'):
            continue
            
        if inspect.isclass(obj):
            print(f"\n🔹 Classe trouvée : {name}")
            doc = inspect.getdoc(obj)
            if doc:
                print(f"   Docs : {doc.splitlines()[0]}")
                
            # Inspecter les méthodes de la classe
            for method_name, method_obj in inspect.getmembers(obj, predicate=inspect.isfunction):
                if method_name.startswith('__') and method_name != '__init__':
                    continue
                try:
                    sig = inspect.signature(method_obj)
                    print(f"   🔸 Méthode : {method_name}{sig}")
                except Exception:
                    print(f"   🔸 Méthode : {method_name}(...)")
                    
        elif inspect.isfunction(obj):
            try:
                sig = inspect.signature(obj)
                print(f"\n🔻 Fonction globale : {name}{sig}")
            except Exception:
                print(f"\n🔻 Fonction globale : {name}(...)")

if __name__ == "__main__":
    analyze_module()