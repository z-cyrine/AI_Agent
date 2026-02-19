# Installation Llama 3.3 (GRATUIT, LOCAL)

## ✅ Pourquoi Llama 3.3 8B pour cette tâche ?

### Votre tâche: Extraction d'intention NL → JSON structuré
- **Llama 3.3 8B**: ⭐ **RECOMMANDÉ** (meilleur rapport qualité/ressources)
  - Excellent pour compréhension NL + extraction structurée
  - **Gratuit, local, offline, aucun coût API**
  - Privacy: données restent sur votre machine
  - **Léger**: Seulement 8 GB RAM requis
  - Qualité largement suffisante pour structured output

- **Llama 3.3 70B**: Alternative si beaucoup de RAM (48+ GB)
  - Qualité légèrement supérieure
  - Mais plus lourd (40 GB téléchargement, 48 GB RAM)

### ❌ Pourquoi PAS Code Llama:
- Code Llama est spécialisé pour **générer du code** (autocomplétion, debugging)
- Pas optimal pour **comprendre** du texte NL et extraire des intentions
- Llama 3.3 > Code Llama pour votre use case

---

## 🚀 Installation (3 étapes)

### 1. Installer Ollama
```powershell
# Télécharger: https://ollama.com/download/windows
# Installer le fichier .exe
# Ollama démarre automatiquement au démarrage de Windows
```

### 2. Télécharger Llama 3.3 8B (RECOMMANDÉ)
```powershell
# Ouvrir PowerShell
ollama pull llama3.3:8b

# Alternative si vous avez beaucoup de RAM (48+ GB):
# ollama pull llama3.3:70b
```

**Taille**: ~4 GB pour 8B, ~40 GB pour 70B  
**RAM requise**: 8 GB pour 8B, 48 GB pour 70B

### 3. Configurer le projet
```powershell
# Créer .env
cp .env.example .env

# .env contient déjà:
# LLM_MODEL=llama3.3:8b
# OLLAMA_BASE_URL=http://localhost:11434
```

---

## ✅ Tester l'installation

```powershell
# Test 1: Ollama fonctionne ?
ollama list

# Test 2: Llama répond ?
ollama run llama3.3:8b "Bonjour"

# Test 3: Agent 1 fonctionne ?
python -c "from agents.agent1_interpreter import IntentInterpreterAgent; agent = IntentInterpreterAgent(); print('✅ OK')"
```

---

## 📊 Performances attendues

| Métrique | Llama 3.3 8B ⭐ | Llama 3.3 70B |
|----------|-----------------|---------------|
| Qualité extraction | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Vitesse (local) | ~0.5-1s/requête | ~2-5s/requête |
| Coût | **GRATUIT** | **GRATUIT** |
| RAM requise | 8 GB | 48 GB |
| Téléchargement | 4 GB | 40 GB |

**Recommandation**: Pour l'extraction d'intention, **llama3.3:8b est largement suffisant**.

---

## 🎯 Utilisation

```python
from agents.agent1_interpreter import IntentInterpreterAgent

# Initialisation (utilise automatiquement Llama 3.3 70B)
agent = IntentInterpreterAgent()

# Extraction d'intention
query = "je veux déployer une base de données postgres avec 16 cores et 32 GB RAM"
intent = agent.interpret(query)

print(intent.json(indent=2))
```

---

## 🔧 Dépannage

### Erreur "Connection refused"
```powershell
# Vérifier qu'Ollama tourne
ollama serve
```

### Erreur "Model not found"
```powershell
# Re-télécharger le modèle
ollama pull llama3.3:8b
```

### Mémoire insuffisante pour 8B
```powershell
# Normalement 8B ne devrait pas poser de problème
# Si encore insuffisant, utiliser la version 1B:
ollama pull llama3.3:1b

# Modifier .env:
# LLM_MODEL=llama3.3:1b
```

---

## 💡 Recommandation
8B via Ollama ⭐  
**Avantages**:
- ✅ **GRATUIT** (aucun coût API)
- ✅ **Local** (pas besoin d'internet)
- ✅ **Privacy** (données sur votre machine)
- ✅ **Léger** (8 GB RAM seulement)
- ✅ **Rapide** (~0.5-1s par requête)
- ✅ **Qualité largement suffisante** pour extraction d'intention

**Si beaucoup de RAM (48+ GB)**:
- Vous pouvez utiliser `llama3.3:70b` pour qualité légèrement supérieure
- Mais pour structured output, 8B est déjà excellent
- ✅ **Qualité excellente** pour extraction d'intention

**Plus besoin de**:
- ❌ GPT-4o (coûteux: ~$0.01-0.03/requête)
- ❌ Claude (coûteux: ~$0.015/1K tokens)
- ❌ Groq (limites API: 30 req/min)
- ❌ Clés API, comptes, facturation

---

## 📚 Ressources

- [Ollama](https://ollama.com)
- [Llama 3.3 Model Card](https://ollama.com/library/llama3.3)
- [LangChain Ollama Integration](https://python.langchain.com/docs/integrations/chat/ollama)
