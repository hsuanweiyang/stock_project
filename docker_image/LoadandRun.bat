docker load < stock_dashboard.tar
docker run -d -it -p 1234:1234 --name stock_service stock_dashboard