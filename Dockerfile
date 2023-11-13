FROM scipoptsuite/scipoptsuite:8.0.4

# commit hash or refs/heads/master or refs/tags/v0.0.1 ...
ARG IMPACT_LIB_REF=refs/heads/master

RUN python -m pip install --upgrade pip && \
    python -m pip install \
        pyscipopt statsmodels sklearn ipython openfoodfacts fastapi uvicorn[standard] \
        progressbar2 aiohttp bson python-multipart pytype
RUN apt-get update --allow-releaseinfo-change && \
    apt-get -y install curl unzip
# install impact estimator library by just pulling source in impact folder
RUN curl -L -o impact.zip https://github.com/openfoodfacts/off-product-environmental-impact/archive/$IMPACT_LIB_REF.zip && \
    unzip impact.zip && \
    mv off-product-environmental-impact-* impact && \
    rm impact.zip
ENV PYTHONPATH=$PYTHONPATH:/impact

WORKDIR /app
COPY . ./
CMD ["python", "main.py"]
