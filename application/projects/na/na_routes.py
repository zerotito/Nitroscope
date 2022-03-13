from flask import Blueprint, render_template
from flask import render_template, request

from application.projects.na.projects.metric_analysis.be.function import metric_analysis
from application.projects.na.projects.metric_analysis.be.function import metric_apiv1
from application.projects.na.projects.metric_analysis.be.function import metric_apiv2
from application.projects.na.projects.metric_analysis.be.function import metric_apiv3
from application.projects.na.projects.metric_analysis.be.function import metric_apiv4

from application.projects.na.projects.counter.be.function import counter_analysis
from application.projects.na.projects.counter.be.function import counter_apiv1
from application.projects.na.projects.counter.be.function import counter_apiv2
from application.projects.na.projects.counter.be.function import counter_apiv3
from application.projects.na.projects.counter.be.function import counter_apiv4

# Set up a Blueprint
na_bp = Blueprint('na_bp', __name__,
                  template_folder='projects',
                  static_folder='static')


@na_bp.after_request
def apply_caching(response):
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response


@na_bp.route('na_navbar', methods=["GET", "POST"])
def navbar_rt():
    return render_template("navbar/navbar.html")

@na_bp.route("/", methods=['GET', 'POST', 'DELETE'])
@na_bp.route("/metrics", methods=['GET', 'POST', 'DELETE'])
def metric_analysis_rt():
    return metric_analysis()

@na_bp.route("/metrics/apiv1", methods=['GET', 'POST', 'DELETE'])
def apiv1_rt():
    return metric_apiv1()

@na_bp.route("/metrics/apiv2", methods=['GET', 'POST', 'DELETE'])
def apiv2_rt():
    return metric_apiv2()

@na_bp.route("/metrics/apiv3", methods=['GET', 'POST', 'DELETE'])
def apiv3_rt():
    return metric_apiv3()

@na_bp.route("/metrics/apiv4", methods=['GET', 'POST', 'DELETE'])
def apiv4_rt():
    return metric_apiv4()

@na_bp.route("/counters", methods=['GET', 'POST', 'DELETE'])
def counter_analysis_rt():
    return counter_analysis()

@na_bp.route("/counters/apiv1", methods=['GET', 'POST', 'DELETE'])
def counter_apiv1_rt():
    return counter_apiv1()

@na_bp.route("/counters/apiv2", methods=['GET', 'POST', 'DELETE'])
def counter_apiv2_rt():
    return counter_apiv2()

@na_bp.route("/counters/apiv3", methods=['GET', 'POST', 'DELETE'])
def counter_apiv3_rt():
    return counter_apiv3()

@na_bp.route("/counters/apiv4", methods=['GET', 'POST', 'DELETE'])
def counter_apiv4_rt():
    return counter_apiv4()

# End of file
