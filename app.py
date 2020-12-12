from flask import Flask,render_template,url_for,redirect,request
from sqlalchemy import create_engine
import math
import json
import plotly
import plotly.graph_objs as go
import plotly.express as px
from math import pi
import numpy as np
import pandas as pd
import folium
import sqlite3
from flaskwebgui import FlaskUI
from extract import extract_result
import petl as etl
db_connect = engine = create_engine('sqlite:///example.db')
global conn
conn = sqlite3.connect('example.db')

app = Flask(__name__)
ui = FlaskUI(app)
conn.execute('CREATE TABLE IF NOT EXISTS staff (id INTEGER PRIMARY KEY AUTOINCREMENT ,name TEXT, email TEXT, contact TEXT, role_ TEXT,location TEXT)')
conn.close()
def getData():
    sql = "select * from agrobean_results"
    df = pd.read_sql(sql, db_connect)
    return df
# create bar graph
def bar_graph():
    df2=getData()
    df2=df2.groupby("result").count()
    df2 = pd.DataFrame(df2)
    df2.reset_index(inplace=True)
    data = [
        go.Bar(
            x=df2['result'], # assign x as the dataframe column 'x'
            y=df2['id']
        )
    ]
    graphJSON = json.dumps(data, cls=plotly.utils.PlotlyJSONEncoder)
    return graphJSON
# create line graph
def line_graph():
    df2=getData()
    # bean rust
    dfr=df2.loc[df2['result'] == 'Bean rust']
    dfr['count']=dfr.groupby('date')['date'].transform('count')
    # Angular leaf spot
    dfl=df2.loc[df2['result'] == 'Angular Leaf Spot']
    dfl['count']=dfl.groupby('date')['date'].transform('count')
    # healthy
    dfh=df2.loc[df2['result'] == 'Healthy']
    dfh['count']=dfh.groupby('date')['date'].transform('count')
    data = [
        go.Scatter(
            x=dfl['date'], # assign x as the dataframe column 'x'
            y=dfl['count'],
            # mode='Angular+Leaf+Spot',
            name='Angular Leaf Spot'
        ),
        go.Scatter(
            x=dfh['date'], # assign x as the dataframe column 'x'
            y=dfh['count'],
            # mode='Healthy',
            name='Healthy'
        )
    ]
    
    graphJSON = json.dumps(data, cls=plotly.utils.PlotlyJSONEncoder)
    return graphJSON
def pie_chart():
    df2=getData()
    df2=df2.groupby("result").count()
    df2 = pd.DataFrame(df2)
    df2.reset_index(inplace=True)
    data = [
        go.Pie(
            labels=df2['result'], # assign x as the dataframe column 'x'
            values=df2['id']
        )
    ]
    graphJSON = json.dumps(data, cls=plotly.utils.PlotlyJSONEncoder)
    return graphJSON
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
    con=sqlite3.connect("example.db")
    cur = con.cursor()
    cur.execute("select * from staff")
    rows = cur.fetchall()
    
    # counts
    # bean rust
    dfr=df2.loc[df2['result'] == 'Bean rust']
    dfr['count']=dfr.groupby('date')['date'].transform('count')
    bean_rust=dfr['count'].sum()
    # Angular leaf spot
    dfl=df2.loc[df2['result'] =="Angular Leaf Spot"]
    dfl['count']=dfl.groupby('date')['date'].transform('count')
    agl=dfl['count'].sum()
    # healthy
    dfh=df2.loc[df2['result'] == 'Healthy']
    dfh['count']=dfh.groupby('date')['date'].transform('count')
    health=dfh['count'].sum()

    
    all_res=health+agl
    s = df2.result
    counts = s.value_counts()
    percent = s.value_counts(normalize=True)
    percent100 = s.value_counts(normalize=True).mul(100).round(1).astype(str) + '%'
    df=pd.DataFrame({'counts': counts, 'per': percent, 'per100': percent100})
    # print(df.reset_index(inplace=True))

    results=db_connect.execute('select * from agrobean_results')
    trial = []
    for row in results:
        trial.append(row[1])
    dianosis_count =trial.count('Angular Leaf Spot')
    dianosis_count_ =trial.count('Healhty')
    
  
    
    
    return render_template('index.html',column_names=df.columns.values, 
    link_column="id", zip=zip,agl=dianosis_count,hl=dianosis_count_ ,all_res=dianosis_count+dianosis_count_ ,row_data=rows)


@app.route('/charts',methods=['GET','POST'])
def charts():
    bar =bar_graph()
    line =line_graph()
    pie=pie_chart()
    return  render_template('chartjs.html',plot=bar,plot2=line,plot3=pie)

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
@app.route('/register_staff')
def register_staff():
    return render_template('Experts.html')
# add staff to db 
@app.route('/add_staff', methods=['GET','POST'])
def add_staff():
    if request.method=="POST":
        username=request.form["username"]
        email=request.form["email"]
        contact=request.form["contact"]
        role=request.form["role"]
        location=request.form["location"]
        with sqlite3.connect("example.db") as conn:
            cur=conn.cursor()
            cur.execute("INSERT INTO staff(name,email,contact,role_,location) VALUES(?,?,?,?,?)",(username,email,contact,role,location))
            conn.commit()
    return render_template('Experts.html')
    
extract_result()
ui.run()
# if __name__ == '__main__':
    
    
#     app.run(debug=True)

