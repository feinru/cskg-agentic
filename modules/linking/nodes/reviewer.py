from ..state import LinkingState


def reviewer(state: LinkingState) -> LinkingState:
    return {"all_done": True}

