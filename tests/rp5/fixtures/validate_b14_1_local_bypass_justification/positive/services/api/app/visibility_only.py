from synthetic.fixture import get_public_demo_exposure_flag


def build_app():
    if get_public_demo_exposure_flag():
        return FastAPI(
            title="synthetic",
            openapi_url=None,
            docs_url=None,
            redoc_url=None,
        )
    return FastAPI(title="synthetic")
