# MAAS Practice — Streamlit Prototype

**P**atient **R**esponses **A**dapted to **C**linical **T**echnique **i**n **C**alibrated **E**ncounters

---

## Quick Start (Local)

```bash
# 1. Install dependencies
pip install streamlit anthropic

# 2. Set API key
export ANTHROPIC_API_KEY="your-key-here"

# 3. Run app
streamlit run app.py
```

Opens at `http://localhost:8501`

---

## Deploy to Streamlit Cloud

### Step 1: Push to GitHub

```bash
git init
git add .
git commit -m "MAAS Practice prototype"
git remote add origin https://github.com/YOUR-USERNAME/maas-practice.git
git push -u origin main
```

### Step 2: Deploy

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Sign in with GitHub
3. Click "New app"
4. Select repository → branch → `app.py`
5. Click "Deploy"

### Step 3: Add API Key

1. In Streamlit Cloud → your app → Settings → Secrets
2. Add:
```toml
ANTHROPIC_API_KEY = "sk-ant-your-key-here"
```
3. Save

### Step 4: Share

Share the URL with testers:
```
https://YOUR-USERNAME-maas-practice-xxxxx.streamlit.app
```

---

## File Structure

```
streamlit-app/
├── app.py              # Main application
├── config.py           # Settings
├── requirements.txt    # Dependencies
├── .gitignore          # Git ignore rules
└── data/
    ├── cases/          # Patient case JSON files
    │   ├── mr-lee-chest-pain.json
    │   └── marcus-back-pain.json
    └── prompts/        # System prompts
        ├── patient-simulation.txt
        └── feedback-generation.txt
```

---

## Features

- **Case selection** — Choose from available patient cases
- **Chat interface** — Interview simulated patient
- **Realistic responses** — Patient responds based on your technique
- **MAAS feedback** — Performance mapped to MAAS scales
- **Transcript download** — Save consultation for review

---

## Adding New Cases

1. Create JSON file following `mr-lee-chest-pain.json` structure
2. Save to `data/cases/`
3. Restart app — new case appears automatically

---

## Cost Estimate

| Usage | API Cost |
|-------|----------|
| 1 full case session | ~$0.50-1.00 |
| 15 testers × 3 cases | ~$25-50 |

Monitor usage at [console.anthropic.com](https://console.anthropic.com)

---

*MAAS Practice | Pilot Testing Prototype*
