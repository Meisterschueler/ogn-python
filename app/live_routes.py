from flask import request, render_template, make_response, send_file
from flask_cors import cross_origin

from app.backend.liveglidernet import rec, lxml

from app import app
from app import db
from app import cache


@app.route("/live.html")
@cross_origin()
def live():
    return render_template("ogn_live.html", host=request.host)


@app.route("/rec.php")
def rec_php():
    a = request.args.get("a")
    z = request.args.get("z")

    xml = rec()
    resp = app.make_response(xml)
    resp.mimetype = "text/xml"
    return resp


@app.route("/lxml.php")
def lxml_php():
    a = request.args.get("a")
    b = request.args.get("b")
    c = request.args.get("c")
    d = request.args.get("d")
    e = request.args.get("e")
    z = request.args.get("z")

    xml = lxml()
    resp = app.make_response(xml)
    resp.mimetype = "text/xml"
    return resp


@app.route("/pict/<filename>")
def pict(filename):
    return app.send_static_file("ognlive/pict/" + filename)


@app.route("/favicon.gif")
def favicon_gif():
    return app.send_static_file("ognlive/pict/favicon.gif")


@app.route("/horizZoomControl.js")
def horizZoomControl_js():
    return app.send_static_file("ognlive/horizZoomControl.js")


@app.route("/barogram.js")
def barogram_js():
    return app.send_static_file("ognlive/barogram.js")


@app.route("/util.js")
def util_js():
    return app.send_static_file("ognlive/util.js")


@app.route("/ogn.js")
def ogn_js():
    return app.send_static_file("ognlive/ogn.js")


@app.route("/ol.js")
def ol_js():
    return app.send_static_file("ognlive/ol.js")


@app.route("/osm.js")
def osm_js():
    return app.send_static_file("ognlive/osm.js")


@app.route("/ol.css")
def ol_css():
    return app.send_static_file("ognlive/ol.css")


@app.route("/osm.css")
def osm_css():
    return app.send_static_file("ognlive/osm.css")
