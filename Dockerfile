FROM scipoptsuite/scipoptsuite:7.0.2

RUN python -m pip install --upgrade pip
RUN python -m pip install pyscipopt statsmodels sklearn ipython openfoodfacts fastapi uvicorn[standard] progressbar2 aiohttp
RUN apt-get update --allow-releaseinfo-change
RUN apt-get -y install git
RUN git clone https://github.com/openfoodfacts/off-product-environmental-impact.git impact
ENV PYTHONPATH=$PYTHONPATH:/impact

WORKDIR /app
COPY . ./
