[![Test](https://github.com/openfoodfacts/impactestimator/actions/workflows/test.yml/badge.svg)](https://github.com/openfoodfacts/impactestimator/actions/workflows/test.yml)

# impactestimator
Experimental service providing product level environmental impact for Open Food Facts products.

> [!WARNING]  
> This is paused, and we're now looking at Ecobalyse integration.

Crawls through productopener products with ingredients and nutrient tables to ensure they all have
computations provided by https://github.com/openfoodfacts/off-product-environmental-impact.

## Developing locally

Install a local productopener by following the instructions at https://github.com/openfoodfacts/openfoodfacts-server, then run the docker image in local dev mode:

```
docker-compose -f docker-compose-dev.yml up
```

## Running the tests

Run the docker image with the tests:

```
docker-compose -f docker-compose-test.yml up
```

