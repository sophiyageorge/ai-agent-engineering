from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


# Fictional listing records for learning only.
LISTINGS = {
    "P101": {"owner_id": "owner_1", "monthly_rent": 2400},
    "P102": {"owner_id": "owner_2", "monthly_rent": 3100},
}


class RentProposalInput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    property_id: str = Field(pattern=r"^P\d{3}$")
    proposed_monthly_rent: int = Field(gt=0, le=100_000)
    reason: str = Field(min_length=5, max_length=200)


PROPOSALS = {}


def create_rent_proposal(arguments: dict) -> dict:
    """Validate and save a suggestion. This function never changes a listing."""
    request = RentProposalInput.model_validate(arguments)
    listing = LISTINGS.get(request.property_id)
    if listing is None:
        return {"success": False, "error": "Property not found."}

    proposal_id = str(uuid4())
    proposal = {
        "proposal_id": proposal_id,
        "property_id": request.property_id,
        "owner_id": listing["owner_id"],
        "current_monthly_rent": listing["monthly_rent"],
        "proposed_monthly_rent": request.proposed_monthly_rent,
        "reason": request.reason,
        "status": "pending",
    }
    PROPOSALS[proposal_id] = proposal
    return {"success": True, "proposal": proposal.copy()}


def approve_rent_proposal(proposal_id: str, authenticated_user_id: str) -> dict:
    """Execute only after the property's owner approves the saved proposal."""
    proposal = PROPOSALS.get(proposal_id)
    if proposal is None:
        return {"success": False, "error": "Proposal not found."}
    if authenticated_user_id != proposal["owner_id"]:
        return {"success": False, "error": "Only the property owner can approve this proposal."}
    if proposal["status"] == "executed":
        return {
            "success": True,
            "message": "Proposal was already executed.",
            "monthly_rent": LISTINGS[proposal["property_id"]]["monthly_rent"],
        }

    listing = LISTINGS[proposal["property_id"]]
    if listing["monthly_rent"] != proposal["current_monthly_rent"]:
        return {"success": False, "error": "Listing changed since this proposal was created."}

    listing["monthly_rent"] = proposal["proposed_monthly_rent"]
    proposal["status"] = "executed"
    return {
        "success": True,
        "message": "Owner approved; listing updated.",
        "monthly_rent": listing["monthly_rent"],
    }
