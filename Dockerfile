FROM python:3.6-slim
# 更换阿里源
RUN printf "deb http://mirrors.aliyun.com/debian/ stretch main non-free contrib\n\
deb http://mirrors.aliyun.com/debian-security stretch/updates main\n\
deb http://mirrors.aliyun.com/debian/ stretch-updates main non-free contrib\n" > /etc/apt/sources.list

WORKDIR /app
COPY .  /app/

RUN apt-get update
# && apt-get install procps
RUN pip3 install -r requirements.txt

#&& python data/gen_data.py
RUN pip3 install -r requirements.txt  --no-cache
EXPOSE 8000/tcp
CMD ["sh","daemon.sh"]
