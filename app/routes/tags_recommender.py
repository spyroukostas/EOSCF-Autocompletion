from typing import List, Optional

from app.recommenders.autocompletion.tag_suggestions.suggestion_generation import \
    get_suggestions_for_tags
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix='/v1')


class Request(BaseModel):
    resource_type: str = "service"

    resource: dict

    maximum_suggestions: int

    existing_values: Optional[List[str]] = None

    class Config:
        schema_extra = {
            "example": {
                "resource_type": "service",
                "resource": {
                    "description": "The Social Sciences and Humanities Open Marketplace, built as part of the Social "
                                   "Sciences and Humanities Open Cloud project (SSHOC), is a discovery portal which "
                                   "pools and contextualises resources for Social Sciences and Humanities research "
                                   "communities: - tools & services, - training materials, - datasets, - publications "
                                   "and - workflows. The Marketplace highlights and showcases solutions and research "
                                   "practices for every step of the SSH research data life cycle.",
                    "tagline": "Discover new and contextualised resources for your research in Social Sciences and "
                               "Humanities: tools, services, training materials, workflows and datasets."
                },
                "maximum_suggestions": 5,
            }
        }


@router.post(
    "/tags_recommendation/suggest",
    response_model=List[str],
    tags=["tags auto-completion"]
)
def tags_recommendations(request: Request):
    tags, _ = get_suggestions_for_tags(service_attributes=request.resource,
                                       existing_values=request.existing_values,
                                       max_num=request.maximum_suggestions,
                                       resource_type=request.resource_type)
    return tags
