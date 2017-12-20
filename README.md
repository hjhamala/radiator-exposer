# Radiator exposer

Radiator is a AWS Lambda which exposes account CodePipeline statuses and CloudWatch alerts as
json data structure. CloudWatch metrics can be also exposed. See handler.py commented section for
way to expose metrics.

## Installation to AWS
Change region in serverless.yml to region which is to be monitored.

Prerequirements
* NPM 
* Python pip

Run

    make 
    npm install serverless serverless-python-requirements
    serverless deploy 

Take note of the endpoint and api key.

## License

https://opensource.org/licenses/BSD-2-Clause

Copyright © 2017 Heikki Hämäläinen
