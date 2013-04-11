try:
    import simplejson as json
except ImportError:
    import json

import sys
import traceback

import cherrypy

from cherrypy import HTTPError
from cherrypy.lib import httputil as cphttputil

from .tsp import *

class UserController(object):

    _cp_config = {"tools.json_in.on": True}

    @cherrypy.tools.json_out()
    def create(self, **kwargs):
        return {}

    @cherrypy.tools.json_out()
    def show(self, id, **kwargs):
        cities_amount = 30
        if kwargs.get('coordsX') and kwargs.get('coordsY'):
            cities_amount = len(kwargs['coordsX'])
            coords = [(int(kwargs['coordsX'][i]), int(kwargs['coordsY'][i])) for i in range(cities_amount)]
        else:
            max_coords = {'x': 800, 'y': 600}
            if kwargs.get('cities_amount'):
                cities_amount = int(kwargs['cities_amount'])
            if kwargs.get('x') and kwargs.get('y'):
                max_coords = {'x': int(kwargs['x']), 'y': int(kwargs['y'])}
            coords = cities_random(cities_amount, max_coords['x'], max_coords['y'])
        cm = cartesian_matrix(coords)
        ev = Environment(cm = cm, size = cities_amount, maxgenerations = 100000,\
                         newindividualrate=0.9,crossover_rate=0.99,\
                         mutation_rate=0.9)
        min_individual = ev.run()
        return {'kwargs': kwargs, 'coords': [{'x': dot[0], 'y': dot[1]} for dot in coords], 'optimal_path': min_individual.toPlainObject()}

    @cherrypy.tools.json_out()
    def update(self, id, **kwargs):
        return {}

    def delete(self, id, **kwargs):
        return {}


rest_controller = cherrypy.dispatch.RoutesDispatcher()
rest_controller.mapper.explicit = False
rest_controller.connect("new_user", "/", UserController, action="create",
                        conditions={"method":["POST"]})
rest_controller.connect("show_user", "/{id}", UserController, action="show",
                        conditions={"method":["GET"]})
rest_controller.connect("update_user", "/{id}", UserController, action="update",
                        conditions={"method":["PUT"]})
rest_controller.connect("delete_user", "/{id}", UserController, action="delete",
                        conditions={"method":["DELETE"]})

# Error handlers

def generic_error_handler(status, message, traceback, version):
    """error_page.default"""
    
    response = cherrypy.response
    response.headers['Content-Type'] = "application/json"
    response.headers.pop('Content-Length', None)

    code, reason, _ = cphttputil.valid_status(status)
    result = {"code": code, "reason": reason, "message": message}
    if hasattr(cherrypy.request, "params"):
        params = cherrypy.request.params
        if "debug" in params and params["debug"]:
            result["traceback"] = traceback
    return json.dumps(result)

def unexpected_error_handler():
    """request.error_response"""

    (typ, value, tb) = sys.exc_info()
    if typ:
        debug = False
        if hasattr(cherrypy.request, "params"):
            params = cherrypy.request.params
            debug = "debug" in params and params["debug"]

        response = cherrypy.response
        response.headers['Content-Type'] = "application/json"
        response.headers.pop('Content-Length', None)
        content = {}

        if isinstance(typ, HTTPError):
            cherrypy._cperror.clean_headers(value.code)
            response.status = value.status
            content = {"code": value.code, "reason": value.reason, "message": value._message}
        elif isinstance(typ, (TypeError, ValueError, KeyError)):
            cherrypy._cperror.clean_headers(400)
            response.status = 400
            reason, default_message = cphttputil.response_codes[400]
            content = {"code": 400, "reason": reason, "message": value.message or default_message}

        if cherrypy.serving.request.show_tracebacks or debug:
            tb = traceback.format_exc()
            content["traceback"] = tb
        response.body = json.dumps(content)
