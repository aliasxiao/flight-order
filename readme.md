### 1.项目简介
该项目主要主要功能是一个机票预定、支付、取消以及航班查询。项目实现语言为python3，使用web框架为tornado，数据存储使用mysql，缓存用到了redis。基于docker-compose构建项目镜像，使得项目可以方便的用于测试、部署。
### 2.项目启动
docker-compose build

docker-compose up

### 3.测试
运行tests下test_flight_order.py文件