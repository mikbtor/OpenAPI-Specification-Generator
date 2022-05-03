#!/usr/bin/python

import xml.etree.ElementTree as ET
import type_models as tm
from dataclasses import asdict

types = []
used_types = set()
children_types = set()
ref_types = set()

ns = {"uml": "http://schema.omg.org/spec/UML/2.1", "xmi": "http://schema.omg.org/spec/XMI/2.1"}
tree = None


def get_types(type_guid) -> dict:
    """
    Create a dictionary of the types used by the paths, and any other types used by the referenced types by association or inheritance
    """
    global tree
    global used_types

    dTypes = {}
    at_tags = {}
    tg_name = ""
    s_req = ""
    a_req = []
    s_disc = ""
    elem = {}
    parent = {}

    build_ref_set(type_guid)

    for el in tree.findall(".//ownedAttribute/..[@{http://schema.omg.org/spec/XMI/2.1}type='uml:Class']"):
        bReq = False
        bDisc = False
        bInherits = False

        el_id = el.get("{http://schema.omg.org/spec/XMI/2.1}id")

        # Inheritance
        el_gen = el.find("generalization")
        if(el_gen is not None):
            idref = el_gen.get("general")
            parent = get_ref_type(idref)
            bInherits = True

        # Tags
        for x in tree.findall(".//tags/.."):
            if(el_id == x.get("{http://schema.omg.org/spec/XMI/2.1}idref")):
                for tg in x.findall(".//tags/tag"):
                    tg_name = tg.get("name")
                    tg_value = tg.get("value")
                    if(tg_name == "required"):
                        s_req = tg_value
                        a_req = s_req.split("|")
                        bReq = True
                    elif(tg_name == "discriminator"):
                        s_disc = tg_value
                        bDisc = True
        # Attributes
        attributes = {}
        for at in el.findall(".//ownedAttribute"):
            at_id = at.get("{http://schema.omg.org/spec/XMI/2.1}id")
            t_ref = at.find(".//type")
            at_assoc = at.get("association")
            # Attribute tags
            at_tags = get_attrib_tags(at_id)
            attributes[at.get("name")] = get_attrib_desc(t_ref.get("{http://schema.omg.org/spec/XMI/2.1}idref"))
            if(at_tags):
                for key in at_tags.keys():
                    attributes[at.get("name")][key] = at_tags[key]

        # Put everything together
        if not bInherits:
            elem = {"type": "object", "properties": attributes}
            if bReq:
                elem = {"required": a_req, "type": "object", "properties": attributes}
            if bDisc:
                elem["discriminator"] = {"propertyName": s_disc}
        else:
            elem = {"allOf": [parent, {"type": "object", "properties": attributes}]}
            if (bReq):
                elem["required"] = s_req
            if (bDisc):
                elem["discriminator"] = {"propertyName": s_disc}

        # In the element inherits from a class, then "allOf" tag has to be included
        if el_id in used_types:
            dTypes[el.get("name")] = elem

    # Enumerations
    for el in tree.findall(".//packagedElement[@{http://schema.omg.org/spec/XMI/2.1}type='uml:Enumeration']"):
        attrs = []
        for at in el.findall(".//ownedLiteral"):
            attrs.append(at.get("name"))
        dTypes[el.get("name")] = {"type": "string", "enum": attrs}
  
    # Sort the dictionary
    keys=[]
    for k in dTypes:
      keys.append(k)
    
    sorted_keys = sorted(keys)
    sorted_dict = {}
    
    for k in sorted_keys:
      sorted_dict[k]=dTypes[k]


    # Error
    sorted_dict["Error"] = tm.error

    return sorted_dict


def build_ref_set(type_guid) -> dict:
    """
    Create a dictionary of the types used by the paths, and any other types used by the referenced types by association or inheritance
    """
    global tree
    global used_types
    global children_types
    global ref_types
  
    # Inheritance - adds only one level of inheritance
    for type in tree.findall(".//element"):
        if type.get("{http://schema.omg.org/spec/XMI/2.1}type") == "uml:Class":
          type_id = type.get("{http://schema.omg.org/spec/XMI/2.1}id")
          links = type.find("links")
          if links is not None:
            for gen in links.findall(".//Generalization"):
              start = gen.get("start")
              end = gen.get("end")
              if end in used_types:
                children_types.add(start)
            for assoc in links.findall(".//Association"):
              start = assoc.get("start")
              end = assoc.get("end")
              if start in used_types:
                ref_types.add(end)

    used_types = set.union(used_types, children_types, ref_types)


def build_dic(type_guid) -> dict:
    """
    Create a dictionary of the types used by the paths, and any other types used by the referenced types by association or inheritance
    """
    global tree
    global used_types

    dTypes = {}
    at_tags = {}
    tg_name = ""
    s_req = ""
    a_req = []
    s_disc = ""
    elem = {}
    parent = {}

    for el in tree.findall(".//ownedAttribute/..[@{http://schema.omg.org/spec/XMI/2.1}type='uml:Class']"):
        bReq = False
        bDisc = False
        bInherits = False

        el_id = el.get("{http://schema.omg.org/spec/XMI/2.1}id")

        # Inheritance
        el_gen = el.find("generalization")
        if(el_gen is not None):
            idref = el_gen.get("general")
            parent = get_ref_type(idref)
            bInherits = True

        # Tags
        for x in tree.findall(".//tags/.."):
            if(el_id == x.get("{http://schema.omg.org/spec/XMI/2.1}idref")):
                for tg in x.findall(".//tags/tag"):
                    tg_name = tg.get("name")
                    tg_value = tg.get("value")
                    if(tg_name == "required"):
                        s_req = tg_value
                        a_req = s_req.split("|")
                        bReq = True
                    elif(tg_name == "discriminator"):
                        s_disc = tg_value
                        bDisc = True
        # Attributes
        attributes = {}
        for at in el.findall(".//ownedAttribute"):
            at_id = at.get("{http://schema.omg.org/spec/XMI/2.1}id")
            t_ref = at.find(".//type")
            at_assoc = at.get("association")
            if at_assoc is not None:
                children_types.add(at_assoc)
            # Attribute tags
            at_tags = get_attrib_tags(at_id)
            attributes[at.get("name")] = get_attrib_desc(t_ref.get("{http://schema.omg.org/spec/XMI/2.1}idref"))
            if(at_tags):
                for key in at_tags.keys():
                    attributes[at.get("name")][key] = at_tags[key]

        # Put everything together
        if not bInherits:
            elem = {"type": "object", "properties": attributes}
            if bReq:
                elem = {"required": a_req, "type": "object", "properties": attributes}
            if bDisc:
                elem["discriminator"] = {"propertyName": s_disc}
        else:
            elem = {"allOf": [parent, {"type": "object", "properties": attributes}]}
            if (bReq):
                elem["required"] = s_req
            if (bDisc):
                elem["discriminator"] = {"propertyName": s_disc}

        # In the element inherits from a class, then "allOf" tag has to be included
        if el_id in used_types:
            dTypes[el.get("name")] = elem

    # Enumerations
    for el in tree.findall(".//packagedElement[@{http://schema.omg.org/spec/XMI/2.1}type='uml:Enumeration']"):
        attrs = []
        for at in el.findall(".//ownedLiteral"):
            attrs.append(at.get("name"))
        dTypes[el.get("name")] = {"type": "string", "enum": attrs}
    dTypes["Error"] = tm.error

    for s in children_types:
        print(s)
    return dTypes


def get_attrib_desc(type_ref: str) -> dict:
    """
    Takes as input one of the EA types and returns an Open API friendly representation
    Types can be either basic types, objects or arrays of either basic types or objects
    """
    global tree
    r = {}
    name = ''

    if(type_ref.find("int") > -1):
        r = {"type": "integer", "format": "int32"}
    elif(type_ref.find("float") > -1):
        r = {"type": "number", "format": "float"}
    elif(type_ref.find("double") > -1):
        r = {"type": "number", "format": "double"}
    elif(type_ref.find("numeric") > -1):
        r = {"type": "string"}
    elif(type_ref.find("date") > -1):
        r = {"type": "string", "format": "date"}
    elif(type_ref.find("time") > -1):
        r = {"type": "string", "format": "time"}
    elif(type_ref.find("string") > -1):
        r = {"type": "string"}
    elif(type_ref.find("EAID") > -1):
        for el in tree.findall(".//element"):
            if(el.get("{http://schema.omg.org/spec/XMI/2.1}idref") == type_ref):
                name = el.get("name")
        for el in tree.findall(".//target"):
            if(el.get("{http://schema.omg.org/spec/XMI/2.1}idref") == type_ref):
                t_el = el.find("type")
                mult = t_el.get("multiplicity")
                if(mult.find("*") > -1):
                    r = {"type": "array", "items":  {"$ref": '#/components/schemas/{}'.format(name)}}
                else:
                    r = {"$ref": '#/components/schemas/{}'.format(name)}
                break
    return r


def get_ref_type(type_ref: str) -> dict:
    """
    The type reference starts with EAID. It returns the object name
    """
    global tree
    r = {}
    name = ''
    for el in tree.findall(".//element"):
        if(el.get("{http://schema.omg.org/spec/XMI/2.1}idref") == type_ref):
            name = el.get("name")
            r = {"$ref": '#/components/schemas/{}'.format(name)}
            break
    return r


def get_attrib_tags(attrib_id: str) -> dict:
    global tree
    tags = {}
    for el in tree.findall(".//attribute"):
        if(el.get("{http://schema.omg.org/spec/XMI/2.1}idref") == attrib_id):
            tags = {}
            for tg in el.findall(".//tags/tag"):
                s_val = tg.get("value")
                s_name = tg.get("name")
                if(s_val == 'true'):
                    tags[s_name] = True
                elif(s_val == 'false'):
                    tags[s_name] = False
                elif(s_val.isdigit()):
                    tags[s_name] = int(s_val)
                else:
                    tags[s_name] = s_val
    return tags

def get_security_scheme(security: str) -> dict:
  sec_scheme = {}
  match security:
    case "basic":
      sec_scheme={'basicAuth':  {'type': 'http', 'scheme': 'basic'}}
    case "api key":
      sec_scheme = {'ApiKeyAuth': {'type': 'apiKey', 'in': 'header', 'name': 'X-API-KEY'}}
    case "bearer token":
      sec_scheme = {'BearerToken': {'type': 'http', 'scheme': 'bearer', 'bearerFormat': 'JWT'}}
    case "oauth - implicit flow":
      sec_scheme ={'OAuth': { 'type': 'oauth2', 'flows': { 'implicit': { 'authorizationUrl': 'https://example.com/api/oauth/dialog', 'scopes': { 'write:pets': 'modify pets in your account','read:pets': 'read your pets'}}}}}        
    case "oauth - authorization code flow":
      sec_scheme ={'OAuth': { 'type': 'oauth2', 'flows': { 'implicit': { 'authorizationUrl': 'https://example.com/api/oauth/dialog', 'scopes': { 'write:pets': 'modify pets in your account','read:pets': 'read your pets'}}}}}
  return sec_scheme

def get_security(security: str) -> list:
  sec = []
  match security:
    case "basic":
      sec =[{'basicAuth':[]}]
    case "api key":
      sec = [{'ApiKeyAuth':[]}]
    case "bearer token":
      sec = [{'BearerToken': []}]
    case "oauth - implicit flow":
      sec = [{'OAuth': []}]
    case "oauth - authorization code flow":
      sec = [{'OAuth': []}]
  return sec        
