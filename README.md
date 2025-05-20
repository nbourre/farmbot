# Exécuter le serveur
```bash
cd backend
uvicorn app.main:app --reload
```

# Tester le serveur
## Tester le serveur avec linux
```bash
npm install axios


curl -X POST "http://localhost:8000/toast?message=Hello%20FarmBot"
```

## Tester le serveur avec PowerShell
```powershell
curl "http://127.0.0.1:8000/status"

iwr "http://localhost:8000/toast?message=Hello FarmBot" -Method POST
```
