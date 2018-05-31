#! /usr/bin/env python
# -*- coding: utf-8 -*-
import os
import re
import json
import codecs
import scrapy
import shutil
import fiona
import fiona.crs


def convert(f_in, f_out='regional-councilors-constituencies-2016.geojson', filter=None):
    with fiona.open(
            f_in,
            'r',
            driver='ESRI Shapefile',
            crs=fiona.crs.from_epsg(4326),
            encoding='Big5-HKSCS') as source:
        with fiona.open(
                f_out,
                'w',
                driver='GeoJSON',
                crs = fiona.crs.from_epsg(3824),
                schema=source.schema,
                encoding='utf-8') as sink:

            if filter:
                for rec in source:
                    if rec['properties']['COUNTYNAME'] == filter:
                        sink.write(rec)
            else:
                for rec in source:
                    sink.write(rec)

def get_counties(f_in):
    with fiona.open(
            f_in,
            'r',
            driver='ESRI Shapefile',
            crs=fiona.crs.from_epsg(4326),
            encoding='utf-8') as source:
        return list({rec['properties']['DISTRICT_T'] for rec in source})

f_in = 'dc_2015/GIH3_DC_2015_POLY.shp'
f_out = u'geojson/regional-councilors-constituencies-2016.geojson'
convert(f_in, f_out, None)
