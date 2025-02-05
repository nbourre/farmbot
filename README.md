# Exécuter le serveur
```bash
uvicorn app.main:app --reload
```

# Tester le serveur
## Tester le serveur avec curl
```bash
curl GET "http://127.0.0.1:8000/status"

curl -X POST "http://localhost:8000/toast?message=Hello%20FarmBot"
```

