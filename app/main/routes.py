from datetime import date, time, datetime

from flask import request, render_template, send_file

from app import db
from app import cache
from app.model import Airport, Country, Sender, SenderInfo, TakeoffLanding, Logbook, Receiver, SenderPosition, RelationStatistic, ReceiverStatistic, SenderStatistic

from app.main import bp
from app.main.matplotlib_service import create_range_figure


@cache.cached(key_prefix="countries_in_receivers")
def get_countries_in_receivers():
    query = db.session.query(Country.iso2).filter(Country.gid == Receiver.country_id).order_by(Country.iso2).distinct(Country.iso2)

    return [{"iso2": country[0]} for country in query.all()]


@cache.cached(key_prefix="countries_in_takeoff_landings")
def get_used_countries():
    query = db.session.query(Country.iso2).filter(Country.gid == TakeoffLanding.country_id).order_by(Country.iso2).distinct(Country.iso2)
    return [{"iso2": country[0]} for country in query.all()]


@cache.memoize()
def get_used_airports_by_country(sel_country):
    query = db.session.query(Airport).filter(Airport.country_code == sel_country).filter(TakeoffLanding.airport_id == Airport.id).filter(TakeoffLanding.country_id == Country.gid).order_by(Airport.name).distinct(Airport.name)
    return [used_airport for used_airport in query]


@cache.memoize()
def get_dates_for_airport(sel_airport):
    query = (
        db.session.query(db.func.date(Logbook.reference_timestamp), db.func.count(Logbook.id).label("logbook_count"))
        .filter(Airport.id == sel_airport)
        .filter(db.or_(Airport.id == Logbook.takeoff_airport_id, Airport.id == Logbook.landing_airport_id))
        .group_by(db.func.date(Logbook.reference_timestamp))
        .order_by(db.func.date(Logbook.reference_timestamp).desc())
    )

    return [{"date": date, "logbook_count": logbook_count} for (date, logbook_count) in query.all()]


@bp.route("/")
@bp.route("/index.html")
def index():
    today_beginning = datetime.combine(date.today(), time())

    senders_today = db.session.query(db.func.count(Sender.id)).filter(Sender.lastseen >= today_beginning).one()[0]
    receivers_today = db.session.query(db.func.count(Receiver.id)).filter(Receiver.lastseen >= today_beginning).one()[0]
    takeoffs_today = db.session.query(db.func.count(TakeoffLanding.id)).filter(db.and_(TakeoffLanding.timestamp >= today_beginning, TakeoffLanding.is_takeoff is True)).one()[0]
    landings_today = db.session.query(db.func.count(TakeoffLanding.id)).filter(db.and_(TakeoffLanding.timestamp >= today_beginning, TakeoffLanding.is_takeoff is False)).one()[0]
    sender_positions_today = db.session.query(db.func.sum(ReceiverStatistic.messages_count)).filter(ReceiverStatistic.date == date.today()).one()[0]
    sender_positions_total = db.session.query(db.func.sum(ReceiverStatistic.messages_count)).one()[0]

    last_logbook_entries = db.session.query(Logbook).order_by(Logbook.reference_timestamp.desc()).limit(10)
    return render_template(
        "index.html",
        senders_today=senders_today,
        receivers_today=receivers_today,
        takeoffs_today=takeoffs_today,
        landings_today=landings_today,
        sender_positions_today=sender_positions_today,
        sender_positions_total=sender_positions_total,
        logbook=last_logbook_entries)


@bp.route("/senders.html", methods=["GET", "POST"])
def senders():
    senders = db.session.query(Sender) \
        .options(db.joinedload(Sender.infos)) \
        .order_by(Sender.name)
    return render_template("senders.html", senders=senders)


@bp.route("/sender_detail.html", methods=["GET", "POST"])
def sender_detail():
    sender_id = request.args.get("sender_id")
    sender = db.session.query(Sender).filter(Sender.id == sender_id).one()

    return render_template("sender_detail.html", title="Sender", sender=sender)


@bp.route("/range_view.png")
def range_view():
    import io
    from flask import Response

    from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas

    sender_id = request.args.get("sender_id")

    fig = create_range_figure(sender_id)
    output = io.BytesIO()
    FigureCanvas(fig).print_png(output)
    return Response(output.getvalue(), mimetype='image/png')


@bp.route("/receivers.html")
def receivers():
    sel_country = request.args.get("country")

    countries = get_countries_in_receivers()

    # Get receiver selection list
    if sel_country:
        receivers = db.session.query(Receiver) \
            .options(db.joinedload(Receiver.airport)) \
            .filter(db.and_(Receiver.country_id == Country.gid, Country.iso2 == sel_country)) \
            .order_by(Receiver.name)
    else:
        receivers = db.session.query(Receiver) \
            .options(db.joinedload(Receiver.airport)) \
            .order_by(Receiver.name)

    return render_template("receivers.html", title="Receivers", sel_country=sel_country, countries=countries, receivers=receivers)


@bp.route("/receiver_detail.html")
def receiver_detail():
    receiver_id = request.args.get("receiver_id")

    receiver = db.session.query(Receiver).filter(Receiver.id == receiver_id).one()
    return render_template("receiver_detail.html", title="Receiver Detail", receiver=receiver)


@bp.route("/airports.html", methods=["GET", "POST"])
def airports():
    sel_country = request.args.get("country")

    countries = get_used_countries()

    if sel_country:
        airports = get_used_airports_by_country(sel_country)
    else:
        airports = []

    page = request.args.get("page", 1, type=int)

    return render_template("airports.html", sel_country=sel_country, countries=countries, airports=airports)


@bp.route("/airport_detail.html")
def airport_detail():
    sel_airport = request.args.get("airport_id")

    airport = db.session.query(Airport).filter(Airport.id == sel_airport)

    senders = db.session.query(Sender).join(Logbook).filter(Logbook.takeoff_airport_id == sel_airport).order_by(Sender.name)

    return render_template("airport_detail.html", title="Airport Detail", airport=airport.one(), senders=senders)


@bp.route("/logbooks.html", methods=["GET", "POST"])
def logbooks():
    sel_country = request.args.get("country")
    sel_airport_id = request.args.get("airport_id")
    sel_date = request.args.get("date")

    sel_sender_id = request.args.get("sender_id")

    countries = get_used_countries()

    if sel_country:
        airports = get_used_airports_by_country(sel_country)
    else:
        airports = []

    if sel_airport_id:
        sel_airport_id = int(sel_airport_id)
        if sel_airport_id not in [airport.id for airport in airports]:
            sel_airport_id = None
            sel_date = None
        dates = get_dates_for_airport(sel_airport_id)
    else:
        dates = []

    if sel_date:
        sel_date = datetime.strptime(sel_date, "%Y-%m-%d").date()
        if sel_date not in [entry["date"] for entry in dates]:
            sel_date = dates[0]["date"]
    elif len(dates) > 0:
        sel_date = dates[0]["date"]

    # Get Logbook
    filters = []
    if sel_airport_id:
        filters.append(db.or_(Logbook.takeoff_airport_id == sel_airport_id, Logbook.landing_airport_id == sel_airport_id))

    if sel_date:
        filters.append(db.func.date(Logbook.reference_timestamp) == sel_date)

    if sel_sender_id:
        filters.append(Logbook.sender_id == sel_sender_id)

    if len(filters) > 0:
        logbooks = db.session.query(Logbook).filter(*filters).order_by(Logbook.reference_timestamp).limit(100)
    else:
        logbooks = None

    return render_template("logbooks.html", title="Logbook", sel_country=sel_country, countries=countries, sel_airport_id=sel_airport_id, airports=airports, sel_date=sel_date, dates=dates, logbooks=logbooks)


@bp.route("/download.html")
def download_flight():
    from io import StringIO

    buffer = StringIO()
    buffer.write("Moin moin\nAlter Verwalter")
    buffer.seek(0)

    return send_file(buffer, as_attachment=True, attachment_filename="wtf.igc", mimetype="text/plain")


@bp.route("/sender_ranking.html")
def sender_ranking():
    sender_statistics = db.session.query(SenderStatistic) \
        .filter(db.and_(SenderStatistic.date == date.today(), SenderStatistic.is_trustworthy is True)) \
        .order_by(SenderStatistic.max_distance.desc()) \
        .all()

    return render_template(
        "sender_ranking.html",
        title="Sender Ranking",
        ranking=sender_statistics)


@bp.route("/receiver_ranking.html")
def receiver_ranking():
    receiver_statistics = db.session.query(ReceiverStatistic) \
        .filter(db.and_(ReceiverStatistic.date == date.today(), ReceiverStatistic.is_trustworthy is True)) \
        .order_by(ReceiverStatistic.max_distance.desc()) \
        .all()

    return render_template(
        "receiver_ranking.html",
        title="Receiver Ranking",
        ranking=receiver_statistics)
