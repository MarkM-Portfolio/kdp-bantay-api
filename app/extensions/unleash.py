from kumuniverse.unleash import UnleashAdmin, UnleashClient


class Unleash:
    def __init__(self):
        self.app = None
        self.unleash_admin = None
        self.unleash_client = None

    def init_app(self, app):
        self.app = app
        self.create_admin_conn()
        self.create_client_conn()

    def create_admin_conn(self):
        unleash_auth_token = self.app.config["UNLEASH_ADMIN_SECRET"]
        unleash_address = self.app.config["UNLEASH_ADDRESS"]
        self.unleash_admin = UnleashAdmin(unleash_address, unleash_auth_token)
        return self.unleash_admin

    def create_client_conn(self):
        unleash_auth_token = self.app.config["UNLEASH_ADMIN_SECRET"]
        unleash_address = self.app.config["UNLEASH_ADDRESS"]
        unleash_app_name = self.app.config["UNLEASH_APP_NAME"]
        self.unleash_client = UnleashClient(
            unleash_address, unleash_auth_token, unleash_app_name, refresh_interval=5
        )
        return self.unleash_client

    def get_unleash_admin(self):
        if not self.unleash_admin:
            return self.create_admin_conn()
        return self.unleash_admin

    def get_unleash_client(self):
        if not self.unleash_client:
            return self.create_client_conn()
        return self.unleash_client
