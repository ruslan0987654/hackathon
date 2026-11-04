"""İlk quraşdırma: .env faylını yaradır və təsadüfi API açarları təyin edir (mövcud .env-ə toxunmur)."""
import secrets
from pathlib import Path

root = Path(__file__).resolve().parents[1]
env = root / ".env"
if env.exists():
    print(".env artıq mövcuddur, dəyişdirilmədi.")
else:
    text = (root / ".env.example").read_text(encoding="utf-8")
    text = text.replace("API_KEY=CHANGE_ME_long_random_string", f"API_KEY={secrets.token_urlsafe(32)}")
    text = text.replace("ADMIN_API_KEY=", f"ADMIN_API_KEY={secrets.token_urlsafe(32)}", 1)
    env.write_text(text, encoding="utf-8")
    print(".env yaradıldı (təsadüfi API_KEY və ADMIN_API_KEY ilə).")
