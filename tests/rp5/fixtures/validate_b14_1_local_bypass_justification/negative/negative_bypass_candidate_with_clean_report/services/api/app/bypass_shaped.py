from synthetic.fixture import get_public_demo_exposure_flag, recruiter_auth_dependency
from fastapi import Depends


def attach_routes(app):
    if not get_public_demo_exposure_flag():
        # Synthetic local/dev bypass: skip recruiter dependency when flag is false.
        app.add_api_route(
            "/demo/health",
            lambda: {"status": "ok"},
        )
    else:
        app.add_api_route(
            "/demo/health",
            lambda: {"status": "ok"},
            dependencies=[Depends(recruiter_auth_dependency)],
        )
