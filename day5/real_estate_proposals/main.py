from workflow import (
    LISTINGS,
    approve_rent_proposal,
    create_rent_proposal,
)


if __name__ == "__main__":
    proposal_result = create_rent_proposal({
        "property_id": "P101",
        "proposed_monthly_rent": 2500,
        "reason": "Similar nearby homes rent for more.",
    })
    proposal = proposal_result["proposal"]
    proposal_id = proposal["proposal_id"]

    print("AI proposal:", proposal)
    print("Rent before owner approval:", LISTINGS["P101"]["monthly_rent"])
    print("Owner approval:", approve_rent_proposal(proposal_id, "owner_1"))
    print("Rent after owner approval:", LISTINGS["P101"]["monthly_rent"])
