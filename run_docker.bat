@echo off
del /Q C:\PythonProjects\fakesCreator\Data\generated_documents\*
docker build -t gzub04/fakes_creator .
docker run --name fakes_container gzub04/fakes_creator
docker cp fakes_container:/fakesCreator/Data/generated_documents C:\PythonProjects\fakesCreator\Data
docker rm fakes_container
