
# backend/api/routes_rankings.py

from fastapi import APIRouter
from services.ranking_service import (
    get_short_term,
    get_long_term,
    get_low_risk,
    get_high_growth
)
from fastapi import Query, Response
import hashlib
import json
from fastapi import APIRouter, Response, Request, Query
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/rankings", tags=["Rankings"])


@router.get("/short-term")
def short_term():
    return get_short_term()


@router.get("/long-term")
def long_term():
    return get_long_term()


@router.get("/low-risk")
def low_risk():
    return get_low_risk()


@router.get("/high-growth")
def high_growth():
    return get_high_growth()


# --------------------------
# RANKING ROUTE
# --------------------------

""" --------This is too repeatative ----------

@router.get("/short-term")
def short_term(
    request: Request,
    response: Response,
    profile: str = "balanced",
    limit: int = Query(20, le=100),
    offset: int = Query(0)
):

    data = get_short_term(profile, limit, offset)

    # Generate stable ETag
    etag = hashlib.md5(
        json.dumps(data, sort_keys=True).encode()
    ).hexdigest()

    # Check client header
    client_etag = request.headers.get("if-none-match")

    if client_etag == etag:
        return Response(status_code=304)

    response.headers["ETag"] = etag
    response.headers["Cache-Control"] = "public, max-age=60"

    return JSONResponse(content=data)


@router.get("/long-term")
def long_term(
    request: Request,
    response: Response,
    profile: str = "balanced",
    limit: int = Query(20, le=100),
    offset: int = Query(0)
):

    data = get_long_term(profile, limit, offset)

    # Generate stable ETag
    etag = hashlib.md5(
        json.dumps(data, sort_keys=True).encode()
    ).hexdigest()

    # Check client header
    client_etag = request.headers.get("if-none-match")

    if client_etag == etag:
        return Response(status_code=304)

    response.headers["ETag"] = etag
    response.headers["Cache-Control"] = "public, max-age=60"

    return JSONResponse(content=data)


@router.get("/low-risk")
def low_risk(
    request: Request,
    response: Response,
    profile: str = "balanced",
    limit: int = Query(20, le=100),
    offset: int = Query(0)
):

    data = get_low_risk(profile, limit, offset)

    # Generate stable ETag
    etag = hashlib.md5(
        json.dumps(data, sort_keys=True).encode()
    ).hexdigest()

    # Check client header
    client_etag = request.headers.get("if-none-match")

    if client_etag == etag:
        return Response(status_code=304)

    response.headers["ETag"] = etag
    response.headers["Cache-Control"] = "public, max-age=60"

    return JSONResponse(content=data)



@router.get("/high-growth")
def high_growth(
    request: Request,
    response: Response,
    profile: str = "balanced",
    limit: int = Query(20, le=100),
    offset: int = Query(0)
):

    data = get_high_growth(profile, limit, offset)

    # Generate stable ETag
    etag = hashlib.md5(
        json.dumps(data, sort_keys=True).encode()
    ).hexdigest()

    # Check client header
    client_etag = request.headers.get("if-none-match")

    if client_etag == etag:
        return Response(status_code=304)

    response.headers["ETag"] = etag
    response.headers["Cache-Control"] = "public, max-age=60"

    return JSONResponse(content=data)

    --------------  """

    # Here is the reusable helper, a shorter version of the above -----

def etag_response(request: Request, response: Response, data):

    etag = hashlib.md5(
        json.dumps(data, sort_keys=True).encode()
    ).hexdigest()

    client_etag = request.headers.get("if-none-match")

    if client_etag == etag:
        return Response(status_code=304)

    response.headers["ETag"] = etag
    response.headers["Cache-Control"] = "public, max-age=60"

    return JSONResponse(content=data)


# --------
# Endpoint
# ---------

@router.get("/short-term")
def short_term(request: Request, response: Response, ...):

    data = get_short_term(profile, limit, offset)
    return etag_response(request, response, data)


