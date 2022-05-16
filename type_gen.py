#!/usr/bin/python

import xml.etree.ElementTree as ET

#from zmq import THREAD_AFFINITY_CPU_REMOVE
import models.type_models as tm
from dataclasses import asdict

types = []
basic_types = {"int", "float", "double", "numberic", "date", "time", "datetime", "boolean", "string"}
basic_type_formats = {"int": {"type": "integer", "format": "int32"},
                      "float": {"type": "number", "format": "float"},
                      "double": {"type": "number", "format": "double"},
                      "numeric": {"type": "string"},
                      "date": {"type": "string", "format": "date"},
                      "time": {"type": "string", "format": "time"},
                      "datetime": {"type": "string", "format": "datetime"},
                      "boolean": {"type": "boolean"},
                      "string": {"type": "string"}}
used_types = set()
children_types = set()
ref_types = set()

ns = {"uml": "http://schema.omg.org/spec/UML/2.1", "xmi": "http://schema.omg.org/spec/XMI/2.1"}
tree = None


def get_types(type_guid) -> dict:
    """
    Create a dictionary of the types used by the paths,
    and any other types used by the referenced types by association or inheritance
    """
    global tree
    global used_types

    dTypes = {}
    at_tags = {}
    tg_name = ""
    s_req = ""
    a_req = []
    s_disc = ""
    parent = {}

    build_ref_set(type_guid)

    # find all the classes that have ownedAttributes
    for el in tree.findall(".//ownedAttribute/..[@{http://schema.omg.org/spec/XMI/2.1}type='uml:Class']"):
        bReq = False
        bDisc = False
        bInherits = False
        elem = {}

        el_id = el.get("{http://schema.omg.org/spec/XMI/2.1}id")

        # Inheritance
        el_gen = el.find("generalization")
        if(el_gen is not None):
            idref = el_gen.get("general")
            parent = get_ref_type(idref)
            bInherits = True

        # Find the element in the extension
        el_ext = tree.find(f".//element[@{{http://schema.omg.org/spec/XMI/2.1}}idref='{el_id}']")
      
        # Tags for the element       
        for tg in el_ext.findall(".//tags/tag"):
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
        for at in el_ext.findall(".//attributes/attribute"):
            attribute = {}
            at_tags = {}
            p = at.find("./properties")
            at_type = p.get("type")
            attribute = get_attrib_desc(at_type)

            # Attribute tags
            at_tags = at.findall(f".//tags/tag")
            for at_tg in at_tags:
              s_val = at_tg.get("value")
              s_name = at_tg.get("name")
              if(s_val == 'true'):
                  attribute.update({s_name:True})
              elif(s_val == 'false'):
                  attribute.update({s_name:False})
              elif(s_val.isdigit()):
                  attribute.update({s_name:int(s_val)})
              else:
                  attribute.update({s_name:s_val})
            attributes.update({at.get("name"):attribute.copy()})

        # Associations
        for a in el_ext.findall("./links/Association"):
          target_id = a.get("end")
          if(target_id != el_id):
            target =  tree.find(f".//connectors/connector/target[@{{http://schema.omg.org/spec/XMI/2.1}}idref='{target_id}']")
            t_name = target.find("./role").get("name")
            t_mult = target.find("./type").get("multiplicity")
            t_type = target.find("./model").get("name")
            if(t_mult.find("*") > -1):
                attributes[t_name] = {"type": "array", "items":  {"$ref": f'#/components/schemas/{t_type}'}}
            else:
                attributes[t_name] = {"$ref": f"#/components/schemas/{t_type}"}

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
            dTypes.update({el.get("name"): elem.copy()})

    # Enumerations
    for el in tree.findall(".//packagedElement[@{http://schema.omg.org/spec/XMI/2.1}type='uml:Enumeration']"):
        attrs = []
        for at in el.findall(".//ownedLiteral"):
            attrs.append(at.get("name"))
        dTypes[el.get("name")] = {"type": "string", "enum": attrs}

    # Sort the dictionary
    keys = []
    for k in dTypes:
        keys.append(k)

    sorted_keys = sorted(keys)
    sorted_dict = {}

    for k in sorted_keys:
        sorted_dict[k] = dTypes[k]

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


# def build_dic(type_guid) -> dict:
#     """
#     Create a dictionary of the types used by the paths,
#     and any other types used by the referenced types by association or inheritance
#     """
#     global tree
#     global used_types

#     dTypes = {}
#     at_tags = {}
#     tg_name = ""
#     s_req = ""
#     a_req = []
#     s_disc = ""
#     elem = {}
#     parent = {}

#     for el in tree.findall(".//ownedAttribute/..[@{http://schema.omg.org/spec/XMI/2.1}type='uml:Class']"):
#         bReq = False
#         bDisc = False
#         bInherits = False

#         el_id = el.get("{http://schema.omg.org/spec/XMI/2.1}id")

#         # Inheritance
#         el_gen = el.find("generalization")
#         if(el_gen is not None):
#             idref = el_gen.get("general")
#             parent = get_ref_type(idref)
#             bInherits = True

#         # Tags
#         for x in tree.findall(".//tags/.."):
#             if(el_id == x.get("{http://schema.omg.org/spec/XMI/2.1}idref")):
#                 for tg in x.findall(".//tags/tag"):
#                     tg_name = tg.get("name")
#                     tg_value = tg.get("value")
#                     if(tg_name == "required"):
#                         s_req = tg_value
#                         a_req = s_req.split("|")
#                         bReq = True
#                     elif(tg_name == "discriminator"):
#                         s_disc = tg_value
#                         bDisc = True
#         # Attributes
#         attributes = {}
#         for at in el.findall(".//ownedAttribute"):
#             at_id = at.get("{http://schema.omg.org/spec/XMI/2.1}id")
#             t_ref = at.find(".//type")
#             at_assoc = at.get("association")
#             if at_assoc is not None:
#                 children_types.add(at_assoc)
#             # Attribute tags
#             # at_tags = {}
#             # at_tags = get_attrib_tags(at_id)
#             # attributes[at.get("name")] = get_attrib_desc(t_ref.get("{http://schema.omg.org/spec/XMI/2.1}idref"))
#             # if(at_tags is not None) and (len(at_tags > 0)):
#             #     for key in at_tags.keys():
#             #         attributes[at.get("name")][key] = at_tags[key]

#         # Put everything together
#         if not bInherits:
#             elem = {"type": "object", "properties": attributes}
#             if bReq:
#                 elem = {"required": a_req, "type": "object", "properties": attributes}
#             if bDisc:
#                 elem["discriminator"] = {"propertyName": s_disc}
#         else:
#             elem = {"allOf": [parent, {"type": "object", "properties": attributes}]}
#             if (bReq):
#                 elem["required"] = s_req
#             if (bDisc):
#                 elem["discriminator"] = {"propertyName": s_disc}

#         # In the element inherits from a class, then "allOf" tag has to be included
#         if el_id in used_types:
#             dTypes[el.get("name")] = elem

#     # Enumerations
#     for el in tree.findall(".//packagedElement[@{http://schema.omg.org/spec/XMI/2.1}type='uml:Enumeration']"):
#         attrs = []
#         for at in el.findall(".//ownedLiteral"):
#             attrs.append(at.get("name"))
#         dTypes[el.get("name")] = {"type": "string", "enum": attrs}
#     dTypes["Error"] = tm.error
#     return dTypes


def get_attrib_desc(type_ref: str) -> dict:
    """
    Takes as input one of the EA types and returns an Open API friendly representation
    Types can be either basic types, objects or arrays of either basic types or objects
    """
    global tree
    global basic_types
    global basic_type_formats
    r = {}
    name = ''


    is_bt, t = is_basic_type(type_ref)
    if is_bt:
        r = basic_type_formats.get(t).copy()
    elif type_ref.find("[]") > 0:
        is_bt2, t2 = is_basic_type(type_ref[0:-2])
        if is_bt2:
            r = {"type": "array", "items": basic_type_formats.get(t2).copy()}
    elif(type_ref.find("EAID") > -1):
        for el in tree.findall(".//element"):
            if(el.get("{http://schema.omg.org/spec/XMI/2.1}idref") == type_ref):
                name = el.get("name")
                break
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


def is_basic_type(type_ref: str) -> tuple[bool, str]:
    r = [False, ""]
    if type_ref is not None and type_ref.find("[]")==-1:
        for t in basic_types:
            if(type_ref.find(t) > -1):
                r = [True, t]
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

def get_security_scheme(security: str) -> dict:
    sec_scheme = {}
    match security:
        case "basic":
            sec_scheme = {'basicAuth':  {'type': 'http', 'scheme': 'basic'}}
        case "api key":
            sec_scheme = {'ApiKeyAuth': {'type': 'apiKey', 'in': 'header', 'name': 'X-API-KEY'}}
        case "bearer token":
            sec_scheme = {'BearerToken': {'type': 'http', 'scheme': 'bearer', 'bearerFormat': 'JWT'}}
        case "oauth - implicit flow":
            sec_scheme = {'OAuth': {'type': 'oauth2', 'flows': {'implicit': {'authorizationUrl': 'https://example.com/api/oauth/dialog',
                                                                             'scopes': {'write:pets': 'modify pets in your account', 'read:pets': 'read your pets'}}}}}
        case "oauth - authorization code flow":
            sec_scheme = {'OAuth': {'type': 'oauth2', 'flows': {'implicit': {'authorizationUrl': 'https://example.com/api/oauth/dialog',
                                                                             'scopes': {'write:pets': 'modify pets in your account', 'read:pets': 'read your pets'}}}}}
    return sec_scheme


def get_security(security: str) -> list:
    sec = []
    match security:
        case "basic":
            sec = [{'basicAuth': []}]
        case "api key":
            sec = [{'ApiKeyAuth': []}]
        case "bearer token":
            sec = [{'BearerToken': []}]
        case "oauth - implicit flow":
            sec = [{'OAuth': []}]
        case "oauth - authorization code flow":
            sec = [{'OAuth': []}]
    return sec
