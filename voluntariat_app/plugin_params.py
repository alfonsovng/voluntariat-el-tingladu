from .helper import logger

class ParamsManager:

    def __init__(self, app=None):
        self.external_url = None
        self.invitation_token = None
        self.allow_modifications = None
        self.allow_volunteers = None

        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        self.external_url = app.config.get('PARAM_EXTERNAL_URL')
        self.invitation_token = app.config.get('PARAM_INVITATION_TOKEN')
        self.allow_modifications = app.config.get('PARAM_ALLOW_MODIFICATIONS')
        self.allow_volunteers = app.config.get('PARAM_ALLOW_VOLUNTEERS')

        logger.info("PARAM: external_url: " + self.external_url)
        logger.info("PARAM: invitation_token: " + self.invitation_token)
        logger.info("PARAM: allow_modifications: " + str(self.allow_modifications))
        logger.info("PARAM: allow_volunteers: " + str(self.allow_volunteers))
        