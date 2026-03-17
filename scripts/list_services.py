"""
Script pour lister tous les services disponibles dans OpenSlice

Utilisation:
    python scripts/list_services.py                    # Résumé des services
    python scripts/list_services.py --detail           # Détails complets
    python scripts/list_services.py --json             # Format JSON brut
    python scripts/list_services.py --search <terme>   # Rechercher un service
"""

import sys
import os
import json
from datetime import datetime

# On s'assure que Python regarde dans le dossier courant
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp.openslice_client import OpenSliceClient


def list_services_summary():
    """Affiche un résumé de tous les services disponibles"""
    print("\n🔍 Connexion au catalogue OpenSlice...")
    client = OpenSliceClient()
    
    try:
        # Authentification
        client.authenticate()
        
        # Récupération du catalogue (TMF633 - Service Catalog Management)
        services = client.get_catalog()
        
        print(f"\n✅ Connexion réussie ! {len(services)} service(s) trouvé(s).\n")
        
        if not services:
            print("⚠️  Aucun service disponible dans le catalogue")
            return
        
        # Afficher le résumé
        print("="*100)
        print(f"{'NOM':<50} | {'ID':<36} | {'VERSION':<10}")
        print("="*100)
        
        for service in sorted(services, key=lambda x: x.get('name', '')):
            name = service.get('name', 'Sans nom')[:48]
            service_id = service.get('id') or service.get('uuid') or 'N/A'
            service_id = str(service_id)[:34]
            version = service.get('version') or 'N/A'
            version = str(version)[:8]
            
            print(f"{name:<50} | {service_id:<36} | {version:<10}")
        
        print("="*100)
        print(f"\n📊 STATISTIQUES:")
        print(f"  • Total services: {len(services)}")
        print(f"  • Avec description: {len([s for s in services if s.get('description')])}")
        print(f"\n💡 Pour voir les détails: python scripts/list_services.py --detail")
        print(f"💡 Pour chercher: python scripts/list_services.py --search <terme>")
        
    except Exception as e:
        print(f"❌ Erreur lors de la récupération : {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()


def list_services_detail():
    """Affiche les détails complets de tous les services"""
    print("\n🔍 Connexion au catalogue OpenSlice (mode détail)...")
    client = OpenSliceClient()
    
    try:
        client.authenticate()
        services = client.get_catalog()
        
        if not services:
            print("⚠️  Aucun service disponible")
            return
        
        print(f"\n✅ {len(services)} service(s) trouvé(s).\n")
        
        for i, service in enumerate(sorted(services, key=lambda x: x.get('name', '')), 1):
            print("\n" + "="*100)
            print(f"[{i}] SERVICE: {service.get('name', 'Sans nom')}")
            print("="*100)
            
            print(f"  ID                : {service.get('id', 'N/A')}")
            print(f"  Version           : {service.get('version', 'N/A')}")
            print(f"  Type              : {service.get('@type', 'N/A')}")
            print(f"  Status            : {service.get('status', 'N/A')}")
            print(f"  Href              : {service.get('href', 'N/A')}")
            
            if service.get('description'):
                desc = service.get('description')
                if len(desc) > 100:
                    print(f"  Description       : {desc[:97]}...")
                else:
                    print(f"  Description       : {desc}")
            
            # Afficher les caractéristiques si disponibles
            if service.get('serviceCharacteristic'):
                print(f"\n  Caractéristiques ({len(service['serviceCharacteristic'])}):")
                for char in service['serviceCharacteristic'][:5]:  # Limiter à 5
                    char_name = char.get('name', 'N/A')
                    char_desc = char.get('description', '')
                    if char_desc:
                        print(f"    • {char_name}: {char_desc}")
                    else:
                        print(f"    • {char_name}")
                if len(service['serviceCharacteristic']) > 5:
                    print(f"    ... et {len(service['serviceCharacteristic']) - 5} autres")
        
        print("\n" + "="*100)
        
    except Exception as e:
        print(f"❌ Erreur : {e}")
    finally:
        client.close()


def list_services_json():
    """Affiche le JSON brut de tous les services"""
    print("\n🔍 Connexion au catalogue OpenSlice (JSON brut)...\n")
    client = OpenSliceClient()
    
    try:
        client.authenticate()
        services = client.get_catalog()
        
        print(json.dumps(services, indent=2, default=str))
        
    except Exception as e:
        print(f"❌ Erreur : {e}")
    finally:
        client.close()


def search_services(search_term):
    """Recherche des services par nom ou description"""
    print(f"\n🔍 Recherche de '{search_term}' dans le catalogue OpenSlice...\n")
    client = OpenSliceClient()
    
    try:
        client.authenticate()
        services = client.get_catalog()
        
        # Recherche insensible à la casse
        term_lower = search_term.lower()
        results = []
        
        for service in services:
            name = service.get('name', '').lower()
            desc = service.get('description', '').lower()
            service_id = service.get('id', '').lower()
            
            if (term_lower in name or 
                term_lower in desc or 
                term_lower in service_id):
                results.append(service)
        
        if not results:
            print(f"❌ Aucun service trouvé pour '{search_term}'")
            return
        
        print(f"✅ {len(results)} résultat(s) trouvé(s):\n")
        print("="*100)
        print(f"{'NOM':<50} | {'ID':<36}")
        print("="*100)
        
        for service in sorted(results, key=lambda x: x.get('name', '')):
            name = service.get('name', 'Sans nom')[:48]
            service_id = service.get('id', 'N/A')[:34]
            print(f"{name:<50} | {service_id:<36}")
            
            # Afficher la description en petite police
            if service.get('description'):
                desc = service.get('description')
                if len(desc) > 80:
                    print(f"  → {desc[:77]}...")
                else:
                    print(f"  → {desc}")
        
        print("="*100)
        
    except Exception as e:
        print(f"❌ Erreur : {e}")
    finally:
        client.close()


def main():
    if len(sys.argv) < 2:
        list_services_summary()
    elif sys.argv[1] == "--detail":
        list_services_detail()
    elif sys.argv[1] == "--json":
        list_services_json()
    elif sys.argv[1] == "--search":
        if len(sys.argv) > 2:
            search_term = " ".join(sys.argv[2:])
            search_services(search_term)
        else:
            print("❌ Utilisation: python scripts/list_services.py --search <terme>")
    else:
        print("""
Usage:
    python scripts/list_services.py                    # Résumé des services
    python scripts/list_services.py --detail           # Détails complets
    python scripts/list_services.py --json             # Format JSON brut
    python scripts/list_services.py --search <terme>   # Rechercher un service

Exemples:
    python scripts/list_services.py --search "5G"
    python scripts/list_services.py --search "XR"
    python scripts/list_services.py --search "edge"
        """)


if __name__ == "__main__":
    main()
