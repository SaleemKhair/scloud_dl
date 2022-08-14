from asyncio.log import logger
from dataclasses import dataclass, asdict
import json, os

@dataclass
class Credentials:
    oauth_token: str = None
    client_id: str = None
    user_id: int = None

    @property
    def __dict__(self) -> dict:
        return asdict(self)

    @property
    def json(self) -> str:
        return json.dumps(self.__dict__)

    @property
    def is_valid(self) -> bool:
        return self.user_id and self.client_id and self.oauth_token

    def save_credentials(self, credentials_file: str):
        with open(credentials_file, 'w') as f:
            f.write(self.json)
            f.flush()
    
    @staticmethod
    def load_credentials(credentials_file: str) -> 'Credentials':
        if os.path.exists(credentials_file):
            with open(credentials_file, 'r') as f:
                return Credentials(**json.load(f))

    def update(self, oauth_token: str, client_id: str, user_id: str):
        if oauth_token: self.oauth_token = oauth_token
        if client_id: self.client_id = client_id
        if user_id: self.user_id = user_id


class CredentialsProviderBase:
    def __init__(self):
        self._credentials: Credentials
     
    def credentials(self, user_name):
        pass
        

