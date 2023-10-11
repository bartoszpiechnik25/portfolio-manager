FROM python:3.10.13

RUN cd /tmp && apt update
RUN wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb && apt install -y ./google-chrome-stable_current_amd64.deb
RUN google-chrome --version && which google-chrome
RUN wget 'https://www.googleapis.com/download/storage/v1/b/chromium-browser-snapshots/o/Linux_x64%2F1181205%2Fchromedriver_linux64.zip?generation=1691535840427415&alt=media' && unzip 'Linux_x64%2F1181205%2Fchromedriver_linux64.zip?generation=1691535840427415&alt=media'\
 && mv chromedriver_linux64/chromedriver /usr/bin/chromedriver\
 && chmod +x /usr/bin/chromedriver

WORKDIR /app

COPY ../.. /app
RUN pip install --no-cache-dir -r requirements.txt

CMD [ "flask", "run" ]
