SOLUTIONS = []


def register_solution(meta: dict):
    """Register a solution in the hub.

    meta must contain: name, slug, description, icon
    meta may contain:  pages (list of {name, path})
    """
    SOLUTIONS.append(meta)


def get_solutions():
    return SOLUTIONS
