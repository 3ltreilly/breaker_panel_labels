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

import pandas as pd
import math
import re

# inputs
# big_h = 20*inch  #?
# big_w = 4*inch
box_w = 2*inch
box_h = inch
start_point = 11*inch  # top of page
box_line=6
fudge=32
panels = ['subpanel', 'main']
the_font = "Courier"
the_font = "Helvetica"


dtypes = {
    'room': 'string',
    # 'amp': int,
    }
df = pd.read_csv(
    "breaker panel labels.csv",
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
        y = start_point - paper_row*inch
        x = paper_col * box_w

        # c.setFont("Helvetica",14)
        c.setLineWidth(box_line)
        # make rounded corners
        c.setLineJoin(1)
        if row.floor == "basement":
            c.setStrokeColor(colors.blue)
        elif row.floor == "1st":
            c.setStrokeColor(colors.green)
        elif row.floor == "2nd":
            c.setStrokeColor(colors.red)
        else:
            c.setStrokeColor(colors.gray)
        # set line details in the rect call or can set them before
        c.rect(x+fudge, y, box_w-fudge, box_h, fill=0)
        # c.setFillColor()
        # c.drawCentredString(x+dx/2, y+texty, name)
        textobject = c.beginText(x+box_line+fudge, y+box_h-box_line*2)
        textobject.setFont(the_font, 10)
        try:
            room_name = row.room.strip().capitalize()
        except AttributeError:
            room_name = ''
        textWidth = stringWidth(room_name, the_font, 10)
        cur_offset = (box_w-fudge)/2 - textWidth / 2 - box_line
        textobject.moveCursor(cur_offset,0)
        textobject.setFont(the_font+"-Bold", 10)
        textobject.textLine(room_name)
        textobject.moveCursor(-cur_offset,0)
        textobject.setFont(the_font, 10)

        for circuit in circuits:    
            textobject.textLine(circuit.strip().capitalize())
        c.drawText(textobject)
        # make circuit number label
        circ_num_obj = c.beginText(x+box_line, y+box_h/2-box_line+5)
        circ_num_obj.setFont(the_font, 19)
        circ_num_obj.textLine(str(row.number))
        if not math.isnan(row.amp):
            circ_num_obj.setFont(the_font, 6)
            circ_num_obj.textLine(str(int(row.amp)))
            circ_num_obj.textLine("Amps")

        c.drawText(circ_num_obj)
    c.showPage()
    c.save()
