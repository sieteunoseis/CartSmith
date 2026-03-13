# Grocery Shopping Agent — Full Project Plan

## Overview
A self-hosted, open-source grocery shopping AI agent — like Pantry Pilot, but for Kroger/Fred Meyer and fully under your control. It scans live sale prices, matches deals to your personal recipe database, generates meal plans around what's cheap this week, and builds a pickup cart — all through a React web UI backed by a FastAPI server. Supports Claude API and OpenRouter for LLM flexibility.

**Core idea:** Most meal planning apps start with "what do you want to eat?" and then find ingredients. This agent starts with "what's on sale?" and figures out what to cook. That's a fundamentally different — and cheaper — approach.

**Distribution model:** Open-source Docker container. Users clone the repo, add their own Kroger API credentials and LLM API key, `docker compose up`, and they're running. No SaaS, no accounts, no data leaves their machine.

## Architecture

```
┌─────────────────────────────────────────────────┐
│                 React Frontend                   │
│         (Vite + TailwindCSS + React Router)      │
│                                                   │
│  ┌──────────┐ ┌──────────┐ ┌────────────────┐   │
│  │ Recipes   │ │ Sales    │ │ Meal Planner   │   │
│  │ Browser   │ │ Scanner  │ │ + Cart Builder │   │
│  └──────────┘ └──────────┘ └────────────────┘   │
│  ┌──────────┐ ┌──────────┐ ┌────────────────┐   │
│  │ Pantry   │ │ Settings │ │ Price History   │   │
│  │ Manager  │ │          │ │ Dashboard       │   │
│  └──────────┘ └──────────┘ └────────────────┘   │
└──────────────────┬──────────────────────────────┘
                   │ HTTP/REST
┌──────────────────▼──────────────────────────────┐
│               FastAPI Backend                     │
│                                                   │
│  ┌──────────────────────────────────────────┐    │
│  │            API Routers                    │    │
│  │  /recipes  /sales  /cart  /agent  /auth   │    │
│  │  /staples  /settings  /prices             │    │
│  └──────────────────┬───────────────────────┘    │
│                     │                             │
│  ┌─────────────┐ ┌──▼──────────┐ ┌───────────┐  │
│  │ Kroger      │ │ Agent       │ │ LLM       │  │
│  │ Service     │ │ Orchestrator│ │ Router    │  │
│  │ (API calls) │ │ (workflow)  │ │ (Claude/  │  │
│  │             │ │             │ │ OpenRouter)│  │
│  └─────────────┘ └─────────────┘ └───────────┘  │
│                     │                             │
│  ┌──────────────────▼───────────────────────┐    │
│  │            SQLite Database                │    │
│  │  recipes | staples | kroger_tokens        │    │
│  │  price_history | meal_plans | settings    │    │
│  └──────────────────────────────────────────┘    │
└──────────────────────────────────────────────────┘
```

## Tech Stack

| Layer | Tech | Why |
|-------|------|-----|
| Frontend | React 18 + Vite + TailwindCSS | Fast dev, modern, lightweight |
| Backend | FastAPI + Python 3.12 | Async, great for API orchestration |
| Database | SQLite (via SQLAlchemy + Alembic) | Zero ops, file-based, plenty for single user |
| LLM | Anthropic SDK + OpenRouter (httpx) | Dual provider support |
| HTTP Client | httpx | Async Kroger API calls |
| Auth | Kroger OAuth2 (refresh token stored in DB) | Persistent auth across restarts |
| Containerization | Docker Compose | Single command startup |

## Project Structure

```
grocery-agent/
├── docker-compose.yml
├── .env.example
├── README.md
│
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── alembic.ini
│   ├── migrations/
│   │   └── versions/
│   │
│   └── app/
│       ├── main.py                  # FastAPI app entry
│       ├── config.py                # Settings (env vars)
│       ├── database.py              # SQLAlchemy engine + session
│       │
│       ├── models/
│       │   ├── recipe.py            # Recipe, Ingredient, Tag
│       │   ├── staple.py            # PantryStaple
│       │   ├── kroger.py            # KrogerToken, PriceHistory
│       │   ├── meal_plan.py         # MealPlan, MealPlanRecipe
│       │   └── settings.py          # UserSettings
│       │
│       ├── routers/
│       │   ├── recipes.py           # CRUD recipes
│       │   ├── staples.py           # CRUD pantry staples
│       │   ├── sales.py             # Scan FM sales
│       │   ├── cart.py              # Kroger cart operations
│       │   ├── agent.py             # Run agent workflow
│       │   ├── auth.py              # Kroger OAuth flow
│       │   ├── prices.py            # Price history
│       │   └── settings.py          # App settings (LLM provider, store, etc.)
│       │
│       └── services/
│           ├── kroger.py            # Kroger API client (from our MCP work)
│           ├── llm.py               # LLM router (Claude / OpenRouter)
│           ├── agent.py             # Agent orchestrator
│           ├── recipe_matcher.py    # Match sales → recipes
│           └── price_tracker.py     # Track prices over time
│
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   ├── index.html
│   │
│   └── src/
│       ├── main.jsx
│       ├── App.jsx
│       ├── api/
│       │   └── client.js            # Axios/fetch wrapper
│       │
│       ├── pages/
│       │   ├── Recipes.jsx          # Browse/search/add recipes
│       │   ├── RecipeDetail.jsx     # Single recipe view + edit
│       │   ├── Sales.jsx            # Current FM sale items
│       │   ├── MealPlanner.jsx      # Weekly plan builder
│       │   ├── Cart.jsx             # Review + send to FM cart
│       │   ├── Pantry.jsx           # Manage staple items
│       │   ├── PriceHistory.jsx     # Charts of prices over time
│       │   └── Settings.jsx         # LLM provider, store, API keys
│       │
│       └── components/
│           ├── RecipeCard.jsx
│           ├── SaleItemCard.jsx
│           ├── IngredientList.jsx
│           ├── CartSummary.jsx
│           ├── AgentChat.jsx        # Chat interface to talk to agent
│           └── Layout.jsx           # Nav, sidebar, etc.
│
└── data/
    └── seed/
        ├── recipes.json             # 13 starter recipes from our meal plan
        └── staples.json             # Your regular Amazon Fresh items
```

## Database Schema

### recipes
| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK | Auto-increment |
| name | TEXT | e.g. "Gnocchi Shepherd's Pie" |
| type | TEXT | dinner, lunch, breakfast, date_night, snack |
| serves | TEXT | "2-3" |
| prep_time | TEXT | "40 min" |
| steps | TEXT | Full instructions |
| rating | INTEGER | 1-5, nullable |
| last_cooked | DATE | nullable |
| source | TEXT | "manual", "generated", URL |
| created_at | DATETIME | |
| updated_at | DATETIME | |

### ingredients
| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK | |
| recipe_id | INTEGER FK | → recipes.id |
| name | TEXT | "ground beef" |
| quantity | TEXT | "1 lb" |
| category | TEXT | protein, produce, dairy, pantry, frozen |
| substitutable | BOOLEAN | Can agent swap for sale item? |
| substitute_group | TEXT | e.g. "ground_meat" — pork/beef/turkey interchangeable |

### tags
| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK | |
| recipe_id | INTEGER FK | → recipes.id |
| tag | TEXT | "quick", "comfort", "spicy", "girlfriend-approved" |

### pantry_staples
| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK | |
| name | TEXT | "jasmine rice" |
| category | TEXT | protein, produce, dairy, pantry, frozen |
| default_store | TEXT | "amazon_fresh" or "fred_meyer" |
| amazon_price | REAL | Last known price |
| typical_quantity | TEXT | "2 lb bag" |
| reorder_frequency | TEXT | "weekly", "biweekly", "monthly" |

### kroger_tokens
| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK | |
| access_token | TEXT | Encrypted |
| refresh_token | TEXT | Encrypted |
| expires_at | DATETIME | access token expiry |
| location_id | TEXT | "70100150" (FM Interstate) |

### price_history
| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK | |
| product_name | TEXT | |
| upc | TEXT | Kroger UPC |
| store | TEXT | "fred_meyer" or "amazon_fresh" |
| regular_price | REAL | |
| sale_price | REAL | nullable |
| recorded_at | DATETIME | |

### meal_plans
| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK | |
| week_of | DATE | Monday of the week |
| status | TEXT | "draft", "approved", "ordered" |
| created_at | DATETIME | |

### meal_plan_recipes
| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK | |
| meal_plan_id | INTEGER FK | → meal_plans.id |
| recipe_id | INTEGER FK | → recipes.id |
| notes | TEXT | e.g. "sub pork tenderloin for chicken (on sale)" |

### settings
| Column | Type | Notes |
|--------|------|-------|
| key | TEXT PK | "llm_provider", "store_location_id", etc. |
| value | TEXT | |

## API Endpoints

### Recipes
- `GET /api/recipes` — List all (filterable by type, tag, rating)
- `GET /api/recipes/:id` — Single recipe with ingredients
- `POST /api/recipes` — Create new recipe
- `PUT /api/recipes/:id` — Update recipe
- `DELETE /api/recipes/:id` — Delete recipe
- `POST /api/recipes/:id/rate` — Rate a recipe
- `POST /api/recipes/:id/cooked` — Mark as cooked today

### Pantry Staples
- `GET /api/staples` — List all staples
- `POST /api/staples` — Add staple
- `PUT /api/staples/:id` — Update staple
- `DELETE /api/staples/:id` — Remove staple

### Sales
- `GET /api/sales/scan` — Scan FM for current sales (triggers Kroger API search across categories)
- `GET /api/sales/matches` — Sale items matched to existing recipes

### Cart
- `GET /api/cart/preview` — Preview what would be added
- `POST /api/cart/add` — Add items to FM cart (Kroger API)
- `POST /api/cart/add-recipe/:id` — Add all ingredients for a recipe

### Agent
- `POST /api/agent/plan-week` — Full workflow: scan sales → match recipes → suggest meal plan
- `POST /api/agent/suggest-recipes` — Given sale items, suggest new recipes
- `POST /api/agent/chat` — Freeform chat with the agent (streaming SSE)

### Auth
- `GET /api/auth/kroger/start` — Initiate Kroger OAuth flow
- `GET /api/auth/kroger/callback` — OAuth callback
- `GET /api/auth/kroger/status` — Check if token is valid

### Prices
- `GET /api/prices/history?item=ground_beef` — Price history for an item
- `GET /api/prices/compare` — FM vs Amazon for staples

### Settings
- `GET /api/settings` — All settings
- `PUT /api/settings` — Update settings

## LLM Router Design

```python
# backend/app/services/llm.py

class LLMRouter:
    """Routes LLM calls to Claude API or OpenRouter based on settings."""

    async def complete(self, messages, tools=None, model=None):
        provider = get_setting("llm_provider")  # "claude" or "openrouter"

        if provider == "claude":
            return await self._claude_call(messages, tools, model or "claude-sonnet-4-20250514")
        else:
            return await self._openrouter_call(messages, tools, model or "anthropic/claude-sonnet-4")

    async def _claude_call(self, messages, tools, model):
        """Direct Anthropic SDK call."""
        client = AsyncAnthropic(api_key=get_setting("anthropic_api_key"))
        response = await client.messages.create(
            model=model,
            messages=messages,
            tools=tools,
            max_tokens=4096
        )
        return response

    async def _openrouter_call(self, messages, tools, model):
        """OpenRouter API call (OpenAI-compatible format)."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {get_setting('openrouter_api_key')}",
                    "HTTP-Referer": "http://localhost:3000",
                },
                json={
                    "model": model,
                    "messages": messages,
                    "tools": tools,
                }
            )
            return response.json()
```

## Agent Orchestrator Design

```python
# backend/app/services/agent.py

class GroceryAgent:
    """Main agent that orchestrates the weekly shopping workflow."""

    def __init__(self, llm: LLMRouter, kroger: KrogerService, db: Session):
        self.llm = llm
        self.kroger = kroger
        self.db = db

    async def plan_week(self) -> MealPlan:
        """Full weekly planning workflow."""

        # 1. Scan current FM sales
        sales = await self.kroger.scan_sales(categories=[
            "meat", "seafood", "produce", "dairy", "frozen", "pantry"
        ])

        # 2. Filter to meaningful discounts (>15% off, in-stock)
        good_deals = [s for s in sales if s.discount_pct > 15 and s.in_stock]

        # 3. Match sales to existing recipes
        recipe_matches = await self.match_sales_to_recipes(good_deals)

        # 4. Get staples list
        staples = self.db.query(PantryStaple).all()

        # 5. Ask LLM to build a meal plan
        plan = await self.llm.complete(
            messages=[{
                "role": "user",
                "content": self._build_planning_prompt(
                    sales=good_deals,
                    matched_recipes=recipe_matches,
                    staples=staples,
                    recent_meals=self._get_recent_meals(days=14)
                )
            }],
            tools=self._get_tools()
        )

        # 6. Parse LLM response into MealPlan
        return self._parse_meal_plan(plan)

    async def suggest_recipes(self, sale_items: list) -> list[Recipe]:
        """Generate new recipe ideas from sale items + staples."""
        staples = self.db.query(PantryStaple).all()

        prompt = f"""You are a home cooking assistant for a single guy in Portland
        who sometimes cooks for his girlfriend. He prefers simple, hearty meals
        that serve 2-3 people and take under 45 minutes.

        SALE ITEMS THIS WEEK:
        {self._format_sale_items(sale_items)}

        PANTRY STAPLES ALWAYS AVAILABLE:
        {self._format_staples(staples)}

        RECENTLY COOKED (avoid repeats):
        {self._format_recent_meals()}

        Generate 3-4 recipe suggestions that maximize the sale items.
        For each recipe, include: name, type, serves, prep_time,
        ingredients (with quantities), and steps.
        Return as JSON."""

        response = await self.llm.complete([{"role": "user", "content": prompt}])
        return self._parse_recipes(response)

    async def match_sales_to_recipes(self, sales: list) -> list:
        """Find existing recipes where a sale item can substitute in."""
        sale_names = [s.name.lower() for s in sales]

        # Find recipes with substitutable ingredients matching sale items
        recipes = self.db.query(Recipe).join(Ingredient).filter(
            Ingredient.substitutable == True
        ).all()

        matches = []
        for recipe in recipes:
            for ing in recipe.ingredients:
                if ing.substitutable:
                    for sale in sales:
                        if self._is_compatible(ing, sale):
                            matches.append({
                                "recipe": recipe,
                                "original_ingredient": ing,
                                "sale_substitute": sale,
                                "savings": sale.regular_price - sale.sale_price
                            })
        return matches
```

## Seed Data

### recipes.json (13 starter recipes)
Seed from the recipes we already built:
1. Gnocchi Shepherd's Pie
2. Shrimp Fried Rice
3. Chorizo Breakfast Tacos
4. One-Pan Italian Sausage & Veggies
5. Beef Tacos
6. Chicken Thigh & Mushroom Rice
7. Rigatoni Bolognese
8. Avocado Toast Bar
9. Chili (ground beef)
10. Honey-Garlic Pork Tenderloin (from today's sale match)
11. Chicken Thigh Tacos (from today's sale match)
12. Tri-Tip Stir Fry (from today's sale match)
13. Slow Cooker Chuck Roast (from today's sale match)

### staples.json (regular Amazon Fresh items)
All items from Jeremy's Amazon Fresh order history, categorized with prices and reorder frequency.

## Docker Compose

```yaml
version: "3.8"

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data          # SQLite DB + seed data
      - ./backend/app:/app/app    # Hot reload in dev
    environment:
      - DATABASE_URL=sqlite:///data/grocery.db
      - KROGER_CLIENT_ID=${KROGER_CLIENT_ID}
      - KROGER_CLIENT_SECRET=${KROGER_CLIENT_SECRET}
      - KROGER_REDIRECT_URI=http://localhost:8000/api/auth/kroger/callback
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    volumes:
      - ./frontend/src:/app/src   # Hot reload in dev
    environment:
      - VITE_API_URL=http://localhost:8000
    command: npm run dev -- --host 0.0.0.0
```

## .env.example

```
KROGER_CLIENT_ID=automatebuildersclaudemcp-bbccprr5
KROGER_CLIENT_SECRET=your_secret_here
KROGER_REDIRECT_URI=http://localhost:8000/api/auth/kroger/callback
KROGER_LOCATION_ID=70100150

ANTHROPIC_API_KEY=your_key_here
OPENROUTER_API_KEY=your_key_here

LLM_PROVIDER=claude
```

## Frontend Pages Detail

### 1. Recipes Page
- Grid of recipe cards with photo placeholder, name, type, rating, last cooked
- Filter by: type (dinner/lunch/etc), tag, rating
- Search bar
- "Add Recipe" button → modal form
- Click card → RecipeDetail page

### 2. Recipe Detail Page
- Full recipe view: name, type, serves, time, rating stars
- Ingredient list with category badges and "substitutable" toggle
- Steps
- "I Cooked This" button (updates last_cooked)
- "Add to This Week's Cart" button
- Edit mode toggle

### 3. Sales Scanner Page
- "Scan Sales" button → hits /api/sales/scan
- Grid of sale items grouped by category
- Each card shows: item name, sale price, regular price, % off
- "Match to Recipes" button → shows which existing recipes could use this item
- Highlight items that match your staples list

### 4. Meal Planner Page
- "Plan This Week" button → triggers agent workflow
- Shows suggested recipes with sale-matched substitutions highlighted
- Drag to reorder / remove / swap
- "Approve Plan" → moves to cart review
- Calendar view of past weeks

### 5. Cart Page
- Aggregated ingredient list from approved meal plan
- Deduplication (if 2 recipes need onions, combine qty)
- Cross-reference with staples (skip items you already have)
- UPC lookup status for each item
- "Send to Fred Meyer Cart" button
- Estimated total

### 6. Pantry Manager Page
- List of your regular staples
- Edit default store (Amazon vs FM)
- Set reorder frequency
- Current price at each store
- "Run Price Check" → scans both stores for current prices

### 7. Settings Page
- LLM provider toggle (Claude / OpenRouter)
- API keys (masked input)
- Default store + location
- Notification preferences
- Data export/import

## Implementation Order

### Phase 1: Foundation
1. Backend scaffold: FastAPI app, config, database models, Alembic migrations
2. Kroger service (port from our MCP server.py)
3. Recipe CRUD endpoints + seed data
4. Staples CRUD endpoints + seed data
5. Frontend scaffold: Vite + React + Tailwind + React Router
6. Recipes page (list + detail + create/edit)
7. Docker Compose (both services running)

### Phase 2: Kroger Integration
8. Kroger OAuth flow (backend endpoint + frontend redirect)
9. Token storage + auto-refresh
10. Sales scanner (search multiple categories, filter for deals)
11. Sales page in frontend
12. Cart add endpoint
13. Cart page in frontend

### Phase 3: Agent
14. LLM router (Claude + OpenRouter)
15. Agent orchestrator (plan_week, suggest_recipes, match_sales)
16. Meal planner page
17. Agent chat interface (streaming SSE)
18. Recipe generation from sale items

### Phase 4: Polish
19. Price history tracking + charts
20. Pantry manager page
21. Settings page
22. Price comparison (FM vs Amazon)
23. Notifications (optional: email/iMessage when good deals found)

## Key Kroger API Details

- **Base URL:** https://api.kroger.com/v1
- **Auth:** OAuth2 (client credentials for search, authorization code for cart)
- **Access token TTL:** 30 minutes
- **Refresh token TTL:** 6 months
- **Rate limits:** Products 10k/day, Locations 1.6k/day, Cart 5k/day
- **Store:** Fred Meyer Interstate, location_id: 70100150
- **Store brands to prefer:** Kroger, Simple Truth, Private Selection, Fred Meyer
- **Client ID:** automatebuildersclaudemcp-bbccprr5
- **Redirect URI:** http://localhost:8000/api/auth/kroger/callback

## Existing Code to Port

The Kroger API client from `~/Developer/kroger_mcp/server.py` contains working implementations of:
- OAuth2 authorization flow with local callback server
- Client credentials token exchange
- Product search by term + location
- Product detail by ID
- Cart add by UPC
- User profile fetch
- Token refresh logic

Port these into `backend/app/services/kroger.py` as an async class using httpx.

## Recipe Import Features (Inspired by Pantry Pilot)

### URL Recipe Import
Paste any recipe URL (blog, AllRecipes, NYT Cooking, Serious Eats, etc.) and the agent extracts and structures it automatically.

**Backend flow:**
```python
# backend/app/services/recipe_importer.py

class RecipeImporter:
    """Import recipes from URLs, social media, and plain text."""

    async def import_from_url(self, url: str) -> Recipe:
        """Fetch a recipe URL and extract structured recipe data."""
        # 1. Fetch page content
        html = await self._fetch_url(url)

        # 2. Try JSON-LD first (most recipe sites use schema.org Recipe markup)
        json_ld = self._extract_json_ld(html)
        if json_ld:
            return self._parse_json_ld(json_ld)

        # 3. Fall back to LLM extraction
        text = self._html_to_text(html)
        return await self._llm_extract(text, source_url=url)

    async def import_from_social(self, url: str) -> Recipe:
        """Import from Instagram/TikTok/YouTube recipe videos."""
        # For video platforms, fetch the page and extract description/captions
        # Then use LLM to parse the recipe from the description text
        html = await self._fetch_url(url)
        text = self._html_to_text(html)

        prompt = f"""Extract a recipe from this social media post.
        If there's not enough detail for exact quantities, make reasonable
        estimates for a serving size of 2-3 people.

        Source text:
        {text[:3000]}

        Return as JSON with: name, type, serves, prep_time,
        ingredients (name, quantity, category), and steps."""

        response = await self.llm.complete([{"role": "user", "content": prompt}])
        recipe = self._parse_llm_recipe(response)
        recipe.source = url
        return recipe

    async def import_from_text(self, text: str) -> Recipe:
        """Import from plain text (copy-pasted recipe, napkin notes, etc.)."""
        prompt = f"""Parse this text into a structured recipe.
        If quantities are missing, estimate for 2-3 servings.

        Text:
        {text}

        Return as JSON with: name, type, serves, prep_time,
        ingredients (name, quantity, category, substitutable), and steps."""

        response = await self.llm.complete([{"role": "user", "content": prompt}])
        recipe = self._parse_llm_recipe(response)
        recipe.source = "manual"
        return recipe

    def _extract_json_ld(self, html: str) -> dict | None:
        """Extract schema.org Recipe JSON-LD from HTML.
        Most major recipe sites (AllRecipes, Serious Eats, NYT Cooking,
        Food Network, etc.) embed structured recipe data this way."""
        from bs4 import BeautifulSoup
        import json
        soup = BeautifulSoup(html, 'html.parser')
        for script in soup.find_all('script', type='application/ld+json'):
            try:
                data = json.loads(script.string)
                if isinstance(data, list):
                    data = data[0]
                if data.get('@type') == 'Recipe':
                    return data
                # Sometimes nested in @graph
                if '@graph' in data:
                    for item in data['@graph']:
                        if item.get('@type') == 'Recipe':
                            return item
            except (json.JSONDecodeError, KeyError):
                continue
        return None
```

**API endpoints:**
- `POST /api/recipes/import/url` — Import from URL (blog, recipe site)
- `POST /api/recipes/import/social` — Import from Instagram/TikTok/YouTube
- `POST /api/recipes/import/text` — Import from plain text

**Frontend:**
- "Import Recipe" button on Recipes page with three tabs: URL, Social Media, Text
- URL tab: paste link, preview extracted recipe, edit before saving
- Social tab: paste Instagram/TikTok/YouTube link
- Text tab: paste or type freeform recipe text
- All tabs show a preview of the extracted recipe for review before saving to DB

### Auto-Substitution at Cart Time

When building a cart from a meal plan, the agent checks each ingredient:

```python
# backend/app/services/cart_builder.py

class CartBuilder:
    """Build a Kroger cart from a meal plan, with smart substitutions."""

    async def build_cart(self, meal_plan: MealPlan) -> CartPreview:
        """Convert meal plan recipes into a Kroger cart with substitutions."""
        cart_items = []

        for recipe in meal_plan.recipes:
            for ingredient in recipe.ingredients:
                # 1. Search Kroger for the ingredient
                results = await self.kroger.search_products(
                    term=ingredient.name,
                    location_id=self.location_id
                )

                if not results:
                    cart_items.append(CartItem(
                        ingredient=ingredient,
                        status="not_found",
                        action_needed=True
                    ))
                    continue

                best_match = results[0]

                # 2. Check if it's in stock
                if not best_match.in_stock and ingredient.substitutable:
                    # Try substitute group
                    alt = await self._find_substitute(ingredient)
                    if alt:
                        cart_items.append(CartItem(
                            ingredient=ingredient,
                            product=alt,
                            status="substituted",
                            original=best_match.name,
                            reason="out of stock"
                        ))
                        continue

                # 3. Check if a sale alternative exists
                if ingredient.substitutable:
                    sale_alt = await self._find_sale_alternative(ingredient)
                    if sale_alt and sale_alt.savings > 0.50:
                        cart_items.append(CartItem(
                            ingredient=ingredient,
                            product=sale_alt.product,
                            status="sale_swap",
                            original=best_match.name,
                            savings=sale_alt.savings,
                            reason=f"${sale_alt.savings:.2f} cheaper"
                        ))
                        continue

                # 4. Use the direct match
                cart_items.append(CartItem(
                    ingredient=ingredient,
                    product=best_match,
                    status="matched"
                ))

        # 5. Deduplicate (combine onions from multiple recipes, etc.)
        cart_items = self._deduplicate(cart_items)

        # 6. Remove items already in pantry staples
        cart_items = self._remove_staples(cart_items)

        return CartPreview(items=cart_items, estimated_total=sum(i.price for i in cart_items))
```

## First-Run Setup Wizard

Since this is a self-hosted Docker app, the frontend needs a setup wizard on first launch:

### Step 1: Welcome
- App name, brief description
- "Let's get you set up in 3 minutes"

### Step 2: Kroger API Credentials
- Link to Kroger Developer Portal (https://developer.kroger.com) with step-by-step instructions
- Input fields for Client ID and Client Secret
- "Test Connection" button to verify credentials work
- Note: "Your credentials stay on your machine. Nothing is sent to any third party."

### Step 3: Find Your Store
- ZIP code input
- Dropdown of nearby Kroger-family stores (Fred Meyer, QFC, Ralphs, etc.)
- Powered by Kroger Locations API
- Shows store name, address, distance

### Step 4: Kroger Account Auth
- "Connect Your Kroger Account" button
- Redirects to Kroger OAuth login
- Needed for cart operations (optional — can skip and use search-only mode)

### Step 5: LLM Provider
- Toggle: Claude API / OpenRouter
- API key input (masked)
- Model selection dropdown
  - Claude: claude-sonnet-4-20250514, claude-haiku-4-5-20251001
  - OpenRouter: anthropic/claude-sonnet-4, google/gemini-2.0-flash, etc.
- "Test Connection" button
- Note: "Your API key stays on your machine."

### Step 6: Seed Data (Optional)
- "Import starter recipes?" — loads the 13 seed recipes
- "Import common pantry staples?" — loads a default pantry list
- "I'll start from scratch" option

### Step 7: Ready!
- Summary of configuration
- "Start Shopping" button → goes to main app

## Competitive Landscape & Differentiation

### Existing Players
| App | Model | Strengths | Gaps |
|-----|-------|-----------|------|
| Pantry Pilot | SaaS, Woolworths (AU) | Great UX, recipe import, auto-checkout | Australia only, closed source, no sale matching |
| Hungryroot | Subscription meal kit | Pre-filled carts, learns preferences | Locked ecosystem, expensive, not your store |
| Instacart Cart Assistant | Built into Instacart | Kroger integration, AI meal planning | Instacart markup, no self-hosting, no BYO LLM |
| Grocery AI App | Mobile app | Pantry tracking, list sharing | No cart integration, no AI recipe generation |
| Cooklist | Mobile app | Recipe management, Kroger integration | No sale scanning, no AI agent |
| Uber Cart Assistant | Built into Uber Eats | Image-to-cart, natural language | Locked to Uber ecosystem |

### Our Differentiation
1. **Sale-driven planning** — starts with what's cheap, not what you want
2. **Open source + self-hosted** — your data, your keys, your machine
3. **BYO LLM** — Claude, OpenRouter, or any OpenAI-compatible API
4. **Kroger ecosystem** — Fred Meyer, QFC, Ralphs, King Soopers, etc. (all Kroger banners)
5. **Recipe database is yours** — not locked in a platform, exportable JSON/SQLite
6. **Price history** — track prices over time, know when a "sale" is actually a deal
7. **Substitution intelligence** — swaps ingredients for sale alternatives automatically
8. **Recipe import from anywhere** — URLs, social media, plain text, JSON-LD extraction
9. **Influencer/creator recipe feed** — follow food bloggers, YouTube chefs, and AllRecipes authors; get notified when their new recipes match current sales
10. **Optional centralized recipe API** — Cloudflare Worker aggregates recipes from popular sources so individual instances don't each scrape the same blogs

## Kroger Banner Support

The Kroger API works across ALL Kroger-family banners. Users pick their local store during setup:
- **Fred Meyer** (Pacific Northwest)
- **QFC** (Quality Food Centers, Pacific Northwest)
- **Ralphs** (Southern California)
- **King Soopers** (Colorado)
- **Fry's** (Arizona)
- **Smith's** (Utah, Nevada)
- **Kroger** (Midwest, Southeast, Mid-Atlantic)
- **Harris Teeter** (Southeast, Mid-Atlantic)
- **Mariano's** (Chicago)
- And ~15 more regional banners

This means the app works nationwide for anyone near a Kroger-family store, which covers roughly 35% of US grocery shoppers.

## Updated Project Structure

```
grocery-agent/
├── docker-compose.yml
├── docker-compose.prod.yml         # Production config (no hot reload)
├── .env.example
├── README.md
├── LICENSE                          # MIT or Apache 2.0
├── CONTRIBUTING.md
│
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── alembic.ini
│   ├── migrations/
│   │   └── versions/
│   │
│   └── app/
│       ├── main.py
│       ├── config.py
│       ├── database.py
│       │
│       ├── models/
│       │   ├── recipe.py
│       │   ├── staple.py
│       │   ├── kroger.py
│       │   ├── meal_plan.py
│       │   └── settings.py
│       │
│       ├── routers/
│       │   ├── recipes.py
│       │   ├── staples.py
│       │   ├── sales.py
│       │   ├── cart.py
│       │   ├── agent.py
│       │   ├── auth.py
│       │   ├── prices.py
│       │   ├── import_recipe.py     # NEW: URL/social/text import
│       │   ├── setup.py             # NEW: First-run wizard API
│       │   └── settings.py
│       │
│       └── services/
│           ├── kroger.py
│           ├── llm.py
│           ├── agent.py
│           ├── recipe_importer.py   # NEW: URL/social/text extraction
│           ├── recipe_matcher.py
│           ├── cart_builder.py      # NEW: Smart cart with substitutions
│           └── price_tracker.py
│
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   ├── index.html
│   │
│   └── src/
│       ├── main.jsx
│       ├── App.jsx
│       ├── api/
│       │   └── client.js
│       │
│       ├── pages/
│       │   ├── Setup.jsx            # NEW: First-run wizard
│       │   ├── Recipes.jsx
│       │   ├── RecipeDetail.jsx
│       │   ├── RecipeImport.jsx     # NEW: Import from URL/social/text
│       │   ├── Sales.jsx
│       │   ├── MealPlanner.jsx
│       │   ├── Cart.jsx
│       │   ├── Pantry.jsx
│       │   ├── PriceHistory.jsx
│       │   └── Settings.jsx
│       │
│       └── components/
│           ├── RecipeCard.jsx
│           ├── SaleItemCard.jsx
│           ├── IngredientList.jsx
│           ├── CartSummary.jsx
│           ├── SubstitutionBadge.jsx # NEW: Shows swap info on cart items
│           ├── ImportPreview.jsx     # NEW: Preview extracted recipe
│           ├── SetupStep.jsx         # NEW: Wizard step component
│           ├── AgentChat.jsx
│           └── Layout.jsx
│
└── data/
    └── seed/
        ├── recipes.json
        └── staples.json
```

## Updated Implementation Phases

### Phase 1: Foundation
1. Backend scaffold: FastAPI app, config, database models, Alembic migrations
2. Kroger service (port from MCP server.py)
3. Recipe CRUD endpoints + seed data
4. Staples CRUD endpoints + seed data
5. Frontend scaffold: Vite + React + Tailwind + React Router
6. Recipes page (list + detail + create/edit)
7. Docker Compose (both services running)

### Phase 2: Kroger Integration
8. First-run setup wizard (frontend + backend)
9. Kroger OAuth flow (backend endpoint + frontend redirect)
10. Token storage + auto-refresh
11. Store location search + selection
12. Sales scanner (search multiple categories, filter for deals)
13. Sales page in frontend
14. Cart add endpoint
15. Cart page in frontend

### Phase 3: Agent + Intelligence
16. LLM router (Claude + OpenRouter)
17. Agent orchestrator (plan_week, suggest_recipes, match_sales)
18. Recipe import from URL (JSON-LD + LLM fallback)
19. Recipe import from social media links
20. Recipe import from plain text
21. Smart cart builder with auto-substitution
22. Meal planner page
23. Agent chat interface (streaming SSE)

### Phase 4: Polish + Open Source Prep
24. Price history tracking + charts
25. Pantry manager page
26. Settings page
27. Price comparison (FM vs Amazon)
28. README with clear setup instructions
29. docker-compose.prod.yml for production use
30. LICENSE file (MIT)
31. GitHub repo setup + initial release

### Phase 5: Influencer / Creator Recipe Feed
32. Followed Sources feature (local polling mode)
33. RSS/Atom feed discovery + polling
34. Social media recipe scraping
35. "New from your creators" notification feed
36. Sale-match alerts on new creator recipes
37. Sources page + creator feed UI

### Phase 6: Centralized Recipe API (Cloudflare Worker)
38. Cloudflare Worker + D1 database for recipe aggregation
39. Cron Trigger for scheduled source polling
40. Public REST API for Docker instances to pull from
41. Admin dashboard for managing sources
42. Docker container config to toggle local vs centralized feed mode

## Followed Sources / Influencer Feed

### Concept
Follow food creators, blogs, and influencer accounts. The agent periodically checks for new recipes, imports them, and cross-references ingredients against current store sales. When a new recipe from someone you follow has ingredients on sale, you get a notification.

### Database Schema

#### followed_sources
| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK | |
| name | TEXT | "Budget Bytes", "Matthew McConaughey", "Joshua Weissman" |
| source_type | TEXT | "blog_rss", "allrecipes_author", "youtube", "instagram", "tiktok" |
| url | TEXT | RSS feed URL, author page URL, or channel URL |
| check_frequency | TEXT | "daily", "weekly" |
| last_checked | DATETIME | |
| last_new_recipe | DATETIME | |
| enabled | BOOLEAN | default true |
| created_at | DATETIME | |

#### imported_recipes (extends recipes table)
Additional columns on recipes:
| Column | Type | Notes |
|--------|------|-------|
| source_id | INTEGER FK | → followed_sources.id (nullable, only for auto-imported) |
| auto_imported | BOOLEAN | true if from a followed source, false if manually added |
| import_status | TEXT | "pending_review", "approved", "rejected" |
| original_url | TEXT | Direct link to the original recipe |

#### sale_alerts
| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK | |
| recipe_id | INTEGER FK | → recipes.id |
| source_id | INTEGER FK | → followed_sources.id |
| sale_items_matched | INTEGER | Number of ingredients currently on sale |
| total_ingredients | INTEGER | Total ingredients in recipe |
| estimated_savings | REAL | Savings vs regular price |
| alert_status | TEXT | "new", "seen", "added_to_plan", "dismissed" |
| created_at | DATETIME | |

### Source Types & Import Strategies

#### 1. Blog RSS Feeds (most reliable)
Most food blogs publish RSS/Atom feeds. This is the cleanest source:
- Discover feed URL from blog homepage (`<link rel="alternate" type="application/rss+xml">`)
- Poll feed on schedule (daily or weekly)
- Each new entry: fetch the full recipe page, extract via JSON-LD or LLM
- **Examples:** Budget Bytes, Serious Eats, Smitten Kitchen, Half Baked Harvest, Minimalist Baker

```python
# backend/app/services/feed_checker.py

class FeedChecker:
    """Check followed sources for new recipes."""

    async def check_rss_source(self, source: FollowedSource) -> list[Recipe]:
        """Poll an RSS feed for new recipes since last check."""
        import feedparser

        feed = feedparser.parse(source.url)
        new_recipes = []

        for entry in feed.entries:
            published = dateutil.parser.parse(entry.published)
            if published <= source.last_checked:
                continue

            # Fetch the full recipe page and import
            recipe = await self.importer.import_from_url(entry.link)
            recipe.source_id = source.id
            recipe.auto_imported = True
            recipe.import_status = "pending_review"
            recipe.original_url = entry.link
            new_recipes.append(recipe)

        source.last_checked = datetime.utcnow()
        if new_recipes:
            source.last_new_recipe = datetime.utcnow()

        return new_recipes

    async def check_allrecipes_author(self, source: FollowedSource) -> list[Recipe]:
        """Check an AllRecipes author/profile page for new recipes."""
        # AllRecipes author pages list recipes chronologically
        # Fetch page, extract recipe links, import any new ones
        html = await self._fetch_url(source.url)
        recipe_links = self._extract_allrecipes_links(html)

        new_recipes = []
        for link in recipe_links:
            # Skip if we've already imported this URL
            existing = self.db.query(Recipe).filter(
                Recipe.original_url == link
            ).first()
            if existing:
                continue

            recipe = await self.importer.import_from_url(link)
            recipe.source_id = source.id
            recipe.auto_imported = True
            recipe.import_status = "pending_review"
            new_recipes.append(recipe)

        return new_recipes

    async def check_youtube_channel(self, source: FollowedSource) -> list[Recipe]:
        """Check a YouTube channel for new recipe videos."""
        # YouTube channels have RSS feeds at:
        # https://www.youtube.com/feeds/videos.xml?channel_id=CHANNEL_ID
        # Parse the feed, fetch each video page, extract recipe from description
        feed_url = self._youtube_to_rss(source.url)
        feed = feedparser.parse(feed_url)

        new_recipes = []
        for entry in feed.entries:
            published = dateutil.parser.parse(entry.published)
            if published <= source.last_checked:
                continue

            # Try to extract recipe from video description
            recipe = await self.importer.import_from_social(entry.link)
            if recipe:
                recipe.source_id = source.id
                recipe.auto_imported = True
                recipe.import_status = "pending_review"
                new_recipes.append(recipe)

        return new_recipes
```

#### 2. AllRecipes Author Pages
AllRecipes profiles list all recipes by an author. Works for celebrity chef collaborations:
- `https://www.allrecipes.com/author/matthew-mcconaughey/`
- `https://www.allrecipes.com/author/alton-brown/`
- Scrape the profile page for recipe links, import each via JSON-LD

#### 3. YouTube Channels
Every YouTube channel has a hidden RSS feed. Good for video recipe creators:
- Joshua Weissman, Babish, Sam the Cooking Guy, etc.
- Feed URL: `https://www.youtube.com/feeds/videos.xml?channel_id=XXXXX`
- Extract recipe from video description, fall back to auto-captions via LLM

#### 4. Instagram (limited)
Instagram doesn't have public RSS or API access for consumer apps:
- **Option A:** User manually pastes Instagram post URLs when they see something good
- **Option B:** Use a third-party service like RapidAPI's Instagram scraper (paid, fragile)
- **Recommended:** Don't auto-poll Instagram. Instead, make it easy to paste links manually.

#### 5. TikTok (limited)
Similar to Instagram — no reliable auto-polling:
- User pastes TikTok URLs manually
- Agent extracts recipe from video description/captions
- Works well for the import flow, just not for auto-discovery

### Sale-Match Alerts

When the feed checker finds new recipes from followed sources, it automatically cross-references ingredients with current store sales:

```python
# backend/app/services/sale_alerter.py

class SaleAlerter:
    """Generate alerts when followed-source recipes match current sales."""

    async def check_new_recipes(self, recipes: list[Recipe]) -> list[SaleAlert]:
        """Check newly imported recipes against current sales."""
        # Get current sales (cached, refreshed daily)
        current_sales = await self.kroger.get_cached_sales()
        sale_names = {s.name.lower(): s for s in current_sales}

        alerts = []
        for recipe in recipes:
            matched_sale_items = 0
            total_savings = 0.0

            for ingredient in recipe.ingredients:
                # Fuzzy match ingredient name against sale items
                match = self._fuzzy_match(ingredient.name, sale_names)
                if match:
                    matched_sale_items += 1
                    total_savings += match.regular_price - match.sale_price

            if matched_sale_items > 0:
                alert = SaleAlert(
                    recipe_id=recipe.id,
                    source_id=recipe.source_id,
                    sale_items_matched=matched_sale_items,
                    total_ingredients=len(recipe.ingredients),
                    estimated_savings=total_savings,
                    alert_status="new"
                )
                alerts.append(alert)

        return alerts
```

### API Endpoints

- `GET /api/sources` — List all followed sources
- `POST /api/sources` — Add a new source (auto-detects type from URL)
- `PUT /api/sources/:id` — Update source settings
- `DELETE /api/sources/:id` — Unfollow a source
- `POST /api/sources/:id/check` — Manually trigger a check for new recipes
- `POST /api/sources/check-all` — Check all enabled sources
- `GET /api/sources/feed` — Combined feed of new recipes from all sources
- `GET /api/alerts` — Sale match alerts (new recipes with sale ingredients)
- `POST /api/alerts/:id/add-to-plan` — Add an alerted recipe to this week's plan
- `POST /api/alerts/:id/dismiss` — Dismiss an alert

### Frontend: Sources Page

**Follow a Creator:**
- "Follow" button → paste URL input
- Auto-detects source type (blog, AllRecipes, YouTube, etc.)
- Shows creator name, avatar (if available), recipe count
- Toggle enabled/disabled
- Set check frequency (daily/weekly)

**Creator Feed:**
- Chronological list of new recipes from followed sources
- Each card shows: creator name, recipe name, photo, date published
- Badge: "3 of 8 ingredients on sale!" with estimated savings
- Actions: "Preview", "Add to My Recipes", "Add to This Week's Plan", "Dismiss"

**Sale Alert Banner:**
- Top of page or as notification dot on nav
- "Budget Bytes posted a new Chicken Taco Soup — 5 ingredients are on sale at your Fred Meyer this week. Estimated savings: $4.20"
- Quick actions: "Add to Plan" / "View Recipe" / "Dismiss"

### Popular Sources to Suggest During Setup

During the setup wizard (Step 6), offer a curated list of popular food creators to follow:

**Budget-Friendly:**
- Budget Bytes (budgetbytes.com) — RSS
- $5 Dinners (5dollardinners.com) — RSS
- Skinnytaste (skinnytaste.com) — RSS

**General Home Cooking:**
- Serious Eats (seriouseats.com) — RSS
- Smitten Kitchen (smittenkitchen.com) — RSS
- Half Baked Harvest (halfbakedharvest.com) — RSS
- Damn Delicious (damndelicious.net) — RSS

**Video Creators:**
- Joshua Weissman — YouTube RSS
- Babish Culinary Universe — YouTube RSS
- Sam the Cooking Guy — YouTube RSS
- Ethan Chlebowski — YouTube RSS
- Internet Shaquille — YouTube RSS

**Celebrity / Influencer:**
- AllRecipes featured authors
- Food Network star pages (individual RSS feeds)

**Quick & Simple:**
- Minimalist Baker (minimalistbaker.com) — RSS
- Pinch of Yum (pinchofyum.com) — RSS
- Cookie and Kate (cookieandkate.com) — RSS

### Scheduled Checking

The backend runs a background task (using APScheduler or similar) that checks followed sources on their configured schedule:

```python
# backend/app/services/scheduler.py

from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

@scheduler.scheduled_job('interval', hours=6)
async def check_followed_sources():
    """Check all enabled sources that are due for a check."""
    sources = db.query(FollowedSource).filter(
        FollowedSource.enabled == True,
        FollowedSource.last_checked < datetime.utcnow() - timedelta(hours=12)
    ).all()

    for source in sources:
        new_recipes = await feed_checker.check_source(source)
        if new_recipes:
            alerts = await sale_alerter.check_new_recipes(new_recipes)
            # Store alerts for frontend to display
            for alert in alerts:
                db.add(alert)
    db.commit()
```

## Phase 6: Centralized Recipe API (Cloudflare Worker)

### Problem
If 1,000 people run this Docker container and each one follows Budget Bytes, that's 1,000 instances independently hitting budgetbytes.com every 6 hours to check for new recipes. That's wasteful, slow, and risks getting IP-banned. The blogs don't change that often — Budget Bytes might post 3-4 recipes a week.

### Solution
Run a single Cloudflare Worker that aggregates recipes from all popular sources on a schedule. Each user's Docker container pulls from this centralized API instead of scraping directly. Users can still add their own private sources (those poll locally), but the curated popular sources come from the shared service.

### Architecture

```
┌────────────────────────────────────────────────────┐
│           Cloudflare Worker (recipes-api)            │
│                                                      │
│  Cron Trigger (every 6h)                             │
│  ├── Poll RSS feeds for ~50 popular food blogs       │
│  ├── Scrape AllRecipes author pages                  │
│  ├── Check YouTube channel RSS feeds                 │
│  ├── Extract recipes via JSON-LD / text parsing      │
│  └── Store in D1 database                            │
│                                                      │
│  REST API                                            │
│  ├── GET /sources         — list available sources   │
│  ├── GET /recipes/latest  — new recipes (paginated)  │
│  ├── GET /recipes/source/:id — recipes from a source │
│  ├── GET /recipes/:id     — single recipe detail     │
│  └── GET /health          — status + last poll time  │
│                                                      │
│  Storage                                             │
│  ├── D1: recipes, sources, ingredients               │
│  └── KV: RSS feed cache, rate limit counters         │
└────────────────────┬───────────────────────────────┘
                     │ HTTPS (public, read-only, no auth needed)
                     │
     ┌───────────────┼───────────────┐
     ▼               ▼               ▼
  Docker #1      Docker #2      Docker #3
  (Jeremy)       (User B)       (User C)
  FM Interstate  Ralphs LA      King Soopers CO
```

### D1 Database Schema

```sql
-- Sources we aggregate from
CREATE TABLE sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,                    -- "Budget Bytes"
    source_type TEXT NOT NULL,             -- "blog_rss", "allrecipes_author", "youtube"
    url TEXT NOT NULL,                     -- RSS feed or profile URL
    website_url TEXT,                      -- Homepage for display
    avatar_url TEXT,                       -- Creator avatar/logo
    description TEXT,                      -- Short bio
    category TEXT,                         -- "budget", "general", "video", "celebrity", "quick"
    recipe_count INTEGER DEFAULT 0,        -- Total recipes imported
    last_checked_at TEXT,                  -- ISO timestamp
    last_new_recipe_at TEXT,               -- ISO timestamp
    enabled INTEGER DEFAULT 1,
    created_at TEXT DEFAULT (datetime('now'))
);

-- Imported recipes
CREATE TABLE recipes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id INTEGER NOT NULL REFERENCES sources(id),
    title TEXT NOT NULL,
    description TEXT,
    recipe_type TEXT,                      -- "dinner", "lunch", "breakfast", etc.
    serves TEXT,                           -- "2-3", "4-6"
    prep_time TEXT,                        -- "30 min"
    cook_time TEXT,                        -- "45 min"
    total_time TEXT,                       -- "1 hr 15 min"
    steps TEXT NOT NULL,                   -- JSON array of step strings
    image_url TEXT,                        -- Recipe photo from source
    original_url TEXT NOT NULL UNIQUE,     -- Link back to original
    published_at TEXT,                     -- When the source published it
    imported_at TEXT DEFAULT (datetime('now')),
    json_ld_raw TEXT                       -- Original JSON-LD for debugging
);

-- Recipe ingredients (normalized for search/matching)
CREATE TABLE ingredients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    recipe_id INTEGER NOT NULL REFERENCES recipes(id),
    name TEXT NOT NULL,                    -- "ground beef"
    raw_text TEXT,                         -- "1 lb 80/20 ground beef, browned"
    quantity TEXT,                         -- "1"
    unit TEXT,                             -- "lb"
    category TEXT,                         -- "protein", "produce", "dairy", "pantry", "frozen"
    notes TEXT                             -- "browned", "diced", etc.
);

-- Index for fast lookups
CREATE INDEX idx_recipes_source ON recipes(source_id);
CREATE INDEX idx_recipes_published ON recipes(published_at DESC);
CREATE INDEX idx_ingredients_name ON ingredients(name);
CREATE INDEX idx_ingredients_recipe ON ingredients(recipe_id);
```

### Cloudflare Worker Code Structure

```
worker/
├── wrangler.toml
├── package.json
├── src/
│   ├── index.ts              # Worker entry, router
│   ├── routes/
│   │   ├── sources.ts        # GET /sources
│   │   ├── recipes.ts        # GET /recipes/*
│   │   └── health.ts         # GET /health
│   ├── cron/
│   │   ├── poll-sources.ts   # Main cron handler
│   │   ├── rss-parser.ts     # RSS/Atom feed parsing
│   │   ├── jsonld-parser.ts  # schema.org Recipe extraction
│   │   ├── allrecipes.ts     # AllRecipes author page scraper
│   │   └── youtube.ts        # YouTube channel RSS
│   ├── db/
│   │   ├── schema.sql        # D1 migrations
│   │   └── queries.ts        # Typed DB helpers
│   └── types.ts              # Shared types
└── seed/
    └── sources.json          # Initial ~50 popular food sources
```

### wrangler.toml

```toml
name = "grocery-agent-recipes"
main = "src/index.ts"
compatibility_date = "2024-01-01"

[triggers]
crons = ["0 */6 * * *"]  # Every 6 hours

[[d1_databases]]
binding = "DB"
database_name = "grocery-recipes"
database_id = "<your-d1-id>"

[[kv_namespaces]]
binding = "CACHE"
id = "<your-kv-id>"
```

### Worker API Endpoints

#### GET /sources
List all available recipe sources users can follow.
```json
{
  "sources": [
    {
      "id": 1,
      "name": "Budget Bytes",
      "source_type": "blog_rss",
      "website_url": "https://www.budgetbytes.com",
      "avatar_url": "https://...",
      "description": "Delicious recipes designed for small budgets",
      "category": "budget",
      "recipe_count": 847,
      "last_new_recipe_at": "2026-03-10T14:30:00Z"
    }
  ]
}
```

#### GET /recipes/latest?since=2026-03-05T00:00:00Z&limit=50
New recipes since a timestamp. This is the main endpoint Docker instances poll.
```json
{
  "recipes": [
    {
      "id": 4521,
      "source_id": 1,
      "source_name": "Budget Bytes",
      "title": "One Pot Chicken Taco Soup",
      "description": "A hearty, budget-friendly soup...",
      "recipe_type": "dinner",
      "serves": "6",
      "prep_time": "10 min",
      "total_time": "35 min",
      "image_url": "https://...",
      "original_url": "https://www.budgetbytes.com/chicken-taco-soup/",
      "published_at": "2026-03-10T14:30:00Z",
      "ingredients": [
        {
          "name": "chicken breast",
          "raw_text": "1.5 lbs boneless skinless chicken breast",
          "quantity": "1.5",
          "unit": "lbs",
          "category": "protein"
        }
      ],
      "steps": [
        "Dice the onion and mince the garlic...",
        "Add chicken broth, diced tomatoes..."
      ]
    }
  ],
  "next_cursor": "2026-03-10T14:30:00Z",
  "total": 12
}
```

#### GET /recipes/source/:id?limit=20&offset=0
All recipes from a specific source, paginated.

#### GET /recipes/:id
Full recipe detail with all ingredients and steps.

#### GET /health
```json
{
  "status": "ok",
  "sources_count": 48,
  "recipes_count": 12847,
  "last_poll": "2026-03-12T06:00:00Z",
  "next_poll": "2026-03-12T12:00:00Z"
}
```

### Cron Handler (Recipe Polling)

```typescript
// src/cron/poll-sources.ts

export async function pollSources(env: Env): Promise<void> {
  const sources = await env.DB.prepare(
    "SELECT * FROM sources WHERE enabled = 1"
  ).all();

  for (const source of sources.results) {
    try {
      let newRecipes: Recipe[] = [];

      switch (source.source_type) {
        case "blog_rss":
          newRecipes = await pollRssFeed(source, env);
          break;
        case "allrecipes_author":
          newRecipes = await pollAllRecipesAuthor(source, env);
          break;
        case "youtube":
          newRecipes = await pollYouTubeChannel(source, env);
          break;
      }

      // Insert new recipes
      for (const recipe of newRecipes) {
        // Check for duplicate by original_url
        const existing = await env.DB.prepare(
          "SELECT id FROM recipes WHERE original_url = ?"
        ).bind(recipe.original_url).first();

        if (!existing) {
          const result = await env.DB.prepare(
            `INSERT INTO recipes (source_id, title, description, recipe_type,
             serves, prep_time, cook_time, total_time, steps, image_url,
             original_url, published_at, json_ld_raw)
             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`
          ).bind(
            source.id, recipe.title, recipe.description, recipe.recipe_type,
            recipe.serves, recipe.prep_time, recipe.cook_time, recipe.total_time,
            JSON.stringify(recipe.steps), recipe.image_url,
            recipe.original_url, recipe.published_at,
            JSON.stringify(recipe.json_ld_raw)
          ).run();

          // Insert ingredients
          for (const ing of recipe.ingredients) {
            await env.DB.prepare(
              `INSERT INTO ingredients (recipe_id, name, raw_text, quantity, unit, category, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?)`
            ).bind(
              result.meta.last_row_id, ing.name, ing.raw_text,
              ing.quantity, ing.unit, ing.category, ing.notes
            ).run();
          }
        }
      }

      // Update source metadata
      await env.DB.prepare(
        `UPDATE sources SET last_checked_at = datetime('now'),
         recipe_count = (SELECT COUNT(*) FROM recipes WHERE source_id = ?)
         ${newRecipes.length > 0 ? ", last_new_recipe_at = datetime('now')" : ""}
         WHERE id = ?`
      ).bind(source.id, source.id).run();

    } catch (err) {
      console.error(`Error polling ${source.name}:`, err);
      // Continue to next source, don't fail the whole batch
    }
  }
}
```

### JSON-LD Recipe Parser

```typescript
// src/cron/jsonld-parser.ts

export function extractRecipeFromHtml(html: string): ParsedRecipe | null {
  // Find JSON-LD script tags
  const jsonLdRegex = /<script[^>]*type="application\/ld\+json"[^>]*>([\s\S]*?)<\/script>/gi;
  let match;

  while ((match = jsonLdRegex.exec(html)) !== null) {
    try {
      let data = JSON.parse(match[1]);

      // Handle arrays
      if (Array.isArray(data)) data = data[0];

      // Direct Recipe type
      if (data["@type"] === "Recipe") return parseRecipeJsonLd(data);

      // Nested in @graph
      if (data["@graph"]) {
        for (const item of data["@graph"]) {
          if (item["@type"] === "Recipe") return parseRecipeJsonLd(item);
        }
      }
    } catch (e) {
      continue;
    }
  }
  return null;
}

function parseRecipeJsonLd(data: any): ParsedRecipe {
  return {
    title: data.name || "",
    description: data.description || "",
    image_url: typeof data.image === "string" ? data.image :
               Array.isArray(data.image) ? data.image[0] :
               data.image?.url || null,
    serves: data.recipeYield?.toString() || null,
    prep_time: parseDuration(data.prepTime),
    cook_time: parseDuration(data.cookTime),
    total_time: parseDuration(data.totalTime),
    recipe_type: categorizeRecipe(data.recipeCategory, data.name),
    ingredients: (data.recipeIngredient || []).map(parseIngredientText),
    steps: extractSteps(data.recipeInstructions),
    json_ld_raw: data,
  };
}

function parseIngredientText(raw: string): ParsedIngredient {
  // "1.5 lbs boneless skinless chicken breast, diced"
  // → { name: "chicken breast", quantity: "1.5", unit: "lbs",
  //     raw_text: "1.5 lbs boneless skinless chicken breast, diced",
  //     category: "protein", notes: "boneless skinless, diced" }

  // Basic regex for quantity + unit + name
  const match = raw.match(/^([\d\/\.\s]+)?\s*(cups?|tbsp|tsp|lbs?|oz|pounds?|cloves?|cans?|packages?|bunch|head)?\s*(.+)$/i);

  const name = normalizeIngredientName(match?.[3] || raw);
  return {
    name,
    raw_text: raw,
    quantity: match?.[1]?.trim() || null,
    unit: match?.[2]?.trim() || null,
    category: categorizeIngredient(name),
    notes: null,
  };
}

function categorizeIngredient(name: string): string {
  const lower = name.toLowerCase();
  const categories: Record<string, string[]> = {
    protein: ["chicken", "beef", "pork", "shrimp", "salmon", "turkey", "sausage", "bacon", "lamb", "fish"],
    produce: ["onion", "garlic", "pepper", "tomato", "lettuce", "carrot", "celery", "potato", "mushroom", "avocado", "lime", "lemon", "cilantro", "broccoli", "asparagus", "spinach", "basil"],
    dairy: ["cheese", "milk", "cream", "butter", "yogurt", "egg", "sour cream"],
    frozen: ["frozen"],
    pantry: ["rice", "pasta", "flour", "sugar", "oil", "vinegar", "sauce", "broth", "stock", "beans", "tomato paste", "honey", "spice", "seasoning", "salt", "pepper"],
  };

  for (const [cat, keywords] of Object.entries(categories)) {
    if (keywords.some(kw => lower.includes(kw))) return cat;
  }
  return "pantry"; // default
}
```

### Seed Sources (seed/sources.json)

```json
[
  {
    "name": "Budget Bytes",
    "source_type": "blog_rss",
    "url": "https://www.budgetbytes.com/feed/",
    "website_url": "https://www.budgetbytes.com",
    "description": "Delicious recipes designed for small budgets",
    "category": "budget"
  },
  {
    "name": "Serious Eats",
    "source_type": "blog_rss",
    "url": "https://www.seriouseats.com/feeds/atom",
    "website_url": "https://www.seriouseats.com",
    "description": "Authoritative, well-tested recipes and food science",
    "category": "general"
  },
  {
    "name": "Smitten Kitchen",
    "source_type": "blog_rss",
    "url": "https://smittenkitchen.com/feed/",
    "website_url": "https://smittenkitchen.com",
    "description": "Fearless cooking from a tiny NYC kitchen",
    "category": "general"
  },
  {
    "name": "Half Baked Harvest",
    "source_type": "blog_rss",
    "url": "https://www.halfbakedharvest.com/feed/",
    "website_url": "https://www.halfbakedharvest.com",
    "description": "Creative, flavor-packed recipes",
    "category": "general"
  },
  {
    "name": "Minimalist Baker",
    "source_type": "blog_rss",
    "url": "https://minimalistbaker.com/feed/",
    "website_url": "https://minimalistbaker.com",
    "description": "Simple recipes, 10 ingredients or less",
    "category": "quick"
  },
  {
    "name": "Damn Delicious",
    "source_type": "blog_rss",
    "url": "https://damndelicious.net/feed/",
    "website_url": "https://damndelicious.net",
    "description": "Quick and easy recipes for every occasion",
    "category": "quick"
  },
  {
    "name": "Pinch of Yum",
    "source_type": "blog_rss",
    "url": "https://pinchofyum.com/feed",
    "website_url": "https://pinchofyum.com",
    "description": "Healthy-ish comfort food recipes",
    "category": "general"
  },
  {
    "name": "Cookie and Kate",
    "source_type": "blog_rss",
    "url": "https://cookieandkate.com/feed/",
    "website_url": "https://cookieandkate.com",
    "description": "Vegetarian recipes so good you won't miss the meat",
    "category": "general"
  },
  {
    "name": "Skinnytaste",
    "source_type": "blog_rss",
    "url": "https://www.skinnytaste.com/feed/",
    "website_url": "https://www.skinnytaste.com",
    "description": "Healthy recipes with smart points",
    "category": "budget"
  },
  {
    "name": "Joshua Weissman",
    "source_type": "youtube",
    "url": "https://www.youtube.com/@JoshuaWeissman",
    "website_url": "https://www.youtube.com/@JoshuaWeissman",
    "description": "Making food better than restaurants at home",
    "category": "video"
  },
  {
    "name": "Babish Culinary Universe",
    "source_type": "youtube",
    "url": "https://www.youtube.com/@BabishCulinaryUniverse",
    "website_url": "https://www.youtube.com/@BabishCulinaryUniverse",
    "description": "Recipes from movies, TV, and the internet",
    "category": "video"
  },
  {
    "name": "Ethan Chlebowski",
    "source_type": "youtube",
    "url": "https://www.youtube.com/@EthanChlebowski",
    "website_url": "https://www.youtube.com/@EthanChlebowski",
    "description": "Evidence-based cooking for better home meals",
    "category": "video"
  },
  {
    "name": "Sam the Cooking Guy",
    "source_type": "youtube",
    "url": "https://www.youtube.com/@samthecookingguy",
    "website_url": "https://www.youtube.com/@samthecookingguy",
    "description": "Simple, delicious meals with Sam Zien",
    "category": "video"
  },
  {
    "name": "Internet Shaquille",
    "source_type": "youtube",
    "url": "https://www.youtube.com/@InternetShaquille",
    "website_url": "https://www.youtube.com/@InternetShaquille",
    "description": "Practical cooking for real people",
    "category": "video"
  }
]
```

### Docker Container Integration

The Docker container needs a toggle for feed mode: local-only (Phase 5) or centralized (Phase 6).

**Settings:**
```
# .env
RECIPE_FEED_MODE=centralized              # "local" or "centralized"
RECIPE_FEED_API_URL=https://recipes.yourdomain.com  # Only needed for centralized
```

**Backend feed service:**
```python
# backend/app/services/feed_service.py

class FeedService:
    """Fetch new recipes from either local polling or centralized API."""

    async def get_new_recipes(self, since: datetime) -> list[Recipe]:
        mode = get_setting("recipe_feed_mode")

        if mode == "centralized":
            return await self._fetch_from_api(since)
        else:
            return await self._poll_local_sources(since)

    async def _fetch_from_api(self, since: datetime) -> list[Recipe]:
        """Pull new recipes from the centralized Cloudflare Worker API."""
        api_url = get_setting("recipe_feed_api_url")
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{api_url}/recipes/latest",
                params={"since": since.isoformat(), "limit": 50}
            )
            data = resp.json()

        recipes = []
        for r in data["recipes"]:
            recipe = Recipe(
                name=r["title"],
                type=r["recipe_type"],
                serves=r["serves"],
                prep_time=r["prep_time"],
                steps="\n".join(r["steps"]),
                source=r["original_url"],
                auto_imported=True,
                import_status="pending_review"
            )
            recipe.ingredients = [
                Ingredient(
                    name=i["name"],
                    quantity=f"{i['quantity'] or ''} {i['unit'] or ''}".strip(),
                    category=i["category"]
                ) for i in r["ingredients"]
            ]
            recipes.append(recipe)

        return recipes

    async def _poll_local_sources(self, since: datetime) -> list[Recipe]:
        """Fall back to local RSS/source polling (Phase 5 behavior)."""
        return await self.feed_checker.check_all_sources(since)

    async def get_available_sources(self) -> list[dict]:
        """Get list of sources the user can follow."""
        mode = get_setting("recipe_feed_mode")

        if mode == "centralized":
            api_url = get_setting("recipe_feed_api_url")
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{api_url}/sources")
                return resp.json()["sources"]
        else:
            # Return locally configured sources
            return [s.to_dict() for s in self.db.query(FollowedSource).all()]
```

### Deployment

The Cloudflare Worker is deployed separately from the Docker container:

```bash
# One-time setup
cd worker/
npm install
npx wrangler d1 create grocery-recipes
npx wrangler d1 execute grocery-recipes --file=src/db/schema.sql
npx wrangler d1 execute grocery-recipes --file=seed/seed.sql

# Deploy
npx wrangler deploy

# Seed initial sources
npx wrangler d1 execute grocery-recipes --command "INSERT INTO sources ..."
```

Users who want to self-host the Worker can deploy their own instance. Otherwise, they point their Docker container at the community-hosted instance.

### Cost Estimate (Cloudflare Free Tier)
- **Worker requests:** 100k/day free — more than enough for recipe API calls
- **D1 database:** 5M rows read/day, 100k writes/day free — plenty for ~50 sources
- **KV storage:** 100k reads/day, 1k writes/day free — fine for caching
- **Cron Triggers:** Free on all plans
- **Total cost:** $0/month on the free tier, even with hundreds of Docker instances pulling recipes
