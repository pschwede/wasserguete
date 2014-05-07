#!/usr/bin/env python

# -*- coding: utf-8 -*-

import gc
import csv
import sys
import glob
import numpy as np
import pprint
import pyodbc
import pickle
import colorsys
import datetime
import etframes
import itertools
from os.path import realpath, join
from matplotlib import pyplot
from collections import defaultdict

DELIM = "\t"

def color_palette(n, nmax=255):
    """
    # tango
    return ["#edd400",
            "#f57900",
            "#c17d11",
            "#73d216",
            "#3465a4",
            "#75507b",
            "#cc0000",
            "#d3d7cf"]
    # solarized
    yellow = (181./255, 137./255, 0./255)
    orange = (203./255, 75./255, 22./255)
    red    = (220./255, 50./255, 47./255)
    magenta = (211./255, 54./255, 130./255)
    violet = (108./255,113./255,196./255)
    blue   = ( 38./255,139./255,210./255)
    cyan   = ( 42./255,161./255,152./255)
    green  = (133./255,153./255,  0./255)
    return [red, orange, yellow, violet, cyan, blue, green][n % 7]
    """
    # rainbow
    return colorsys.hsv_to_rgb(0.66 * n / nmax, .8, .8)


def get_substrate_key(cvs_dir, substrate):
    with open(join(cvs_dir, "ZENTRAL_ZTPARAM.csv"), "r") as z:
        reader = csv.reader(z, delimiter=DELIM)
        for row in reader:
            if substrate in row:
                return row[0]


def get_rows(cvs_dir, key):
    rows = []
    for csv_file in glob.glob("%s/*.csv" % cvs_dir):
        if "ZENTRAL_ZTPARAM.csv" in csv_file:
            continue
        with open(csv_file, "r") as f:
            dictreader = csv.DictReader(f, delimiter=DELIM)
            for k in dictreader:
                if "PRAEFIX" not in k:
                    break
                if key in k.values():
                    rows.append(k)
    return rows


def extract_info(substances):
    rows = defaultdict(dict)
    for subs in substances:
        rows[subs] = {}
        for cvs_dir in glob.glob("data/csv/*"):
            try:
                subs_key = get_substrate_key(cvs_dir, subs)
                if not subs_key:
                    continue
                subs_rows = get_rows(cvs_dir, subs_key)
                positives = 0
                for row in subs_rows:
                    if row["PRAEFIX"] == "nn":
                        #continue
                        value = 0.0
                    else:
                        value = float(row["ERGEBNIS"])
                    try:
                        time = datetime.datetime.strptime("%s %s" % (row["PDATUM"].split(" ")[0], row["PZEIT"].split(" ")[1]), "%x %X")
                    except IndexError, e:
                        time = datetime.datetime.strptime(row["PDATUM"], "%x %X")

                    try:
                        pos = row["MKZ_"]
                    except KeyError:
                        pos = row["MKZ"]

                    dic = {"datetime": time, "value": value}
                    try:
                        rows[subs][pos].append(dic)
                    except KeyError:
                        rows[subs][pos] = [dic]
                    positives += 1 if row["PRAEFIX"] == "nn" else 0
            except IOError, e:
                print "Error: %s" % (e, cvs_dir)
    return rows


def timelines(info, years):
    for j, substance in enumerate(info):
        tuples = [row for row in itertools.chain(*info[substance].values())]
        tuples = sorted(tuples, key=lambda x: x["datetime"])

        x = np.array([i["datetime"] for i in tuples])
        y = np.array([i["value"] for i in tuples])

        fig, ax = pyplot.subplots()

        ax.scatter(x, y, color="none", linewidth=1, edgecolor="black")
        # ax.scatter(x, y, color="none", linewidth=1, edgecolor=color_palette(j, len(info)))
        etframes.add_dot_dash_plot(ax, ys=y)

        pyplot.title(u"%s im Oberfl\u00E4chenwasser (\u00B5g/l)" % substance)
        fig.autofmt_xdate()
        fig.set_size_inches(16, 9)
        fig.savefig("%s.png" % substance, format="png", dpi=100, bbox_inches="tight")
        gc.collect()


def get_years(info):
    years = set([])
    for substance in enumerate(info):
        years |= set([x["datetime"].year for x in tuples[substance]])
    years = sorted(list(years))
    return years


def positives_per_year(info, years=None):
    fig, ax = pyplot.subplots()
    
    tuples = {}
    for i, substance in enumerate(info):
        tuples[substance] = [row for row in itertools.chain(*info[substance].values())]
        tuples[substance] = sorted(tuples[substance], key=lambda x: x["datetime"])

    if not years:
        years = get_years(info)

    bar_width = 0.9 / len(years)
    xpos = np.arange(len(years))

    for i, substance in enumerate(info):
        values = []
        pct = []
        for j, year in enumerate(years):
            # a bar for each substance
            positives = 0
            yearly = 0
            all_ = 0
            for t in tuples[substance]:
                if t["datetime"].year == year:
                    all_ += 1
                    yearly += t["value"]
                    if t["value"] > 0:
                        positives += 1

            pct.append(float(positives) * 100 / all_ if all_ else 0)
            values.append(float(yearly) / all_ if all_ else 0)
        ax.bar(xpos + (bar_width * i), pct, width=bar_width, color=color_palette(i, len(years)), linewidth=0.01, label=substance)
        #ax.bar(xpos + (bar_width * i), values, width=bar_width, color=color_palette(i, len(years)), linewidth=0.01, label=substance)

    leg = ax.legend(loc="best", fancybox=True)
    leg.get_frame().set_alpha(0.5)

    ax.set_ylabel("Anteil in %")
    ax.set_xlabel("Jahr")

    pyplot.xticks(xpos + bar_width * len(years) / 2, years)
    pyplot.title(u"Positivbefunde Oberfl\u00E4chenwasser pro Jahr in Sachsen")
    fig.set_size_inches(16, 9)
    fig.savefig("positives_per_year.png", format="png", dpi=100, bbox_inches="tight")


def punchcard(info, years=None):
    if not years:
        years = get_years(info)

    for year in years:
        fig, ax = pyplot.subplots()
        ax.set_ylim(24, 0)
        ax.set_yticks(range(0,24))
        ax.set_xlim(0, 365)

        for i, substance in enumerate(info):
            pos = lambda x: x > 0
            neg = lambda x: x <= 0
            for side in [pos, neg]:
                datapoints = [r for r in itertools.chain(*info[substance].values()) if r["datetime"].year == year and side(r["value"])]
                day_of_year = [r["datetime"].timetuple().tm_yday for r in datapoints]
                hour_of_day = [r["datetime"].hour + float(i) / len(info) for r in datapoints]

                col = color_palette(i, len(info))
                if side is pos:
                    ax.scatter(x=day_of_year, y=hour_of_day, s=10, color=col, edgecolor=col, linewidth=0.5, label=substance)
                else:
                    ax.scatter(x=day_of_year, y=hour_of_day, s=10, color="w", edgecolor=col, alpha=0.5, linewidth=0.25)

        pyplot.title(u"Oberfl\u00E4chenwasser Messungen in Sachsen %s" % year)

        leg = ax.legend(loc="best", fancybox=True)
        leg.get_frame().set_alpha(0.5)

        ax.set_ylabel("Stunde")
        ax.set_xlabel("Tag im Jahr")

        fig.set_size_inches(16,9)
        fig.savefig("punchcard_%s.png" % year, format="png", dpi=100, bbox_inches="tight")
        gc.collect()


if __name__ == "__main__":
    substances = ["Imidacloprid", "Clothianidin", "Propoxur", "Glyphosate", "Propioconazol", "Tebuconazol", "Thiamethoxam"]
    try:
        with open("data/info.pkl", "r") as f:
            info = pickle.load(f)
    except:
        info = extract_info(substances)
        gc.collect()
        with open("data/info.pkl", "w") as f:
            pickle.dump(info, f)
    years = [2007, 2008, 2009, 2010, 2011, 2012, 2013]
    timelines(info, years)
    positives_per_year(info, years)
    punchcard(info, years)
