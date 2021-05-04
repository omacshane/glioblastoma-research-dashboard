FROM ubuntu
RUN apt-get update
RUN apt-get update \
  && apt-get install -y python3-pip python3-dev \
  && cd /usr/local/bin \
  && ln -s /usr/bin/python3 python \
  && pip3 install --upgrade pip

ADD requirements.txt /requirements.txt

ADD . /.

RUN pip3 install -r /requirements.txt

EXPOSE 8501

CMD streamlit run src/streamlit_app.py