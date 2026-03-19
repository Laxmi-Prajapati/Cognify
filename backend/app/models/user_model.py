import bcrypt


class User:
    def __init__(self, name: str, email: str, password: str, settings: dict = None):
        self.name = name
        self.email = email
        self.password = self._hash_password(password)
        self.settings = settings or {}

    def _hash_password(self, password: str) -> bytes:
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode("utf-8"), salt)

    def verify_password(self, password: str) -> bool:
        return bcrypt.checkpw(password.encode("utf-8"), self.password)

    def to_dict(self):
        return {
            "name": self.name,
            "email": self.email,
            "password": self.password.decode("utf-8"),
            "settings": self.settings,
        }

    @staticmethod
    def from_dict(data):
        user = User(name=data["name"], email=data["email"], password="placeholder")
        user.password = data["password"].encode("utf-8")
        user.settings = data.get("settings", {})
        return user
