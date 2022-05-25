#!/usr/bin/python

import xml.etree.ElementTree as ET
from models import path_models as pm
import type_gen as tg

tree = None
p_paths = set()


def r_200(description: str, return_dict: str,  content_type: str = 'application/json') -> dict:
    """ Method used to create the 200 response
    """
    r = {'description': description, 'content': {content_type: return_dict}}
    return r


r_400 = {'description': 'Bad Request', 'content': {
    'application/problem+json': {'schema': {'$ref': '#/components/schemas/Error'}}}}
r_401 = {"description": "Unauthorized"}
r_403 = {"description": "Forbidden"}
r_500 = {'description': 'Internal Server Error', 'content': {
    'application/problem+json': {'schema': {'$ref': '#/components/schemas/Error'}}}}


def get_paths(paths_guid: str) -> dict:
    """
        Parse the model and return the paths under the paths-guid
    """
    global tree
    global p_paths

    paths = {}
    params = {}
    path_tag = ''
    path_url = ""
    path_name = ''

    # Find the package for the paths_guid
    build_paths_set(paths_guid)

    # Iterate through the element list
    for path in tree.findall(".//element"):
        if path.get("{http://schema.omg.org/spec/XMI/2.1}type") == "uml:Interface" and path.get("{http://schema.omg.org/spec/XMI/2.1}idref") in p_paths:
            path_name = path.get('name')
            # Tags
            tags = path.findall(".//tag")
            for tag in tags:
                if(tag.get("name") == "path"):
                    path_url = tag.get('value').split("#")[0]
                if(tag.get("name") == "apiTag"):
                    path_tag = tag.get("value").split("#")[0]

            # Operations
            operations = {}
            for op in path.findall(".//operation"):
                op_styp = op.find(".//stereotype").get("stereotype")
                op_name = '{}.{}'.format(path_name.lower(), op.get("name"))
                params, ret_dict = get_op_params(path_url, op)
                if(op_styp == "GET"):
                    operations[op_styp.lower()] = {
                        "tags": [path_tag], "operationId": op_name, "parameters": params, "responses": {
                            200: r_200("Search results", ret_dict), 400: r_400.copy(), 401: r_401.copy(), 500: r_500.copy()}}
                elif(op_styp == "PATCH"):
                    operations[op_styp.lower()] = {
                        "tags": [path_tag], "operationId": op_name, "parameters": params, "requestBody": get_req_body(op), "responses": {
                            200: {"description": "Update successful"}, 400: r_400, 401: r_401.copy(), 500: r_500.copy()}}
                elif(op_styp == "POST"):
                    operations[op_styp.lower()] = {
                        "tags": [path_tag], "operationId": op_name, "parameters": params, "requestBody": get_req_body(op), "responses": {
                            201: {"description": "Create successful"}, 400: r_400.copy(), 401: r_401.copy(), 500: r_500.copy()}}
                elif(op_styp == "DELETE"):
                    operations[op_styp.lower()] = {
                        "tags": [path_tag], "operationId": op_name, "parameters": params, "responses": {
                            200: {"description": "Delete successful"}, 400: r_400.copy(), 401: r_401.copy(), 500: r_500.copy()}}
                elif(op_styp == "PUT"):
                    operations[op_styp.lower()] = {
                        "tags": [path_tag], "operationId": op_name, "parameters": params, "requestBody": get_req_body(op), "responses": {
                            200: {"description": "Update successful"}, 400: r_400.copy(), 401: r_401.copy(), 500: r_500.copy()}}

            # Add to dictionary
            paths[path_url] = operations
    return paths


def get_op_params(path_url: str, op: ET) -> tuple:
    global tree
    params = []
    ret = {}
    prm = {}
    path_param = ""
    op_id = op.get("{http://schema.omg.org/spec/XMI/2.1}idref")
    op_stereotype = op.find(".//stereotype").get("stereotype")
    op_name = op.get("name")

    #print(op_name, op_stereotype, op_id)

    # Accept language
    params.append({"name": "Accept-Language", "in": "header", "schema": {"type": "string"}})
    # Path parameter
    path_parts = path_url.split('/')
    for part in path_parts:
        if part.find("{") > -1:
            n1 = part.find("{")
            n2 = part.find("}")
            path_param = part[n1+1:n2]
            params.append({"name": path_param, "in": "path", "schema": {"type": "string"}, "required": True})

    for ow in tree.findall(".//ownedOperation"):
        ow_id = ow.get("{http://schema.omg.org/spec/XMI/2.1}id")

        if (op_id == ow_id):
            for param in ow.findall(".//ownedParameter"):
                # p_id = param.get("{http://schema.omg.org/spec/XMI/2.1}id")
                p_type = param.get("type")
                p_name = param.get("name")
                if(p_name != "return" and (op_stereotype.find("GET")>-1 )):
                    # Method parameters
                    # Basic types - do not take into account parameters that are objects
                    prm["name"] = p_name
                    prm["in"] = "query"
                    if(p_type.find("__") == -1):
                        # single instance
                        if(p_type.find("int") > -1):
                            prm["schema"] = {"type": "integer", "format": "int32"}
                        elif(p_type.find("float") > -1):
                            prm["schema"] = {"type": "number", "format": "float"}
                        elif(p_type.find("double") > -1):
                            prm["schema"] = {"type": "number", "format": "double"}
                        elif(p_type.find("date") > -1):
                            prm["schema"] = {"type": "string", "format": "date"}
                        elif(p_type.find("string") > -1):
                            prm["schema"] = {"type": "string"}
                        else:
                            if p_type.find("EAID") > -1:
                                tg.used_types.add(p_type)
                                prm["schema"] = tg.get_ref_type(p_type)
                            else:
                                s_type = p_type.split("_")
                                if s_type[1].find("void") == -1:
                                    tg.used_types.add(tg.get_id_by_name(s_type[1]))
                                    prm["schema"] = tg.get_ref_type(s_type[1])

                    else:
                        # array
                        if(p_type.find("int") > -1):
                            prm["schema"] = {"type": "array", "items": {"type": "number", "format": "int32"}}
                        elif(p_type.find("float") > -1):
                            prm["schema"] = {"type": "array", "items": {"type": "number", "format": "float"}}
                        elif(p_type.find("double") > -1):
                            prm["schema"] = {"type": "array", "items": {"type": "number", "format": "double"}}
                        elif(p_type.find("date") > -1):
                            prm["schema"] = {"type": "array", "items": {"type": "string", "format": "date"}}
                        elif(p_type.find("string") > -1):
                            prm["schema"] = {"type": "array", "items": {"type": "string"}}
                        else:
                            prm["schema"] = {"type": "array", "items": {"type": "string"}}
                        prm["style"] = "form"
                        prm["explode"] = False
                    params.append(prm.copy())
                else:
                    # Return parameter
                    if(p_type.find("__") == -1):
                        # Single instance
                        if(p_type.find("int") > -1):
                            ret["schema"] = {"type": "integer", "format": "int32"}
                        elif(p_type.find("float") > -1):
                            ret["schema"] = {"type": "number", "format": "float"}
                        elif(p_type.find("double") > -1):
                            ret["schema"] = {"type": "number", "format": "double"}
                        elif(p_type.find("date") > -1):
                            ret["schema"] = {"type": "string", "format": "date"}
                        elif(p_type.find("string") > -1):
                            ret["schema"] = {"type": "string"}
                        else:
                            if p_type.find("EAID") > -1:
                                tg.used_types.add(p_type)
                                ret["schema"] = tg.get_ref_type(p_type)
                            else:
                                s_type = p_type.split("_")
                                if(s_type[1].find("void") == -1):
                                    tg.used_types.add(tg.get_id_by_name(s_type[1]))
                                    ret["schema"] = tg.get_ref_type(p_type)

                    else:
                        if(p_type.find("int") > -1):
                            ret["schema"] = {"type": "array", "items": {"type": "number", "format": "int32"}}
                        elif(p_type.find("float") > -1):
                            ret["schema"] = {"type": "array", "items": {"type": "number", "format": "float"}}
                        elif(p_type.find("double") > -1):
                            ret["schema"] = {"type": "array", "items": {"type": "number", "format": "double"}}
                        elif(p_type.find("date") > -1):
                            ret["schema"] = {"type": "array", "items": {"type": "string", "format": "date"}}
                        elif(p_type.find("string") > -1):
                            ret["schema"] = {"type": "array", "items": {"type": "string"}}
                        else:
                            if p_type.find("EAID") > -1:
                                tg.used_types.add(p_type)
                                ret["schema"] = {"type": "array", "items": {"$ref": '#/components/schemas/{}'.format(p_type[7:-2])}}
                            else:
                                s_type = p_type.split("_")
                                if s_type[1].find("void") == -1:
                                    tg.used_types.add(tg.get_id_by_name(s_type[1]))
                                    ret["schema"] = {"type": "array", "items": {"$ref": '#/components/schemas/{}'.format(p_type[7:-2])}}
            break
    if  op.find(".//stereotype").get("stereotype") == "GET" and op.get("name").find("search")>-1:
        params.append({"name": "offset", "in": "query", "schema": {"type": "integer", "format":"int32"}})
        params.append({"name": "page_size", "in": "query", "schema": {"type": "integer", "format":"int32"}})
    return params, ret


def get_req_body(op: ET) -> list:
    global tree
    req_body = {}

    op_id = op.get("{http://schema.omg.org/spec/XMI/2.1}idref")

    for ow in tree.findall(".//ownedOperation"):
        ow_id = ow.get("{http://schema.omg.org/spec/XMI/2.1}id")
        if (op_id == ow_id):
            for param in ow.findall(".//ownedParameter"):
                p_type = param.get("type")
                p_name = param.get("name")

                if(p_name != "return"):
                    if(p_type.find("EAID") > -1):
                        tg.used_types.add(p_type)
                        req_body = {'content': {'application/json': {'schema': tg.get_ref_type(p_type)}}}
    return req_body


def find_owned_operation(packages, path_id: str, op_id: str):
    ownedOp = None
    for x in packages:
        if x.getAttribute("xmi:type") == "uml:Interface":
            id = x.getAttribute("xmi:id")
            if(id == path_id):
                ownedOps = x.getElementsByTagName("ownedOperation")
                for o in ownedOps:
                    o_id = o.getAttribute("xmi:id")
                    if (o_id == op_id):
                        ownedOp = o
                        break
    return ownedOp


def build_paths_set(paths_guid: str):
    global tree
    for p in tree.findall(".//packagedElement"):
        if p.get("{http://schema.omg.org/spec/XMI/2.1}type") == "uml:Package":
            p_id = p.get("{http://schema.omg.org/spec/XMI/2.1}id")
            if (p_id is not None) and (p_id.find(paths_guid) > -1):
                add_paths(p)
                break


def add_paths(p):
    global p_paths
    for pp in p.findall(".//packagedElement"):
        if pp.get("{http://schema.omg.org/spec/XMI/2.1}type") == "uml:Interface":
            # Find the element in the extension
            el_id = pp.get("{http://schema.omg.org/spec/XMI/2.1}id")
            el_ext = tree.find(f".//element[@{{http://schema.omg.org/spec/XMI/2.1}}idref='{el_id}']")
            # Process only if stereotype is <<Resource>>
            el_props = el_ext.find("./properties")
            if el_props.get("stereotype").lower() == "path":
                p_paths.add(pp.get("{http://schema.omg.org/spec/XMI/2.1}id"))
        elif pp.get("{http://schema.omg.org/spec/XMI/2.1}type") == "uml:Package":
            add_paths(pp)
