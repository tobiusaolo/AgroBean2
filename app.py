from flask import Flask,render_template,url_for,redirect
from sqlalchemy import create_engine
import math
from math import pi
import numpy as np
import pandas as pd
import folium
from bokeh.models import (HoverTool, FactorRange, Plot, LinearAxis, Grid, Range1d)
from bokeh.plotting import figure
from bokeh.resources import CDN
from bokeh.models import ColumnDataSource
from bokeh.models.tools import HoverTool
from bokeh.palettes import Spectral5,Category20c,Spectral11
from bokeh.transform import factor_cmap,cumsum
from bokeh.embed import components,file_html
from bokeh.models.sources import ColumnDataSource


db_connect = engine = create_engine('sqlite://///home/kobe-toby/Documents/new/untitled1/example.db')

app = Flask(__name__)

ui=FlaskUI(app)



def getData():
    sql = "select * from agrobean_results"
    df = pd.read_sql(sql, db_connect)
    return df
#helper function to convert lat/long to easting/northing for mapping
#this relies on functions from the pyproj library
def LongLat_to_EN(long, lat):
    try:
      easting, northing = transform(
        Proj(init='epsg:4326'), Proj(init='epsg:3857'), long, lat)
      return easting, northing
    except:
      return None, None

@app.route('/')
def index():
    df2=getData()
    s = df2.result
    counts = s.value_counts()
    percent = s.value_counts(normalize=True)
    percent100 = s.value_counts(normalize=True).mul(100).round(1).astype(str) + '%'
    df=pd.DataFrame({'counts': counts, 'per': percent, 'per100': percent100})
    print(df.reset_index(inplace=True))
    return render_template('index.html',column_names=df.columns.values, row_data=list(df.values.tolist()),link_column="id", zip=zip)


@app.route('/charts',methods=['GET','POST'])
def charts():
    df2=getData()
    df2=df2.groupby("result").count()
    print(df2)
    source = ColumnDataSource(df2)
    results = source.data['result'].tolist()
    p = figure(x_range=results,plot_height=350,plot_width=900)
    color_map = factor_cmap(field_name='result',palette=Spectral5, factors=results)
    p.vbar(x='result', top='date', source=source, width=0.90, color=color_map)
    p.xaxis.axis_label = 'Bean Diseases'
    p.yaxis.axis_label = 'COUNT'
    hover = HoverTool()
    hover.tooltips = [("Totals", "@id")]
    hover.mode = 'vline'
    p.add_tools(hover)
    # script, div = components(p)
    html3 = file_html(p,CDN) 
    # dispaly piechart
    df2['angle'] = df2['date']/df2['date'].sum() * 2*pi
    df2['color'] = Category20c[len(df2)]
    p = figure(plot_height=350, toolbar_location=None,tools="hover", tooltips="@result: @date", x_range=(-0.5, 1.0))
    p.wedge(x=0, y=1, radius=0.4,start_angle=cumsum('angle', include_zero=True), end_angle=cumsum('angle'),line_color="white", fill_color='color', legend_field='result', source=df2)
    p.axis.axis_label=None
    p.axis.visible=False
    p.grid.grid_line_color = None
    html = file_html(p, CDN)   
    # creating line graph
    toy_df = pd.DataFrame(data=np.random.rand(5,3), columns = ('a', 'b' ,'c'), index = pd.DatetimeIndex(start='01-01-2015',periods=5, freq='d'))
    numlines=len(toy_df.columns)
    mypalette=Spectral11[0:numlines]
    p = figure(width=900, height=300, x_axis_type="datetime") 
    p.multi_line(xs=[toy_df.index.values]*numlines,
                    ys=[toy_df[name].values for name in toy_df],
                    line_color=mypalette,
                    line_width=5)
    html2 = file_html(p,CDN)

    return  render_template('chartjs.html',plot2=html2,plot=html,plot3=html3)

@app.route('/tables',methods=['GET','POST'])
def tables():
    results=db_connect.execute('select * from agrobean_results')
    return render_template('basic-tables.html',tables=results)
@app.route('/maps')
def maps():
    df2=getData()
    df2['lat'], df2['lng'] = df2['location'].str.split(',', 1).str
    df2['lat']=pd.to_numeric(df2['lat'],errors='coerce')
    df2['lng']=pd.to_numeric(df2['lng'],errors='coerce')
    start_coords = (1.373333,32.290276)
    folium_map = folium.Map(
        location=start_coords, 
        zoom_start=7.5
    )
    for lat,lng in zip(df2.lat,df2.lng):
        folium.CircleMarker([lat,lng],popup='67%',tooltip="click for more",radius=8).add_to(folium_map)
    folium_map.save('templates/map.html')
    return render_template('mapjs.html')
@app.route('/map')
def map():
    return render_template('map.html')

if __name__ == '__main__':
    
    app.run()

