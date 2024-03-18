from utilities import logger, get_local_ip
from webserver import webserver
from waitress import serve
import argparse, os


if __name__ == '__main__':
    parser = argparse.ArgumentParser('polestar-logbook')
    parser.add_argument("-d", dest='debug', help="allowed options: true/false", type=str, default="false")
    args = parser.parse_args()
    app = webserver()
    ip = get_local_ip()
    port = int(os.getenv('WEBSERVER_PORT'))
    if args.debug == "true":
        app.run(debug=True, host=ip, port=port)
    elif args.debug == "false":
        serve(app, port=port, host=ip)
    else:
        raise RuntimeError("Required Args missing, use -h for more information.")