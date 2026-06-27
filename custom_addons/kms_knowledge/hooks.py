from .seed_more_knowledge_articles import seed_extra_knowledge_articles


def post_init_hook(env):
    seed_extra_knowledge_articles(env, commit=False)
