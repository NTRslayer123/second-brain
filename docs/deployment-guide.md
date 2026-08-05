# SecondSelf Production Cloud Deployment Guide (Phase 8)

This guide provides step-by-step instructions for deploying **SecondSelf** to public cloud hosting platforms (**Streamlit Community Cloud** or **Hugging Face Spaces**).

---

## 🚀 Option A: Streamlit Community Cloud (Recommended)

### Step 1: Push Repository to GitHub
Ensure your repository is committed and pushed to GitHub:
```bash
git add .
git commit -m "feat(phase8): prepare production cloud deployment configuration"
git push origin main
```

### Step 2: Connect to Streamlit Community Cloud
1. Navigate to [share.streamlit.io](https://share.streamlit.io/) and log in with your GitHub account.
2. Click **"New App"**.
3. Select your repository: `secondself` (or your repo name).
4. Set **Main file path** to `app.py`.
5. Select **Python version**: `3.10` or `3.11`.

### Step 3: Configure Environment Secrets
1. Expand **Advanced Settings...** -> **Secrets**.
2. Paste your Groq API Key and threshold configuration into the editor:
   ```toml
   GROQ_API_KEY = "gsk_your_actual_groq_api_key_here"
   AUTO_LINK_THRESHOLD = "0.55"
   ```
3. Click **Deploy!**

---

## 🚀 Option B: Hugging Face Spaces (Alternative)

### Step 1: Create a New Space
1. Log in to [huggingface.co](https://huggingface.co/) and click **New Space**.
2. Select **Space SDK**: `Streamlit`.
3. Set Space hardware to **Free CPU basic**.

### Step 2: Upload Code & Set Repository Secrets
1. Push your repository files to the Hugging Face Space repository.
2. Go to **Settings** -> **Variables and Secrets**.
3. Add a New Secret:
   * **Key**: `GROQ_API_KEY`
   * **Value**: `gsk_your_actual_groq_api_key_here`

---

## 🛠️ Cloud Runtime Features & Fallbacks

- **Secret Detection**: `classify.py` and `ask.py` automatically detect `st.secrets["GROQ_API_KEY"]` when running in the cloud.
- **TF-IDF Fallback**: If PyTorch DLL permissions or heavy model downloads are restricted in lightweight cloud runtimes, SecondSelf seamlessly falls back to `scikit-learn` TF-IDF vector retrieval.
- **Persistent Vault**: Notes created during runtime are written to the local `/wiki` directory on the cloud instance.

---

## ⚡ Deployment Verification
Once deployed, verify:
1. The sidebar displays `☁️ Groq API Active`.
2. Ingestion of a test note categorizes payload into PARA directories.
3. **Living Brain** tab renders the interactive 2D/3D force-directed graph.
4. **Ask Your Brain** RAG search returns synthesized answers with citations.
