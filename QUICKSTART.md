# 🚀 Démarrage Rapide - Llama 3.3 70B

## En 3 commandes:

```powershell
# 1. Installer Ollama (télécharger depuis https://ollama.com/download/windows)

# 2. Télécharger Llama 3.3 8B
ollama pull llama3.3:8b

# 3. Tester
python test_llama.py
```

## ✅ C'est tout !

Le projet est déjà configuré pour utiliser **Llama 3.3 8B** (gratuit, local, offline).

**Pourquoi ce modèle ?**
- ✅ **Meilleur pour extraction d'intention** (compréhension NL + structured output)
- ✅ **Gratuit** (aucun coût API)
- ✅ **Local** (offline, privacy)
- ❌ **PAS Code Llama** (spécialisé pour génération de code, pas extraction NL)

## 📖 Documentation complète

- [INSTALLATION_LLAMA.md](INSTALLATION_LLAMA.md) - Guide détaillé
- [README.md](README.md) - Architecture du projet
- [GUIDE_DEMARRAGE.md](GUIDE_DEMARRAGE.md) - Tests et utilisation

## 🎯 Utilisation

```python
from agents.agent1_interpreter import IntentInterpreterAgent

# Initialisation automatique avec Llama 3.3 70B
agent = IntentInterpreterAgent()

# Extraction d'intention
intent = agent.interpret("je veux déployer une base de données postgres")
print(intent.json(indent=2))
```

---

**Note**: Pour la plupart des machines, **llama3.3:8b est suffisant** pour l'extraction d'intention. Si vous avez 48+ GB RAM, vous pouvez utiliser `llama3.3:70b` pour une qualité légèrement supérieure.
