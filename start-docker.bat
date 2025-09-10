@echo off
echo Building and starting Circle Management Platform with Docker...
echo.
echo Building Docker image...
docker-compose build
echo.
echo Starting containers...
docker-compose up -d
echo.
echo Platform is now running at http://localhost:8060
echo.
echo To view logs: docker-compose logs -f
echo To stop: docker-compose down
echo.
pause
