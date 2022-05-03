#!/usr/bin/python

from dataclasses import dataclass, field

#  Problem Details for HTTP APIs https://tools.ietf.org/html/rfc7807
error = {
    'type': 'object',
    'properties':
    {
        'id':{ 'type': 'string'},
        'type': {'type': 'string'},
        'title':{'type': 'string'},
        'detail':{'type': 'string'},
        'instance': { 'type': 'string'},
        'invalidParameters':
         { 
            'type': 'array',
            'items':
            { 
                'type': 'object',
                'properties': 
                {
                    'parameters': 
                    {
                        'type': 'array', 
                        'items': 
                        {
                            'type': 'string'
                        }
                    }, 
                    'reason': 
                    {
                        'type': 'string'
                    }
                }
            }
        }
    }
}



@dataclass
class API_Type:
    type: str
    required: dict
    discriminator: dict
    properties: dict
