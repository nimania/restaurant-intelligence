from quality_enrich_base import *  # noqa: F401,F403
from quality_enrich_base import main as base_main


if __name__ == "__main__":
    base_main()
    from semantic_enrich import main as semantic_main
    semantic_main()
