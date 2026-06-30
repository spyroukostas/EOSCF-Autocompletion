import pickle

import matplotlib.pyplot as plt
import numpy as np
import requests
from app.recommenders.autocompletion.tag_suggestions.components.filtering.filtering import \
    filtering
from app.recommenders.autocompletion.tag_suggestions.components.tag_candidates import \
    get_tag_candidates
from app.settings import APP_SETTINGS
from tqdm import tqdm


def get_tags_with_score(text_of_service):
    candidate_tags = get_tag_candidates(text_of_service)
    candidate_tags, _ = filtering(candidate_tags, existing_values=None)

    return candidate_tags


def get_textrank_scores_of_all_services():
    print("Requesting all services...", end='')
    base_url = APP_SETTINGS["BACKEND"]["CATALOGUE_API"]["BASE_URL"]
    services = requests.get(f"{base_url}/services?quantity=1000").json()["results"]
    print("Done")

    textrank_scores = []

    for service in tqdm(services):  # Takes ~2min if we disable field value filtering
        text_of_service = service["tagline"] + ". " + service["description"]

        ret = get_tags_with_score(text_of_service)
        textrank_scores.extend(list(ret['score']))

    with open("app/recommenders/autocompletion/tag_suggestions/evaluation/score_normalization/storage"
              "/textrank_scores.pkl", "wb") as f:
        pickle.dump(textrank_scores, f)


def score_analysis():
    with open("app/recommenders/autocompletion/tag_suggestions/evaluation/score_normalization/storage"
              "/textrank_scores.pkl", "rb") as f:
        textrank_scores = pickle.load(f)

    textrank_scores = np.array(textrank_scores)
    print(f"Mean: {np.mean(textrank_scores)} | Std: {np.std(textrank_scores)}")
    print(f"Min: {np.min(textrank_scores)} | Max: {np.max(textrank_scores)}")
    plt.hist(textrank_scores)
    plt.show()


if __name__ == '__main__':
    get_textrank_scores_of_all_services()
    # score_analysis()
