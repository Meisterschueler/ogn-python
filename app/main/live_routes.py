from flask import request, render_template, current_app
from flask_cors import cross_origin

from app.backend.liveglidernet import rec, lxml
from app.main import bp


@bp.route("/live.html")
@cross_origin()
def live():
    return render_template("ogn_live.html", host=request.host)


@bp.route("/rec.php")
def rec_php():
    a = request.args.get("a")
    z = request.args.get("z")

    xml = rec()
    resp = current_app.make_response(xml)
    resp.mimetype = "text/xml"
    return resp


@bp.route("/lxml.php")
def lxml_php():
    a = request.args.get("a")
    b = request.args.get("b")
    c = request.args.get("c")
    d = request.args.get("d")
    e = request.args.get("e")
    z = request.args.get("z")

    xml = lxml()
    resp = current_app.make_response(xml)
    resp.mimetype = "text/xml"
    return resp


@bp.route("/pict/<filename>")
def pict(filename):
    return current_app.send_static_file("ognlive/pict/" + filename)


@bp.route("/favicon.gif")
def favicon_gif():
    return current_app.send_static_file("ognlive/pict/favicon.gif")


@bp.route("/horizZoomControl.js")
def horizZoomControl_js():
    return current_app.send_static_file("ognlive/horizZoomControl.js")


@bp.route("/barogram.js")
def barogram_js():
    return current_app.send_static_file("ognlive/barogram.js")


@bp.route("/util.js")
def util_js():
    return current_app.send_static_file("ognlive/util.js")


@bp.route("/ogn.js")
def ogn_js():
    return current_app.send_static_file("ognlive/ogn.js")


@bp.route("/ol.js")
def ol_js():
    return current_app.send_static_file("ognlive/ol.js")


@bp.route("/osm.js")
def osm_js():
    return current_app.send_static_file("ognlive/osm.js")


@bp.route("/ol.css")
def ol_css():
    return current_app.send_static_file("ognlive/ol.css")


@bp.route("/osm.css")
def osm_css():
    return current_app.send_static_file("ognlive/osm.css")
