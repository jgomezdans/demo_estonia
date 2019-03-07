#!/usr/bin/env python
import json
import warnings
from concurrent.futures import ThreadPoolExecutor, as_completed

import datetime as dt

import urllib.request

import numpy as np

from tqdm.autonotebook import tqdm


import gdal

gdal.UseExceptions()




def retrieve_field(k, url0, roi, urlcloud=None, cld_thresh=20):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        if roi.find("http://") >= 0:
            prefix = "/vsicurl/"
        else:
            prefix = ""
        if urlcloud is not None:
            g = gdal.Open(f"/vsicurl/{url0:s}")
            height = g.RasterYSize
            width=g.RasterXSize
            g = gdal.Warp("", f"/vsicurl/{urlcloud:s}", format="MEM",
                          height=height, width=width,
                          cutlineDSName=f"{prefix:s}{roi}",
                          cropToCutline=True)
            cld = g.ReadAsArray()
            if np.sum(cld < cld_threshold) == 0:
                # No clear pixels
                return k, None

        g = gdal.Warp("", f"/vsicurl/{url0:s}", format="MEM",
                        cutlineDSName=f"{prefix:s}{roi}",
                        cropToCutline=True)
        data1 = g.ReadAsArray()*1.
        data1[data1 < -9990] = np.nan
        data1[cld > cld_thresh] = np.nan
        if np.isnan(np.nanmean(data1)):
            return k, None
        return k, data1


def calculate_index(k, url0, url1, urlcloud, roi, cld_thresh):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        if roi.find("http://") >= 0:
            prefix = "/vsicurl/"
        else:
            prefix = ""
        g = gdal.Open(f"/vsicurl/{url0:s}")
        height = g.RasterYSize
        width=g.RasterXSize
        g = gdal.Warp("", f"/vsicurl/{urlcloud:s}", format="MEM",
                      height=height, width=width,
                      cutlineDSName=f"{prefix:s}{roi}",
                      cropToCutline=True)
        cld = g.ReadAsArray()
        if np.sum(cld > cld_threshold) == 0:
            # No clear pixels
            return k, None

        g = gdal.Warp("", f"/vsicurl/{url0:s}", format="MEM",
                        cutlineDSName=f"{prefix:s}{roi}",
                        cropToCutline=True)
        data1 = g.ReadAsArray()*1.
        g = gdal.Warp("", f"/vsicurl/{url1:s}", format="MEM",
                        cutlineDSName=f"{prefix:s}{roi}",
                        cropToCutline=True)
        data1[data1 < -9990] = np.nan
        data2[data2 < -9990] = np.nan
        data1[cld > cld_thresh] = np.nan
        data2[cld > cld_thresh] = np.nan
        data1 = data1/10000.
        data2 = data2/10000.
        if np.isnan(np.nanmean(data1)):
            return k, None
        ndvi = (data2-data1)/(data2+data1)
        return k,ndvi


def extract_roi_data_ndre(img_db, roi=None, b0=3, b1=6, cld_thresh=20):
    analysis_data = {}
    with ThreadPoolExecutor(max_workers=10) as ex:
        futures = []
        for k in img_db.keys():
            futures.append(ex.submit(calculate_index, k, img_db[k][b0],
                            img_db[k][b1], img_db[k][-1],
                            roi, cld_thresh))
        kwargs = {
            'total': len(futures),
            'unit': 'it',
            'unit_scale': True,
            'leave': True
        }
        #Print out the progress as tasks complete
        for f in tqdm(as_completed(futures), **kwargs):
            f0, f1  = f.result()
            analysis_data[f0] = f1
    clean_data = {k:v for k,v in analysis_data.items() if v is not None}
    return clean_data




def grab_holdings(url="http://www2.geog.ucl.ac.uk/" +
                  "~ucfajlg/Ghana/composites/database.json"):

    tmp_db  = json.loads(urllib.request.urlopen(url).read())
    dates = [(k, dt.datetime.strptime(k, "%Y-%m-%d").date())
             for k in tmp_db.keys()]

    the_db = {kk:tmp_db[k] for (k,kk) in dates}
    return the_db
