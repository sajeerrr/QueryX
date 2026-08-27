from functools import lru_cache


@lru_cache(maxsize=512)
def cached_rewrite(fn, question):

    return fn(question)