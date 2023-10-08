FROM continuumio/miniconda3

WORKDIR /app
COPY ../.. /app
RUN conda create -n flask python=3.10
RUN echo "source activate flask" > ~/.bashrc
RUN pip install --no-cache-dir -r requirements.txt
ENV PATH /opt/conda/envs/flask/bin:$PATH

CMD [ "flask", "run" ]
