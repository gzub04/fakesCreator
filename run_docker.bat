@echo off
del /Q .\Data\generated_documents\*
docker build -t gzub04/fakes_creator .
docker run --name fakes_container gzub04/fakes_creator
docker cp fakes_container:/fakesCreator/Data/generated_documents .\Data
timeout /t 1
docker rm fakes_container
docker image prune -f
PAUSE