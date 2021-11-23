'''
make labels for breaker panel
list what is controls
list amps
color code for which floor, colored box
list the room(s)???
tracked or not
'''
import os
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch

import pandas as pd

def colorsRGB(canvas, list):
    from reportlab.lib import colors
    # from reportlab.lib.units import inch
    num_colums = 3
    y= 650
    x = 0; dy=inch*2; dx=inch*5.5/num_colums; w=h=dy/2; rdx=(dx-w)/2
    rdy=h/5.0; texty=h+2*rdy
    canvas.setFont("Helvetica",10)

    canvas.setLineWidth(6)
    # make rounded corners
    canvas.setLineJoin(1)
    canvas.setStrokeColor(colors.blue)
    # set line details in the rect call or can set them before
    canvas.rect(x+rdx, y+rdy, w, h, fill=0, strokeColor=colors.blue, strokeWidth=6)
    # canvas.setFillColor()
    # canvas.drawCentredString(x+dx/2, y+texty, name)
    textobject = canvas.beginText(x+rdx+5, y+rdy+h-16)
    textobject.setFont("Helvetica-Oblique", 8)
    for circuit in list:    
        textobject.textLine(circuit.strip().capitalize())
    canvas.drawText(textobject)
    x = x+dx

if __name__ == "__main__":
    df = pd.read_csv("test.csv")
    c = canvas.Canvas("hello.pdf")
    # move the origin up and to the left
    c.translate(inch,inch)
    # textobject = c.beginText(0, 650)
    # textobject.setFont("Helvetica-Oblique", 14)
    # c.rect(0,650,200,30)
    circuits = []
    for circuit in df.iloc[1].circuits.split(';'):
        circuits.append(circuit.strip().capitalize())
        # textobject.textLine(circuit.strip().capitalize())
    
    # c.drawText(textobject)
    # good example of putting shit in space
    colorsRGB(c, circuits)

    c.showPage()
    c.save()

