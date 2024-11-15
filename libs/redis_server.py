from redis import Redis
from config import config


class RedisServer(Redis):
    def __init__(self):
        super().__init__(host=config.REDIS.IP, port=config.REDIS.PORT, password=config.REDIS.PASSWORD, db=0)


redisServer = RedisServer()
