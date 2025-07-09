import numpy as np

def encode_id(hour_bucket, article_id):
    i =  np.int64((int(hour_bucket) << 32) | int(article_id))
    return i


def decode_id(composite_id):
    hour_bucket = composite_id >> 32
    article_id = composite_id & 0xFFFFFFFF
    return int(hour_bucket), int(article_id)
