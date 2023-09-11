docker run -it --name fakes_container -v %cd%/data/sources:/fakesCreator/data/sources fakes_creator -h
docker cp fakes_container:/fakesCreator/output .\
timeout /t 1
docker rm fakes_container
docker image prune -f
PAUSE
