import logging
from typing import Dict, List, Optional

from app.exceptions import MissingAttribute, MissingStructure
from app.recommenders.autocompletion.autocompletion import \
    get_auto_completion_suggestions
from app.recommenders.autocompletion.enumerated_field_suggestions.evaluation.evaluation import \
    evaluation
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix='/v1')


class Request(BaseModel):
    resource_type: str = "service"

    resource: dict

    # Fields to suggest options
    fields_to_suggest: List[str]

    # The maximum suggestions per field
    maximum_suggestions: int

    existing_fields_values: Optional[Dict[str, List[str]]] = {}

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
                "fields_to_suggest": ["categories", "scientific_domains", "tags"],
                "maximum_suggestions": 3,
                "existing_fields_values": {
                    "categories": ["subcategory-access_physical_and_eInfrastructures-compute-job_execution",
                                   "subcategory-access_physical_and_eInfrastructures-compute-other"],
                    "scientific_domains": ["scientific_subdomain-agricultural_sciences-other_agricultural_sciences"]
                }
            }
        }


class FieldSuggestions(BaseModel):
    field_name: str
    suggestions: List[str]


@router.post(
    "/auto_completion/suggest",
    response_model=List[FieldSuggestions],
    tags=["fields auto-completion"]
)
def auto_completion_suggestions(request: Request):
    """
    **Create auto-complete suggestions for the requested fields**

    Based on the new service's filled fields given as input, we recommend auto-complete suggestions for the requested
    fields.

    - **resource**: the filled fields of the new partial created resource
    - **fields_to_suggest**: the fields for which suggestion will be generated
    - **maximum_suggestions**: the maximum number of suggestions per field
    - **existing_fields_values**: the existing values for each suggested field

    **Returns** a list with the name and the suggestions for every requested field
    """
    try:
        return [
            FieldSuggestions(field_name=field, suggestions=suggestions)
            for field, suggestions in get_auto_completion_suggestions(
                request.resource, request.fields_to_suggest,
                request.maximum_suggestions,
                request.existing_fields_values,
                resource_type=request.resource_type).items()
        ]
    except (MissingStructure, MissingAttribute) as e:
        logger.error((str(e)))
        raise HTTPException(status_code=404, detail=str(e))


class FieldCompletionEvaluation(BaseModel):
    field: str
    results: dict


@router.post(
    "/auto_completion/evaluate_enumerated_fields",
    response_model=List[FieldCompletionEvaluation],
    tags=["fields auto-completion"]
)
def evaluate_enumerated_fields():
    try:
        return [FieldCompletionEvaluation(field=field, results=results)
                for field, results in evaluation().items()]
    except MissingStructure as e:
        logger.error(str(e))
        raise HTTPException(status_code=404, detail=str(e))
