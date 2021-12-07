'''
make labels for breaker panel
list what is controls
list amps
color code for which floor, colored box
list the room(s)???
tracked or not
'''
import os
from reportlab.lib.rl_accel import instanceStringWidthTTF
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.platypus import Table, SimpleDocTemplate, TableStyle
from reportlab.lib.pagesizes import letter

import pandas as pd
import math
import re

# inputs
box_w = 2*inch
box_h = inch
start_point = [0,11*inch ] # top of page
box_line=6
fudge=32
panels = ['subpanel', 'main']
the_font = "Courier"
the_font = "Helvetica"


dtypes = {
    'room': 'string',
    'vue_number': 'string',
    # 'amp': 'int'
    }
df = pd.read_csv(
    "breaker panel labels.csv",
    keep_default_na=False,
    na_values='',
    na_filter=False,
    dtype=dtypes,
#   keep_default_na=False
  )
for panel in panels:
        
    c = canvas.Canvas(panel + "_labels.pdf")
    # move the origin up and to the left
    # c.translate(inch,inch)
    # textobject = c.beginText(0, 650)
    # textobject.setFont(the_font, 14)
    # c.rect(0,650,200,30)
    for index, row in df.iterrows():
        if row.panel != panel:
            continue
        # check for 20th breaker
        if row.number >= 21:
            start_point = [box_w*2,10*inch + 11*inch]
        else:
            start_point = [0,11*inch]

        try:
            if math.isnan(row.circuits):
                row.circuits = ""
        except TypeError:
            pass
        # get row on the physical paper sheet
        paper_row = math.ceil(row.number/2)
        paper_col = (row.number - 1) % 2
        # parse text for circuits
        circuits = []
        for circuit in re.split('[;|,|.]',row.circuits):
            circuits.append(circuit.strip().capitalize())
        # good example of putting shit in space
        y = start_point[1] - paper_row*inch
        x = start_point[0] + paper_col * box_w

        # c.setFont("Helvetica",14)

        if row.floor == "basement":
            c.setStrokeColor(colors.blue)
        elif row.floor == "1st":
            c.setStrokeColor(colors.green)
        elif row.floor == "2nd":
            c.setStrokeColor(colors.red)
        elif row.floor == "outside":
            c.setStrokeColor(colors.brown)
        else:
            c.setStrokeColor(colors.gray)
        # set line details in the rect call or can set them before
        c.setLineWidth(box_line)
        # make rounded corners
        c.setLineJoin(1)
        c.rect(x+fudge, y, box_w-fudge, box_h, fill=0)
        # c.setFillColor()
        # c.drawCentredString(x+dx/2, y+texty, name)
        textobject = c.beginText(x+box_line+fudge, y+box_h-box_line*2)
        textobject.setFont(the_font, 10)
        # add room name
        try:
            room_name = row.room.strip().capitalize()
        except AttributeError:
            room_name = ''
        textWidth = stringWidth(room_name, the_font, 10)  #get length of string
        cur_offset = (box_w-fudge)/2 - textWidth / 2 - box_line  #fake a horizontal center layout
        textobject.moveCursor(cur_offset,0)  
        textobject.setFont(the_font+"-Bold", 10)  #make bold
        textobject.textLine(room_name) # set name
        textobject.moveCursor(-cur_offset,0)
        textobject.setFont(the_font, 10)

        for circuit in circuits:    
            textobject.textLine(circuit.strip().capitalize())
        c.drawText(textobject)
        # make circuit number label
        circ_num_obj = c.beginText(x+box_line, y+box_h/2-box_line+5)
        circ_num_obj.setFont(the_font, 19)
        circ_num_obj.textLine(str(row.number))
        # add amp number
        if row.amp:
            circ_num_obj.setFont(the_font, 6)
            circ_num_obj.textLine(row.amp)
            circ_num_obj.textLine("Amps")
        # add Empria tracking number
        if row.vue_number:
            tweak = [-3,-1]
            if len(row.vue_number) == 1:
                c.drawString(x+box_w-10+tweak[0],y+10+tweak[1], row.vue_number)
                c.setLineWidth(2)
                c.setStrokeColor(colors.darkblue)
                c.circle(x+box_w-8+tweak[0],y+13+tweak[1], 0.1*inch, fill=0)
            else:
                c.drawString(x+box_w-15+tweak[0],y+10+tweak[1], row.vue_number)
                c.setLineWidth(2)
                c.setStrokeColor(colors.darkblue)
                c.circle(x+box_w-10+tweak[0],y+13+tweak[1], 0.13*inch, fill=0)                
        c.drawText(circ_num_obj)
    c.showPage()
    c.save()

    doc = SimpleDocTemplate(panel + "circuit_table.pdf", pagesize=letter, topMargin=inch/2)
    elements=[]
    # make table of circuits sorted by floor and room
    table_df = df[df.circuits != 'EMPTY'][df['panel'] == panel].sort_values(['floor', 'room'])
    table_df = table_df.drop('panel', axis='columns')
    # reset index after sort
    table_df = table_df.reset_index()
    column_list = table_df.columns.values.tolist()
    second = table_df.index[table_df['floor'] == '2nd'].tolist()
    first = table_df.index[table_df['floor'] == '1st'].tolist()
    basement = table_df.index[table_df['floor'] == 'basement'].tolist()
    outside = table_df.index[table_df['floor'] == 'outside'].tolist()
    data_list = table_df.values.tolist()
    data_list.insert(0,column_list)
    table = Table(data_list,style=[
        ('GRID',(0,0),(-1,-1),1,colors.black)])
    if first:
        table.setStyle(TableStyle([
            ('GRID',(0,first[0]+1),(-1,first[-1]+1),2,colors.green)
        ]))
    if second:
        table.setStyle(TableStyle([
            ('GRID',(0,second[0]+1),(-1,second[-1]+1),2,colors.red)
        ]))
    if basement:
        table.setStyle(TableStyle([
            ('GRID',(0,basement[0]+1),(-1,basement[-1]+1),2,colors.blue)
        ]))
    if outside:
        table.setStyle(TableStyle([
            ('GRID',(0,outside[0]+1),(-1,outside[-1]+1),2,colors.brown)
        ]))

    elements.append(table)
    doc.build(elements)