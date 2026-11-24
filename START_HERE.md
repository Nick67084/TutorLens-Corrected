# TutorLens corrected source package

Extract into a NEW folder. Do not overwrite the old project or copy its data directory: old vector chunks contain incorrect page labels. This package excludes all uploaded PDFs and databases. Your original files remain untouched.

Windows PowerShell, in the extracted folder:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
```
Set OLLAMA_MODEL in .env to the installed model from `ollama list`. Start Ollama, then:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m streamlit run main.py
```
Register a fresh test account and upload your original lecture PDF again. Existing accounts, marks and chats are not migrated. Keep the old project as backup. Text extraction does not read image-only diagrams; architecture answers may be partial. Citation warnings are not factual verification. Both modes still use a model-based relevance gate. Quiz redaction is heuristic, not a guarantee.

To publish separately, use a NEW empty private repository on GitHub. In the extracted folder (no .git included):

```powershell
git init -b main
git add .
git status
git commit -m "TutorLens corrected source"
git remote add origin https://github.com/YOUR_USERNAME/YOUR_NEW_REPOSITORY.git
git remote -v
git push -u origin main
```
Replace the URL with the actual new repository URL. Verify it before pushing. Never force push. Existing repository history may contain uploaded PDFs; removing them from this package does not remove them from GitHub.
