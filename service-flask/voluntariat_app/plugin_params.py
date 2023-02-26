class ParamsManager:

    def __init__(self, app=None):
        self.external_url = None
        self.invitation_token = None
        self.allow_modifications = None

        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        self.external_url = app.config.get('PARAM_EXTERNAL_URL')
        self.invitation_token = app.config.get('PARAM_INVITATION_TOKEN')
        self.allow_modifications = app.config.get('PARAM_ALLOW_MODIFICATIONS')