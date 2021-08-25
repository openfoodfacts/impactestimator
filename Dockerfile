FROM scipoptsuite/scipoptsuite:7.0.2

RUN apt-get update --allow-releaseinfo-change
RUN python -m pip install pyscipopt statsmodels sklearn ipython openfoodfacts fastapi uvicorn[standard] progressbar2
RUN apt-get -y install git
RUN git clone https://framagit.org/GustaveCoste/off-product-environmental-impact.git impact
ENV PYTHONPATH=$PYTHONPATH:/impact

WORKDIR /app
COPY . ./
CMD ["uvicorn", "--reload", "--host", "0.0.0.0", "main:app"]
