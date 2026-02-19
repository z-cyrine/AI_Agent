# Configuration API pour Llama 3.3 70B

## Providers Supportés

### Option 1: Groq (⭐ RECOMMANDÉ - Le plus rapide)

**Avantages:**
- ⚡ **Ultra-rapide** (~280 tokens/sec)
- 🆓 **Quota gratuit généreux** (30 req/min, 6000 tokens/min)
- 🎯 **Parfait pour développement**

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

### Option 2: Together AI (Bonne alternative)

**Avantages:**
- 💰 **5$ de crédits gratuits** à l'inscription
- 🚀 **Rapide** (~100-150 tokens/sec)
- 📚 **Nombreux modèles disponibles**

**Configuration:**
1. Créer un compte sur [api.together.xyz](https://api.together.xyz)
2. Récupérer votre clé API dans "API Keys"
3. Dans `.env`:
   ```env
   LLM_PROVIDER=together
   LLM_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   LLM_MODEL=meta-llama/Meta-Llama-3.3-70B-Instruct-Turbo
   ```

**Modèles disponibles:**
- `meta-llama/Meta-Llama-3.3-70B-Instruct-Turbo` (recommandé)
- `meta-llama/Llama-3.1-70B-Instruct-Turbo`

---

### Option 3: Fireworks AI

**Configuration:**
1. Compte sur [fireworks.ai](https://fireworks.ai)
2. Dans `.env`:
   ```env
   LLM_PROVIDER=fireworks
   LLM_API_KEY=fw_xxxxxxxxxxxxxxxxxxxxx
   LLM_MODEL=accounts/fireworks/models/llama-v3p3-70b-instruct
   ```

---

### Option 4: Replicate

**Configuration:**
1. Compte sur [replicate.com](https://replicate.com)
2. Dans `.env`:
   ```env
   LLM_PROVIDER=replicate
   LLM_API_KEY=r8_xxxxxxxxxxxxxxxxxxxxx
   LLM_MODEL=meta/meta-llama-3.3-70b-instruct
   ```

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

## Comparaison des Providers

| Provider   | Vitesse       | Quota Gratuit        | Prix (après quota)     | Recommandation      |
|------------|---------------|----------------------|------------------------|---------------------|
| Groq       | ⚡⚡⚡ Ultra   | 30 req/min gratuit   | Pas de pricing public  | 🏆 **Développement** |
| Together   | ⚡⚡ Rapide   | 5$ gratuits          | ~0.9$/M tokens         | Production          |
| Fireworks  | ⚡⚡ Rapide   | Crédits limités      | ~0.9$/M tokens         | Alternative         |
| Replicate  | ⚡ Moyen      | Pay-per-use          | ~3-4$/M tokens         | Pas recommandé      |

## Vérification de la Configuration

```bash
# Test rapide de connexion
python -c "from agents.agent1_interpreter import IntentInterpreterAgent; agent = IntentInterpreterAgent(); print('✅ Configuration OK')"
```

## Dépannage

**Erreur: "API key not found"**
- Vérifiez que `.env` contient bien `LLM_API_KEY=votre_clé`
- Vérifiez qu'il n'y a pas d'espace avant/après la clé

**Erreur: "Rate limit exceeded"**
- Groq: Attendez 1 minute (limite: 30 req/min)
- Together: Vérifiez vos crédits restants

**Erreur: "Model not found"**
- Vérifiez le nom du modèle selon votre provider
- Voir les tableaux ci-dessus pour les noms exacts

## 🎯 Recommandation Finale

**Pour ce projet IBN:**
1. **Développement/Tests**: Groq (gratuit, rapide, parfait)
2. **Production**: Together AI (crédits gratuits puis ~0.9$/M tokens)

**Note**: Le quota gratuit de Groq (30 req/min) est largement suffisant pour tester et développer votre système IBN!
