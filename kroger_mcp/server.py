#!/usr/bin/env python3
"""
Kroger MCP Server — Fred Meyer / Kroger grocery integration for Claude.

Provides tools to search stores, find products, compare prices,
and add items to your Kroger/Fred Meyer cart via the Kroger Public API.
"""

import json
import os
import sys
import webbrowser
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from typing import Optional, List, Dict, Any
from enum import Enum

import httpx
from pydantic import BaseModel, Field, ConfigDict
from mcp.server.fastmcp import FastMCP

# ── Constants ──
API_BASE = "https://api.kroger.com/v1"
AUTH_URL = f"{API_BASE}/connect/oauth2/authorize"
TOKEN_URL = f"{API_BASE}/connect/oauth2/token"

CLIENT_ID = os.environ.get("KROGER_CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("KROGER_CLIENT_SECRET", "")
REDIRECT_URI = os.environ.get("KROGER_REDIRECT_URI", "http://localhost:8000/callback")
DEFAULT_ZIP = os.environ.get("KROGER_USER_ZIP_CODE", "97217")

# ── Token State ──
_tokens: Dict[str, Any] = {
    "client_access_token": None,
    "user_access_token": None,
    "user_refresh_token": None,
    "location_id": None,
}

# ── Initialize MCP Server ──
mcp = FastMCP("kroger_mcp")


# ═══════════════════════════════════════════
# Shared Utilities
# ═══════════════════════════════════════════

def _basic_auth_header() -> str:
    import base64
    credentials = f"{CLIENT_ID}:{CLIENT_SECRET}"
    encoded = base64.b64encode(credentials.encode()).decode()
    return f"Basic {encoded}"


def _get_client_token(scope: str = "product.compact") -> str:
    """Get or reuse a client credentials token for read-only API calls."""
    if _tokens["client_access_token"]:
        return _tokens["client_access_token"]

    with httpx.Client(timeout=30.0) as client:
        resp = client.post(
            TOKEN_URL,
            headers={
                "Authorization": _basic_auth_header(),
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={"grant_type": "client_credentials", "scope": scope},
        )
        resp.raise_for_status()
        data = resp.json()
        _tokens["client_access_token"] = data["access_token"]
        return data["access_token"]


def _get_user_token() -> Optional[str]:
    """Return existing user token or None if not authorized yet."""
    return _tokens.get("user_access_token")


def _refresh_user_token() -> Optional[str]:
    """Refresh the user access token using the refresh token."""
    refresh = _tokens.get("user_refresh_token")
    if not refresh:
        return None
    with httpx.Client(timeout=30.0) as client:
        resp = client.post(
            TOKEN_URL,
            headers={
                "Authorization": _basic_auth_header(),
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={"grant_type": "refresh_token", "refresh_token": refresh},
        )
        if resp.status_code == 200:
            data = resp.json()
            _tokens["user_access_token"] = data["access_token"]
            _tokens["user_refresh_token"] = data.get("refresh_token", refresh)
            return data["access_token"]
    return None


def _api_get(endpoint: str, params: Optional[Dict] = None, user_auth: bool = False) -> Dict:
    """Make an authenticated GET request to the Kroger API."""
    token = _get_user_token() if user_auth else _get_client_token()
    if user_auth and not token:
        raise PermissionError("User not authorized. Use kroger_authorize first.")

    with httpx.Client(timeout=30.0) as client:
        resp = client.get(
            f"{API_BASE}/{endpoint}",
            headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
            params=params or {},
        )
        if resp.status_code == 401 and user_auth:
            new_token = _refresh_user_token()
            if new_token:
                resp = client.get(
                    f"{API_BASE}/{endpoint}",
                    headers={"Authorization": f"Bearer {new_token}", "Accept": "application/json"},
                    params=params or {},
                )
            else:
                raise PermissionError("Session expired. Use kroger_authorize to re-authenticate.")
        resp.raise_for_status()
        return resp.json()


def _api_put(endpoint: str, json_body: Dict, user_auth: bool = True) -> Dict:
    """Make an authenticated PUT request to the Kroger API."""
    token = _get_user_token() if user_auth else _get_client_token()
    if user_auth and not token:
        raise PermissionError("User not authorized. Use kroger_authorize first.")

    with httpx.Client(timeout=30.0) as client:
        resp = client.put(
            f"{API_BASE}/{endpoint}",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            json=json_body,
        )
        if resp.status_code == 401 and user_auth:
            new_token = _refresh_user_token()
            if new_token:
                resp = client.put(
                    f"{API_BASE}/{endpoint}",
                    headers={
                        "Authorization": f"Bearer {new_token}",
                        "Content-Type": "application/json",
                        "Accept": "application/json",
                    },
                    json=json_body,
                )
            else:
                raise PermissionError("Session expired. Use kroger_authorize to re-authenticate.")
        resp.raise_for_status()
        if resp.status_code == 204:
            return {"status": "success"}
        return resp.json()


def _handle_error(e: Exception) -> str:
    if isinstance(e, PermissionError):
        return f"Error: {str(e)}"
    if isinstance(e, httpx.HTTPStatusError):
        status = e.response.status_code
        if status == 404:
            return "Error: Resource not found. Check the ID and try again."
        if status == 401:
            return "Error: Authentication failed. Try kroger_authorize to re-authenticate."
        if status == 429:
            return "Error: Rate limit exceeded. Wait a moment and try again."
        return f"Error: API returned status {status}."
    if isinstance(e, httpx.TimeoutException):
        return "Error: Request timed out. Try again."
    return f"Error: {type(e).__name__}: {str(e)}"


def _format_product(p: Dict) -> Dict:
    """Extract useful fields from a Kroger product response."""
    desc = p.get("description", "Unknown")
    brand = p.get("brand", "")
    upc = p.get("upc", "")
    product_id = p.get("productId", "")
    size = ""
    items = p.get("items", [])
    price_regular = None
    price_promo = None
    in_stock = False

    if items:
        item = items[0]
        size = item.get("size", "")
        price_info = item.get("price", {})
        price_regular = price_info.get("regular")
        price_promo = price_info.get("promo")
        fulfillment = item.get("fulfillment", {})
        in_stock = fulfillment.get("curbside", False) or fulfillment.get("delivery", False) or fulfillment.get("inStore", False)

    return {
        "name": desc,
        "brand": brand,
        "upc": upc,
        "productId": product_id,
        "size": size,
        "price": price_promo if price_promo and price_promo > 0 else price_regular,
        "regular_price": price_regular,
        "promo_price": price_promo if price_promo and price_promo > 0 else None,
        "in_stock": in_stock,
    }


# ═══════════════════════════════════════════
# OAuth2 Callback Server
# ═══════════════════════════════════════════

_auth_code_received = threading.Event()
_auth_code_value = None


class _OAuthCallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global _auth_code_value
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        code = params.get("code", [None])[0]

        if code:
            _auth_code_value = code
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(b"<html><body><h2>Authorized! You can close this tab and return to Claude.</h2></body></html>")
            _auth_code_received.set()
        else:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Authorization failed - no code received.")

    def log_message(self, format, *args):
        pass  # Suppress HTTP logs


# ═══════════════════════════════════════════
# Tool Input Models
# ═══════════════════════════════════════════

class SearchLocationInput(BaseModel):
    """Input for searching Kroger/Fred Meyer store locations."""
    model_config = ConfigDict(str_strip_whitespace=True)

    zip_code: Optional[str] = Field(default=None, description="ZIP code to search near (default: 97217 for North Portland)", max_length=10)
    radius: Optional[int] = Field(default=10, description="Search radius in miles", ge=1, le=100)
    limit: Optional[int] = Field(default=5, description="Max number of stores to return", ge=1, le=25)


class SearchProductInput(BaseModel):
    """Input for searching products at a Kroger/Fred Meyer store."""
    model_config = ConfigDict(str_strip_whitespace=True)

    term: str = Field(..., description="Product search term (e.g., 'ground beef', 'organic milk', 'avocado')", min_length=1, max_length=200)
    location_id: Optional[str] = Field(default=None, description="Store location ID. If not provided, uses previously found store.")
    limit: Optional[int] = Field(default=10, description="Max products to return", ge=1, le=50)


class ProductDetailInput(BaseModel):
    """Input for getting detailed product info."""
    model_config = ConfigDict(str_strip_whitespace=True)

    product_id: str = Field(..., description="Kroger product ID to look up")
    location_id: Optional[str] = Field(default=None, description="Store location ID for pricing")


class AddToCartInput(BaseModel):
    """Input for adding items to the Kroger/Fred Meyer cart."""
    model_config = ConfigDict(str_strip_whitespace=True)

    items: List[Dict[str, Any]] = Field(
        ...,
        description="List of items to add. Each item: {'upc': '0001234567890', 'quantity': 1}",
        min_length=1,
        max_length=25,
    )


class AuthorizeInput(BaseModel):
    """Input for initiating OAuth2 user authorization."""
    model_config = ConfigDict(str_strip_whitespace=True)

    scope: Optional[str] = Field(
        default="cart.basic:write profile.compact product.compact",
        description="OAuth2 scopes to request",
    )


# ═══════════════════════════════════════════
# Tools
# ═══════════════════════════════════════════

@mcp.tool(
    name="kroger_authorize",
    annotations={
        "title": "Authorize Kroger Account",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
def kroger_authorize(params: AuthorizeInput) -> str:
    """Initiate OAuth2 authorization to connect your Kroger/Fred Meyer account.

    Opens a browser window for you to log in and authorize cart access.
    This must be done once before using kroger_add_to_cart.

    Returns:
        str: Authorization status message.
    """
    global _auth_code_value
    try:
        _auth_code_value = None
        _auth_code_received.clear()

        parsed = urlparse(REDIRECT_URI)
        port = parsed.port or 8000

        server = HTTPServer(("127.0.0.1", port), _OAuthCallbackHandler)
        server_thread = threading.Thread(target=server.handle_request, daemon=True)
        server_thread.start()

        auth_url = (
            f"{AUTH_URL}?"
            f"scope={params.scope}&"
            f"response_type=code&"
            f"client_id={CLIENT_ID}&"
            f"redirect_uri={REDIRECT_URI}"
        )
        webbrowser.open(auth_url)

        _auth_code_received.wait(timeout=120)
        server.server_close()

        if not _auth_code_value:
            return "Error: Authorization timed out. Please try again."

        with httpx.Client(timeout=30.0) as client:
            resp = client.post(
                TOKEN_URL,
                headers={
                    "Authorization": _basic_auth_header(),
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                data={
                    "grant_type": "authorization_code",
                    "code": _auth_code_value,
                    "redirect_uri": REDIRECT_URI,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            _tokens["user_access_token"] = data["access_token"]
            _tokens["user_refresh_token"] = data.get("refresh_token")

        return "Successfully authorized! You can now search products and add items to your Fred Meyer cart."

    except Exception as e:
        return _handle_error(e)


@mcp.tool(
    name="kroger_search_locations",
    annotations={
        "title": "Search Kroger/Fred Meyer Stores",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
def kroger_search_locations(params: SearchLocationInput) -> str:
    """Search for Kroger-family stores (Fred Meyer, QFC, etc.) near a ZIP code.

    Returns store names, addresses, and location IDs needed for product searches.

    Args:
        params: ZIP code, radius, and limit.

    Returns:
        str: JSON list of nearby stores with location IDs.
    """
    try:
        zip_code = params.zip_code or DEFAULT_ZIP
        data = _api_get("locations", params={
            "filter.zipCode.near": zip_code,
            "filter.radiusInMiles": params.radius,
            "filter.limit": params.limit,
        })

        stores = []
        for loc in data.get("data", []):
            addr = loc.get("address", {})
            store = {
                "locationId": loc.get("locationId"),
                "name": loc.get("name", ""),
                "chain": loc.get("chain", ""),
                "address": f"{addr.get('addressLine1', '')}, {addr.get('city', '')} {addr.get('state', '')} {addr.get('zipCode', '')}",
                "phone": loc.get("phone", ""),
            }
            stores.append(store)

        if stores:
            _tokens["location_id"] = stores[0]["locationId"]

        return json.dumps({"stores": stores, "default_location_id": _tokens.get("location_id")}, indent=2)

    except Exception as e:
        return _handle_error(e)


@mcp.tool(
    name="kroger_search_products",
    annotations={
        "title": "Search Products at Kroger/Fred Meyer",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
def kroger_search_products(params: SearchProductInput) -> str:
    """Search for grocery products at a specific Kroger/Fred Meyer store.

    Returns product names, prices, UPCs, and availability.
    Use kroger_search_locations first to get a location_id if needed.

    Args:
        params: Search term, optional location_id, and limit.

    Returns:
        str: JSON list of matching products with prices and UPCs.
    """
    try:
        location_id = params.location_id or _tokens.get("location_id")
        if not location_id:
            return "Error: No store selected. Use kroger_search_locations first to find a store."

        api_params = {
            "filter.term": params.term,
            "filter.locationId": location_id,
            "filter.limit": params.limit,
            "filter.fulfillment": "csd",  # curbside + delivery + ship
        }

        data = _api_get("products", params=api_params)
        products = [_format_product(p) for p in data.get("data", [])]

        return json.dumps({
            "products": products,
            "count": len(products),
            "search_term": params.term,
            "location_id": location_id,
        }, indent=2)

    except Exception as e:
        return _handle_error(e)


@mcp.tool(
    name="kroger_get_product",
    annotations={
        "title": "Get Product Details",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
def kroger_get_product(params: ProductDetailInput) -> str:
    """Get detailed information about a specific product by its product ID.

    Args:
        params: Product ID and optional location ID for pricing.

    Returns:
        str: JSON product details including price, size, availability.
    """
    try:
        location_id = params.location_id or _tokens.get("location_id")
        api_params = {}
        if location_id:
            api_params["filter.locationId"] = location_id

        data = _api_get(f"products/{params.product_id}", params=api_params)
        product = _format_product(data.get("data", {}))

        return json.dumps(product, indent=2)

    except Exception as e:
        return _handle_error(e)


@mcp.tool(
    name="kroger_add_to_cart",
    annotations={
        "title": "Add Items to Kroger/Fred Meyer Cart",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True,
    },
)
def kroger_add_to_cart(params: AddToCartInput) -> str:
    """Add items to your Kroger/Fred Meyer shopping cart.

    Requires prior authorization via kroger_authorize.
    Each item needs a UPC (from kroger_search_products) and quantity.

    Args:
        params: List of items with UPC and quantity.

    Returns:
        str: Confirmation of items added to cart.
    """
    try:
        body = {"items": []}
        for item in params.items:
            body["items"].append({
                "upc": item["upc"],
                "quantity": item.get("quantity", 1),
            })

        result = _api_put("cart/add", json_body=body)

        return json.dumps({
            "status": "success",
            "items_added": len(params.items),
            "message": f"Added {len(params.items)} item(s) to your Kroger/Fred Meyer cart. Open fredmeyer.com or the app to check out.",
        }, indent=2)

    except Exception as e:
        return _handle_error(e)


@mcp.tool(
    name="kroger_get_profile",
    annotations={
        "title": "Get Kroger/Fred Meyer Profile",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
def kroger_get_profile() -> str:
    """Get your Kroger/Fred Meyer account profile info.

    Requires prior authorization via kroger_authorize.

    Returns:
        str: JSON profile data.
    """
    try:
        data = _api_get("identity/profile", user_auth=True)
        profile = data.get("data", {})
        return json.dumps({
            "id": profile.get("id"),
            "first_name": profile.get("firstName"),
            "last_name": profile.get("lastName"),
        }, indent=2)
    except Exception as e:
        return _handle_error(e)


# ═══════════════════════════════════════════
# Entry Point
# ═══════════════════════════════════════════

if __name__ == "__main__":
    if not CLIENT_ID or not CLIENT_SECRET:
        print("Error: KROGER_CLIENT_ID and KROGER_CLIENT_SECRET environment variables are required.", file=sys.stderr)
        print("Set them in your environment or .env file.", file=sys.stderr)
        sys.exit(1)
    mcp.run()
