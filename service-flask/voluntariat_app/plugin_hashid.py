from hashids import Hashids
import sys, time, random, string
from datetime import datetime
from werkzeug.utils import secure_filename

class HashidManager:

    def __init__(self, app=None):
        self.hashid_generator = None
        self.token_generator = None
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        salt = app.config.get('HASHID_SALT')
        self.hashid_generator = Hashids(salt=salt,min_length=8)
        self.token_generator = Hashids(salt=self.create_password(),min_length=42)

    def get_id_from_hashid(self, hashid):
        maybe_id = self.hashid_generator.decode(hashid)
        if len(maybe_id) > 0:
            return maybe_id[0]
        return None

    def get_hashid(self, id):
        return self.hashid_generator.encode(id)

    def create_token(self, id):
        t = int(time.time()*1000)
        r = int(random.random()*sys.maxsize)
        return self.token_generator.encode(id, t, r)

    def create_unique_file_name(self,id,name,extension):
        prefix = secure_filename(name)
        hash = self.hashid_generator.encode(id, int(random.random()*sys.maxsize))
        str_date_time = datetime.fromtimestamp(time.time()).strftime("%Y%m%d%H%M%S")
        return str_date_time + "_" + prefix + "_" + hash + extension

    def create_password(self):
        return ''.join(random.choice(string.printable) for i in range(32))