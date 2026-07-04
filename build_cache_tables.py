from __future__ import annotations

import northamerica as na
import worldwide as world


def write_cache_tables(module: object, label: str) -> None:
    module.CACHE_DIR.mkdir(exist_ok=True)

    airports = module.compute_airport_table()
    routes = module.compute_flight_route_table()

    airports.to_csv(module.AIRPORT_CACHE_CSV, index=False)
    routes.to_csv(module.FLIGHT_ROUTE_CACHE_CSV, index=False)

    print(f"Wrote {len(airports):,} {label} airports to {module.AIRPORT_CACHE_CSV}")
    print(f"Wrote {len(routes):,} {label} flight routes to {module.FLIGHT_ROUTE_CACHE_CSV}")


def main() -> None:
    write_cache_tables(na, "North America")
    write_cache_tables(world, "worldwide")


if __name__ == "__main__":
    main()
