# Configuration API pour Llama 3.3 70B

## Provider: Groq

**Avantages:**
- **Ultra-rapide** (~280 tokens/sec)
- **Quota gratuit généreux** (30 req/min, 6000 tokens/min)
- **Parfait pour développement et production**

**Configuration:**

1. Créer un compte sur [console.groq.com](https://console.groq.com)
2. Générer une clé API dans "API Keys"
3. Dans `.env`:
   ```env
   LLM_PROVIDER=groq
   LLM_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxx
   LLM_MODEL=llama-3.3-70b-versatile
   ```

**Modèles disponibles:**
- `llama-3.3-70b-versatile` (recommandé)
- `llama-3.1-70b-versatile`

---

## Installation

```bash
# 1. Installer langchain-openai
pip install langchain-openai

# 2. Remplir votre .env avec la clé API
# Voir .env.example pour un template

# 3. Tester
python test_quick.py
```

## Vérification de la Configuration

```bash
# Test rapide de connexion
python -c "from agents.agent1_interpreter import IntentInterpreterAgent; agent = IntentInterpreterAgent(); print('Configuration OK')"
```

## Dépannage

**Erreur: "API key not found"**
- Vérifiez que `.env` contient bien `LLM_API_KEY=votre_clé`
- Vérifiez qu'il n'y a pas d'espace avant/après la clé

**Erreur: "Rate limit exceeded"**
- Attendez 1 minute (limite: 30 req/min)
- Réduisez la fréquence des requêtes

**Erreur: "Model not found"**
- Utilisez `llama-3.3-70b-versatile` (nom exact)

## Pourquoi Groq uniquement?

**Pour ce projet IBN:**
- Gratuit (30 req/min)
- Ultra-rapide
- Stable et fiable
- Largement suffisant pour développement ET production

**Note**: Le quota de 30 req/min est parfait pour un système IBN!
