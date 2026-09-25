import os

from dotenv import load_dotenv

load_dotenv()

# "development" enables POST /auth/dev-login. Anything else (default) disables it.
ENV = os.getenv("ENV", "production")
IS_DEV = ENV == "development"

# Web OAuth client ID from Google Cloud Console. Google ID tokens must be issued for this.
GOOGLE_WEB_CLIENT_ID = os.getenv("GOOGLE_WEB_CLIENT_ID", "")

# Secret used to sign OUR access tokens. Generate with: openssl rand -hex 32
JWT_SECRET = os.getenv("JWT_SECRET", "")
if len(JWT_SECRET) < 32:
    raise RuntimeError(
        "JWT_SECRET is missing or too short. Add a long random value to .env "
        "(generate one with: openssl rand -hex 32)."
    )

ACCESS_TOKEN_MINUTES = int(os.getenv("ACCESS_TOKEN_MINUTES", "60"))
