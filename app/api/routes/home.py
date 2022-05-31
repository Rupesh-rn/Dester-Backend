import random
import time
from typing import Dict, Union

from app import logger
#from diskcache import Cache
from fastapi import APIRouter

router = APIRouter(
    # dependencies=[Depends(get_token_header)],
    prefix="/home",
    responses={404: {"description": "Not found"}},
    tags=["internals"],
)

data_cap_limit = 15

#cache = Cache(directory="cache", timeout=60 * 10)
# This current implementation is not optimal since it just straight up deletes all the cache.
# Which forces the script to regenerate the cache causing delay to user-end.
# A better way is to run a cron job to update the cache every 'x' seconds and provide the data
# which reduces any delay, I haven't implemented it cuz I plan to use asyncio here but the code itself is not compatible with asyncio yet.


@router.get("", response_model=Dict[str, Union[str, int, float, bool, None, dict]])
def home() -> Dict[str, str]:
    start = time.perf_counter()
    #data = cache.get("home_route_data")
    if True:  # if not data
        logger.debug("Generating new data for home route")
        from main import mongo

        random.seed(100)
        categories_data = []
        carousel_data = []
        most_popular_movies_data = []
        most_popular_series_data = []
        top_rated_series_data = []
        top_rated_movies_data = []
        newly_added_movies_data = []
        newly_added_episodes_data = []
        unwanted_keys = {
            "_id": 0,
            "cast": 0,
            "seasons": 0,
            "file_name": 0,
            "subtitles": 0,
            "external_ids": 0,
            "collection": 0,
            "homepage": 0,
            "last_episode_to_air": 0,
            "next_episode_to_air": 0,
        }
        for category in mongo.categories:
            category_col = mongo.metadata[category["id"]]
            if True:
                sorted_popularity_data = list(category_col.aggregate([
                    {
                        '$sort': {
                            'popularity': -1
                        }
                    }, {
                        '$limit': data_cap_limit
                    }, {
                        '$project': unwanted_keys
                    }]
                ))
                category["metadata"] = sorted_popularity_data
                categories_data.append(category)
                carousel_data.extend(sorted_popularity_data[:3])

                sorted_top_rated_data = category_col.aggregate([
                    {
                        '$sort': {
                            'rating': -1
                        }
                    }, {
                        '$limit': data_cap_limit
                    }, {
                        '$project': unwanted_keys
                    }]
                )

                if category["type"] == "movies":
                    most_popular_movies_data.extend(sorted_popularity_data)
                    top_rated_movies_data.extend(sorted_top_rated_data)
                    sorted_newly_added_data = category_col.aggregate([
                        {
                            '$sort': {
                                'modified_time': -1
                            }
                        }, {
                            '$limit': data_cap_limit
                        }, {
                            '$project': unwanted_keys
                        }]
                    )
                    newly_added_movies_data.extend(sorted_newly_added_data)
                else:
                    most_popular_series_data.extend(sorted_popularity_data)
                    top_rated_series_data.extend(sorted_top_rated_data)
                    sorted_newly_added_data = category_col.aggregate([
                        {
                            '$sort': {
                                'seasons.episodes.modified_time': -1
                            }
                        }, {
                            '$limit': data_cap_limit
                        }, {
                            '$project': unwanted_keys
                        }]
                    )
                    newly_added_episodes_data.extend(sorted_newly_added_data)
        carousel_data = sorted(
            carousel_data, key=lambda k: k["popularity"], reverse=True
        )
        most_popular_movies_data = sorted(
            most_popular_movies_data, key=lambda k: k["popularity"], reverse=True
        )
        most_popular_series_data = sorted(
            most_popular_series_data, key=lambda k: k["popularity"], reverse=True
        )
        top_rated_movies_data = sorted(
            top_rated_movies_data, key=lambda k: k["rating"], reverse=True
        )
        top_rated_series_data = sorted(
            top_rated_series_data, key=lambda k: k["rating"], reverse=True
        )
        newly_added_movies_data = sorted(
            newly_added_movies_data, key=lambda k: k["modified_time"], reverse=True
        )
        # cache.set("home_route_data", dict(categories_data=categories_data, carousel_data=carousel_data, top_rated_series_data=top_rated_series_data,
        #          top_rated_movies_data=top_rated_movies_data, newly_added_movies_data=newly_added_movies_data, newly_added_episodes_data=newly_added_episodes_data))
    else:
        logger.debug("Using cached data")
        categories_data = data.get("categories_data")
        carousel_data = data.get("carousel_data")
        top_rated_movies_data = data.get("top_rated_movies_data")
        top_rated_series_data = data.get("top_rated_series_data")
        newly_added_episodes_data = data.get("newly_added_episodes_data")
        newly_added_movies_data = data.get("newly_added_movies_data")
    end = time.perf_counter()
    return {
        "ok": True,
        "message": "success",
        "data": {
            "categories": categories_data,
            "carousel": carousel_data,
            "most_popular_movies": most_popular_movies_data,
            "most_popular_series": most_popular_series_data,
            "top_rated_movies": top_rated_movies_data,
            "top_rated_series": top_rated_series_data,
            "newly_added_movies": newly_added_movies_data,
            "newly_added_episodes": newly_added_episodes_data,
        },
        "time_taken": end - start,
    }
