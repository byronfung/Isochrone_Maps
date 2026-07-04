from __future__ import annotations

import northamerica as na


def main() -> None:
    na.CACHE_DIR.mkdir(exist_ok=True)

    airports = na.compute_airport_table()
    routes = na.compute_flight_route_table()

    airports.to_csv(na.AIRPORT_CACHE_CSV, index=False)
    routes.to_csv(na.FLIGHT_ROUTE_CACHE_CSV, index=False)

    print(f"Wrote {len(airports):,} airports to {na.AIRPORT_CACHE_CSV}")
    print(f"Wrote {len(routes):,} flight routes to {na.FLIGHT_ROUTE_CACHE_CSV}")


if __name__ == "__main__":
    main()
