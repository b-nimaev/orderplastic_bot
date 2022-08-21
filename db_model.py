from abc import ABC, abstractmethod
from random import choice
import string


class DbWorker(ABC):
    # def __init__(self, message):
    #     self.db = None
    #     self.key = None
    #     self.default_data = None
    #     self.db_object = None

    def __setitem__(self, name, value):
        self.db_object[name] = value
        self.save()

    def __getitem__(self, name):
        if name in self.db_object.keys():
            return self.db_object[name]
        else:
            try:
                return self.default_data[name]
            except:
                raise Exception("Error get {}".format(name))

    def __eq__(self, other):
        return self.key == other.key

    def find_or_create(self):
        self.db_object = self.db.find_one(self.key)
        if not self.db_object:
            self.create_obj()

    def create_obj(self):
        self.db.insert_one(self.default_data)
        self.db_object = self.db.find_one(self.key)

    def save(self):
        self.db.save(self.db_object)




