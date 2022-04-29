#!/usr/bin/python
import yaml
import xml.etree.ElementTree as ET
import models.path_models as pm
import models.type_models as tm
import type_gen as tg
import path_gen as pg
from dataclasses import asdict


def generate_spec(f_in: str, f_out: str, path_guid: str, type_guid: str, title: str, security: str):
    spec = create_api_spec(f_in, path_guid, type_guid, title, security)
    with open(f_out, 'w+') as f:
        yaml.dump(asdict(spec), f, allow_unicode=True, sort_keys=False)


def create_api_spec(f_name: str, path_guid: str, type_guid: str, title: str, security: str):
    global tree
    tree = load_model(f_name)
    tg.tree = tree
    pg.tree = tree
    pathsDic = pg.get_paths(path_guid)
    typesDic = tg.get_types(type_guid)
    spec = pm.ApiSpec()
    spec.info["title"] = title
    spec.paths["paths"] = pathsDic
    spec.components["schemas"] = typesDic
    spec.components["securitySchemes"]= tg.get_security_scheme(security)
    spec.security = tg.get_security(security)
    spec.paths = pathsDic
    return spec


def load_model(f_name):
    return ET.parse(f_name)
