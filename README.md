# KrishiMitra (full working version)

## Run on your computer (VS Code terminal)
    python -m venv .venv
    .venv\Scripts\activate          # Mac/Linux: source .venv/bin/activate
    pip install -r requirements.txt
    set ANTHROPIC_API_KEY=your-key   # Mac/Linux: export ANTHROPIC_API_KEY=your-key
    uvicorn main:app --reload
Open http://127.0.0.1:8000

## Deploy free on Render (get a public link)
1. Put this folder on GitHub (new repo, upload all files; do NOT upload .env).
2. render.com -> New -> Web Service -> connect the repo.
3. Build command:  pip install -r requirements.txt
   Start command:  uvicorn main:app --host 0.0.0.0 --port $PORT
4. Environment -> add ANTHROPIC_API_KEY = your key.
5. Deploy. Your link looks like https://krishimitra.onrender.com
Free plan sleeps after idle time: open the link once a few minutes before your demo.
Set a monthly spend limit on your API account, since the link is public.
