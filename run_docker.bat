docker run --name fakes_container -v %cd%/data/sources:/fakesCreator/data/sources gzub04/fakes_creator
docker cp fakes_container:/fakesCreator/output .\
timeout /t 1
docker rm fakes_container
docker image prune -f
PAUSE
