#!/usr/bin/env python
import PySimpleGUI as sg
import sys
import api_spec
import configparser

"""
    Generates Open API Specification from an XMI design model
"""


def runGUI():
    path_guid = ''
    type_guid = ''
    f_in = ''
    f_out = ''

    if not sys.platform.startswith('win'):
        sg.popup_error('Sorry, you gotta be on Windows')
        sys.exit(0)
    sg.change_look_and_feel('Dark Blue 3')      # because gray windows are boring

    config = configparser.RawConfigParser()
    with open('config.ini', 'r+') as configfile:
        config.read_file(configfile)

    layout = [
        [sg.Text('Open API Specificatin Generator', auto_size_text=True)],
        [sg.Text('Path GUID', size=(12, 1)),
         sg.Input(key="i-1", size=(80, 1), default_text=config['default']['path_guid'])],
        [sg.Text('Types GUID', size=(12, 1)),
         sg.Input(key='i-2', size=(80, 1), default_text=config['default']['type_guid'])],
        [sg.Text('XMI model file', size=(12, 1)),
         sg.Input(key="i-3", size=(80, 1), default_text=config['default']['f_in']),
         sg.FileBrowse()],
        [sg.Text('Output file', size=(12, 1)),
         sg.Input(key='i-4', size=(80, 1), default_text=config['default']['f_out']),
         sg.FileBrowse()],
        [sg.Text('Title', size=(12, 1)),
         sg.Input(key="i-5", size=(80, 1), default_text=config['default']['title'])],
        [sg.Text('Security Scheme', size=(12, 1)),
         sg.Combo(["basic", "api key", "bearer token", "oauth - implicit flow", "oauth - authorization code flow"], key="i-6", size=(40, 1), default_value=config['default']['security'])],
         [sg.Text('')],
        [sg.Button('Generate', key="Generate"),
         sg.Button('Exit', key="Exit")]]

    window = sg.Window('Open API Specification Generator',
                       layout, auto_size_text=False, default_element_size=(22, 1),
                       text_justification='right')

    while True:     # Event Loop
        event, values = window.read()
        if(event == "Generate"):
            path_guid = values["i-1"]
            type_guid = values["i-2"]
            f_in = values["i-3"]
            f_out = values["i-4"]
            title = values["i-5"]
            security = values["i-6"]
            api_spec.generate_spec(f_in, f_out, path_guid, type_guid, title, security)
            sg.popup_auto_close('Specification has been generated', title="Completed", auto_close_duration=10)
        elif(event == "Exit"):
            config['default'] = {}
            config['default']["path_guid"] = values["i-1"]
            config['default']['type_guid'] = values["i-2"]
            config['default']['f_in'] = values["i-3"]
            config['default']['f_out'] =  values["i-4"]
            config['default']['title'] =  values["i-5"]
            config['default']['security'] =  values["i-6"]
            with open('config.ini', 'w') as configfile:
                config.write(configfile)
            sys.exit(0)
        elif event is None:
            break

    window.close()


if __name__ == '__main__':
    runGUI()
