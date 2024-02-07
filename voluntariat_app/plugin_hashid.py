from hashids import Hashids
import sys, time, random, string
from werkzeug.utils import secure_filename
from .helper import get_timestamp

class HashidManager:

    def __init__(self, app=None):
        self.user_hashid_generator = None
        self.task_hashid_generator = None
        self.token_generator = None
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        salt = app.config.get('HASHID_SALT')
        self.user_hashid_generator = Hashids(salt=salt,min_length=8)
        self.task_hashid_generator = Hashids(salt=salt[::-1],min_length=10) #salt reversed
        self.token_generator = Hashids(salt=self.create_password(),min_length=42)

    def get_user_id_from_hashid(self, hashid):
        maybe_id = self.user_hashid_generator.decode(hashid)
        if len(maybe_id) > 0:
            return maybe_id[0]
        return None

    def get_user_hashid(self, user_id):
        return self.user_hashid_generator.encode(user_id)

    def get_task_id_from_hashid(self, hashid):
        maybe_id = self.task_hashid_generator.decode(hashid)
        if len(maybe_id) > 0:
            return maybe_id[0]
        return None

    def get_task_hashid(self, task_id):
        return self.task_hashid_generator.encode(task_id)

    def create_token(self, id):
        t = int(time.time()*1000)
        r = int(random.random()*sys.maxsize)
        return self.token_generator.encode(id, t, r)

    def create_unique_file_name(self,user_id,name,extension):
        prefix = secure_filename(name)
        hash = self.task_hashid_generator.encode(int(random.random()*sys.maxsize))
        str_date_time = get_timestamp()
        return str_date_time + "_" + hash + "_" + str(user_id) + "_" + prefix + extension

    def create_password(self):
        return ''.join(random.choice(string.printable) for i in range(32))