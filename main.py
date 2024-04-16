from utilities import logger, get_local_ip
from flask import render_template
from webserver import webserver
from waitress import serve
import argparse, os, logging


if __name__ == '__main__':
    parser = argparse.ArgumentParser('polestar-logbook')
    parser.add_argument("-d", dest='debug', help="allowed options: true/false", type=str, default="false")
    args = parser.parse_args()
    app = webserver()
    
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html')
    
    ip = get_local_ip()
    port = int(os.getenv('WEBSERVER_PORT'))
    if args.debug == "true":
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s [%(levelname)s]: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        app.run(debug=True, host=ip, port=port)
    elif args.debug == "false":
        serve(app, port=port, host=ip)
    else:
        raise RuntimeError("Required Args missing, use -h for more information.")