from pymongo import MongoClient, ReadPreference
import time

MONGO_URI = 'mongodb://localhost:27017'

def primary_write_then_read():
    client = MongoClient(MONGO_URI)
    db = client.module2
    coll = db.users
    coll.insert_one({'_id': 'u1', 'name': 'mongo_user', 'value': 1})
    print('Wrote to primary')
    # read with primaryPreferred (stronger)
    client_pp = MongoClient(MONGO_URI, read_preference=ReadPreference.PRIMARY_PREFERRED)
    doc = client_pp.module2.users.find_one({'_id': 'u1'})
    print('Read with PRIMARY_PREFERRED:', doc)

def eventual_read_from_secondary():
    # read from secondary (may be stale until replication)
    client = MongoClient(MONGO_URI, read_preference=ReadPreference.SECONDARY_PREFERRED)
    doc = client.module2.users.find_one({'_id': 'u1'})
    print('Read with SECONDARY_PREFERRED (may be None if not replicated yet):', doc)

if __name__ == '__main__':
    primary_write_then_read()
    print('Sleeping briefly to allow replication...')
    time.sleep(2)
    eventual_read_from_secondary()
