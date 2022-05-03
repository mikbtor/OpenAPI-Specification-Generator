#!/usr/bin/python

from dataclasses import dataclass, field

@dataclass
class Parameter:
    id: str = field(repr=False)
    name:str
    location: str # in the Open API Spec is called 'in'. May be one of {header, path, query}
    schema: dict   # may be {"type":"", "format":""} or {"$ref":"#/components/schemas/..."} or  {'type': 'array', 'items': { 'type': ''},'style': 'pipeDelimited','explode': 'false'}

@dataclass
class RequestBody:
    id: str = field(repr=False)
    content: dict  #{"application/json": { "schema": { "$ref": '#/components/schemas/'}}}

@dataclass
class Operation:
    tags: str
    operationId: str
    parameters: list
    requestBody: dict
    responses: dict

@dataclass
class ApiSpec:
    openapi: str = field(init=False)
    info: dict = field(init=False)
    tags: list = field(init=False)
    servers: list = field(init=False)
    paths: dict = field(init=False)
    components: dict = field(init=False)
    security: dict = field(init = False)

    def __post_init__(self):
        self.openapi = '3.0.2'
        self.info = { "version": '1.0', "title": "Open API Definition", "description": "API Definitions"}
        self.tags = []
        self.servers = [{"url":"http://localhost:8080", "description": "development server"}]
        self.paths = {}
        self.components = {"schemas":{}}       
    