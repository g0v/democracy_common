FROM python:3.6


ADD constituency.py /

RUN pip install requests asks trio lxml html5lib BeautifulSoup4 pandas

CMD [ "python", "./constituency.py" ]
