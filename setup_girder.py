#!/usr/bin/env python
import json
import requests
import time
import os
import sys

params = {
    "login": "admin",
    "email": "root@dev.null",
    "firstName": "John",
    "lastName": "Doe",
    "password": "arglebargle123",
    "admin": True,
}
headers = {"Content-Type": "application/json", "Accept": "application/json"}


def final_msg():
    print("-------------- You should be all set!! -------------")
    print("try going to https://girder.local.wholetale.org and log in with: ")
    print("  user : %s" % params["login"])
    print("  pass : %s" % params["password"])


api_url = "https://girder.local.wholetale.org/api/v1"

# Give girder time to start
while True:
    print("Waiting for Girder to start")
    r = requests.get(api_url)
    if r.status_code == 200:
        break
    time.sleep(2)

print("Creating admin user")
r = requests.post(api_url + "/user", params=params, headers=headers)
if r.status_code == 400:
    print("Admin user already exists. Database was not purged.")
    print("If that is OK:")
    final_msg()
    sys.exit()

# Store token for future requests
headers["Girder-Token"] = r.json()["authToken"]["token"]

print("Creating default assetstore")
r = requests.post(
    api_url + "/assetstore",
    headers=headers,
    params={
        "type": 1,
        "name": "GridFS",
        "db": "gridfs",
        "shard": False,
        "replicaset": None,
    },
)

print("Enabling plugins")
plugins = [
    "oauth",
    "gravatar",
    "jobs",
    "worker",
    "globus_handler",
    "wt_data_manager",
    "wholetale",
    "wt_home_dir",
]
r = requests.put(
    api_url + "/system/plugins",
    headers=headers,
    params={"plugins": json.dumps(plugins)},
)
r.raise_for_status()

print("Restarting girder to load plugins")
r = requests.put(api_url + "/system/restart", headers=headers)
r.raise_for_status()

# Give girder time to restart
while True:
    print("Waiting for Girder to restart")
    r = requests.get(
        api_url + "/oauth/provider",
        headers=headers,
        params={"redirect": "http://blah.com"},
    )
    if r.status_code == 200:
        break
    time.sleep(2)

print("Setting up Plugin")

settings = [
    {
        "key": "core.cors.allow_origin",
        "value": "https://dashboard.local.wholetale.org,http://localhost:4200,https://legacy.local.wholetale.org",
    },
    {
        "key": "core.cors.allow_headers",
        "value": (
            "Accept-Encoding, Authorization, Content-Disposition, Set-Cookie, "
            "Content-Type, Cookie, Girder-Authorization, Girder-Token, "
            "X-Requested-With, X-Forwarded-Server, X-Forwarded-For, "
            "X-Forwarded-Host, Remote-Addr, Cache-Control"
        ),
    },
    {"key": "worker.api_url", "value": "http://girder:8080/api/v1"},
    {"key": "worker.broker", "value": "redis://redis/"},
    {"key": "worker.backend", "value": "redis://redis/"},
    {"key": "oauth.globus_client_id", "value": os.environ.get("GLOBUS_CLIENT_ID")},
    {
        "key": "oauth.globus_client_secret",
        "value": os.environ.get("GLOBUS_CLIENT_SECRET"),
    },
    {"key": "oauth.orcid_client_id", "value": os.environ.get("ORCID_CLIENT_ID")},
    {
        "key": "oauth.orcid_client_secret",
        "value": os.environ.get("ORCID_CLIENT_SECRET"),
    },
    #Deriva key and secret pair
    {"key": "oauth.providers_enabled", "value": ["globus","deriva"]},


    {"key": "oauth.deriva_client_id", "value": os.environ.get("DERIVA_CLIENT_ID")},
    {
        "key": "oauth.deriva_client_secret",
        "value": os.environ.get("DERIVA_CLIENT_SECRET"),
    },



    {"key": "dm.globus_gc_dir", "value": "/opt/globusconnectpersonal"},
    {
        "key": "wholetale.dataverse_extra_hosts",
        "value": ["dev2.dataverse.org", "demo.dataverse.org"],
    },
]

r = requests.put(
    api_url + "/system/setting", headers=headers, params={"list": json.dumps(settings)}
)
r.raise_for_status()

print("Create a Jupyter image")
i_params = {
    "config": json.dumps(
        {
            "command": (
                "jupyter notebook --no-browser --port {port} --ip=0.0.0.0 "
                "--NotebookApp.token={token} --NotebookApp.base_url=/{base_path} "
                "--NotebookApp.port_retries=0"
            ),
            "environment": ["CSP_HOSTS=dashboard.local.wholetale.org"],
            "memLimit": "2048m",
            "port": 8888,
            "targetMount": "/home/jovyan/work",
            "urlPath": "?token={token}",
            "buildpack": "PythonBuildPack",
            "user": "jovyan",
        }
    ),
    "icon": (
        "https://raw.githubusercontent.com/whole-tale/jupyter-base/master/"
        "squarelogo-greytext-orangebody-greymoons.png"
    ),
    "iframe": True,
    "name": "Jupyter Notebook",
    "public": True,
}
r = requests.post(api_url + "/image", headers=headers, params=i_params)
r.raise_for_status()
image = r.json()


print("Create an RStudio image")
i_params = {
    "config": json.dumps(
        {
            "command": "/start.sh",
            "environment": [
                "CSP_HOSTS=dashboard.local.wholetale.org",
                "PASSWORD=djkslajdklasjdklsajd",
            ],
            "memLimit": "2048m",
            "port": 8787,
            "targetMount": "/WholeTale",
            "urlPath": "",
            "buildpack": "RockerBuildPack",
            "user": "rstudio",
        }
    ),
    "icon": "https://www.rstudio.com/wp-content/uploads/" "2014/06/RStudio-Ball.png",
    "iframe": True,
    "name": "RStudio",
    "public": True,
}
r = requests.post(api_url + "/image", headers=headers, params=i_params)
r.raise_for_status()
image = r.json()

print("Create a JupyterLab image")
i_params = {
    "config": json.dumps(
        {
            "command": (
                "jupyter notebook --no-browser --port {port} --ip=0.0.0.0 "
                "--NotebookApp.token={token} --NotebookApp.base_url=/{base_path} "
                "--NotebookApp.port_retries=0"
            ),
            "environment": ["CSP_HOSTS=dashboard.local.wholetale.org"],
            "memLimit": "2048m",
            "port": 8888,
            "targetMount": "/home/jovyan/work",
            "urlPath": "lab?token={token}",
            "buildpack": "PythonBuildPack",
            "user": "jovyan",
        }
    ),
    "fullName": "xarthisius/jupyter",
    "icon": (
        "https://raw.githubusercontent.com/whole-tale/jupyter-base/master/"
        "squarelogo-greytext-orangebody-greymoons.png"
    ),
    "iframe": True,
    "name": "JupyterLab",
    "public": True,
}
r = requests.post(api_url + "/image", headers=headers, params=i_params)
r.raise_for_status()
image = r.json()

print("Create OpenRefine image")
i_params = {
    "config": json.dumps(
        {
            "memLimit": "2048m",
            "port": 3333,
            "targetMount": "/wholetale",
            "urlPath": "",
            "buildpack": "OpenRefineBuildPack",
            "user": "wtuser",
        }
    ),
    "icon": (
        "https://raw.githubusercontent.com/whole-tale/openrefine/master/openrefine_logo.png"
    ),
    "iframe": True,
    "name": "OpenRefine",
    "public": True,
}
r = requests.post(api_url + "/image", headers=headers, params=i_params)
r.raise_for_status()
image = r.json()

print("Create Jupyter Spark image")
i_params = {
    "config": json.dumps(
        {
            "command": (
                "jupyter notebook --no-browser --port {port} --ip=0.0.0.0 "
                "--NotebookApp.token={token} --NotebookApp.base_url=/{base_path} "
                "--NotebookApp.port_retries=0"
            ),
            "environment": ["CSP_HOSTS=dashboard.local.wholetale.org"],
            "memLimit": "2048m",
            "port": 8888,
            "targetMount": "/home/jovyan/work",
            "urlPath": "lab?token={token}",
            "buildpack": "SparkBuildPack",
            "user": "jovyan",
        }
    ),
    "icon": (
        "https://raw.githubusercontent.com/whole-tale/jupyter-base/master/"
        "squarelogo-greytext-orangebody-greymoons.png"
    ),
    "iframe": True,
    "name": "Jupyter with Spark",
    "public": True,
}
r = requests.post(api_url + "/image", headers=headers, params=i_params)
r.raise_for_status()
image = r.json()

print('Create Jupyter with R image')
i_params = {
    'config': json.dumps({
        'command': (
            'jupyter notebook --no-browser --port {port} --ip=0.0.0.0 '
            '--NotebookApp.token={token} --NotebookApp.base_url=/{base_path} '
            '--NotebookApp.port_retries=0'
        ),
        'environment': ['CSP_HOSTS=dashboard.local.wholetale.org'],
        'memLimit': '2048m',
        'port': 8888,
        'targetMount': '/home/jovyan/work',
        'urlPath': '?token={token}',
        'buildpack': 'RBuildPack',
        'user': 'jovyan'
    }),
    'icon': (
        'https://raw.githubusercontent.com/whole-tale/jupyter-base/master/'
        'squarelogo-greytext-orangebody-greymoons.png'
    ),
    'iframe': True,
    'name': 'Jupyter with R',
    'public': True
}
r = requests.post(api_url + '/image', headers=headers,
                  params=i_params)
r.raise_for_status()
image = r.json()

final_msg()
