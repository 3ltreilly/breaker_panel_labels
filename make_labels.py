"""
make labels for breaker panel
list what is controls
list amps
color code for which floor, colored box
list the room(s)???
tracked or not
"""
import math
import re
import tkinter as tk
from pathlib import Path
from tkinter import filedialog

import click
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle


def parse_circuits(row):
    """Parse circuit name text from csv file

    Args:
        row (array): row from csv file

    Examples:
        >>> parse_circuits(
            pd.Series(
                [1, 30, "water heater", "subpanel", "basement", "basement", ""],
                index=["number", "amp", "circuits", "panel", "room", "floor", "vue_number"],
                )
            )
        ['Water heater']

    Returns:
        list: list of items controlled by circuit
    """
    circuits = []
    for circuit in re.split("[;|,|.]", row.circuits):
        circuits.append(circuit.strip().capitalize())
    return circuits


def set_floor_color(c, row):
    """Set box color based on floor

    Args:
        c (report_lab_obj): report lab canvas
        row (array): row from csv file
    """
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


# inputs
box_w = 2 * inch
box_h = inch
start_point = [0, 11 * inch]  # top of page
box_line = 6
fudge = 32
panels = ["subpanel", "main"]
the_font = "Courier"
the_font = "Helvetica"


@click.command()
@click.argument("csv_file", type=click.Path(exists=True), required=False)
def cli(csv_file):
# def cli():
    print("current directory is")
    print(Path.cwd())

    # check for argument, if not there ask for it in a gui
    if not csv_file:
        root = tk.Tk()
        root.withdraw()
        csv_file = filedialog.askopenfilename()

    csv_file = Path(csv_file)

    dtypes = {
        "room": "string",
        "vue_number": "string",
        # 'amp': 'int'
    }
    # read in csv file
    df = pd.read_csv(
        csv_file,
        keep_default_na=False,
        na_values="",
        na_filter=False,
        dtype=dtypes,
        #   keep_default_na=False
    )
    for panel in panels:

        c = canvas.Canvas(csv_file.with_name(panel + "_labels.pdf").as_posix())
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
                start_point = [box_w * 2, 10 * inch + 11 * inch]
            else:
                start_point = [0, 11 * inch]

            try:
                if math.isnan(row.circuits):
                    row.circuits = ""
            except TypeError:
                pass
            # get row on the physical paper sheet
            paper_row = math.ceil(row.number / 2)
            paper_col = (row.number - 1) % 2
            # parse text for circuits
            circuits = parse_circuits(row)
            # good example of putting shit in space
            y = start_point[1] - paper_row * inch
            x = start_point[0] + paper_col * box_w

            set_floor_color(c, row)
            # set line details in the rect call or can set them before
            c.setLineWidth(box_line)
            # make rounded corners
            c.setLineJoin(1)
            c.rect(x + fudge, y, box_w - fudge, box_h, fill=0)

            textobject = c.beginText(x + box_line + fudge, y + box_h - box_line * 2)
            textobject.setFont(the_font, 10)
            # add room name
            try:
                room_name = row.room.strip().capitalize()
            except AttributeError:
                room_name = ""
            textWidth = stringWidth(room_name, the_font, 10)  # get length of string
            cur_offset = (
                (box_w - fudge) / 2 - textWidth / 2 - box_line
            )  # fake a horizontal center layout
            textobject.moveCursor(cur_offset, 0)
            textobject.setFont(the_font + "-Bold", 10)  # make bold
            textobject.textLine(room_name)  # set name
            textobject.moveCursor(-cur_offset, 0)
            textobject.setFont(the_font, 10)

            for circuit in circuits:
                textobject.textLine(circuit.strip().capitalize())
            c.drawText(textobject)
            # make circuit number label
            circ_num_obj = c.beginText(x + box_line, y + box_h / 2 - box_line + 5)
            circ_num_obj.setFont(the_font, 19)
            circ_num_obj.textLine(str(row.number))
            # add amp number
            if row.amp:
                circ_num_obj.setFont(the_font, 6)
                circ_num_obj.textLine(row.amp)
                circ_num_obj.textLine("Amps")
            # add Emporia tracking number
            if row.vue_number:
                tweak = [-3, -1]
                if len(row.vue_number) == 1:
                    c.drawString(
                        x + box_w - 10 + tweak[0], y + 10 + tweak[1], row.vue_number
                    )
                    c.setLineWidth(2)
                    c.setStrokeColor(colors.darkblue)
                    c.circle(
                        x + box_w - 8 + tweak[0], y + 13 + tweak[1], 0.1 * inch, fill=0
                    )
                else:
                    c.drawString(
                        x + box_w - 15 + tweak[0], y + 10 + tweak[1], row.vue_number
                    )
                    c.setLineWidth(2)
                    c.setStrokeColor(colors.darkblue)
                    c.circle(
                        x + box_w - 10 + tweak[0],
                        y + 13 + tweak[1],
                        0.13 * inch,
                        fill=0,
                    )
            c.drawText(circ_num_obj)
        c.showPage()
        c.save()

        doc = SimpleDocTemplate(
            csv_file.with_name(panel + "circuit_table.pdf").as_posix(),
            pagesize=letter,
            topMargin=inch / 2,
        )
        elements = []
        # make table of circuits sorted by floor and room
        table_df = df[df.circuits != "EMPTY"][df["panel"] == panel].sort_values(
            ["floor", "room"]
        )
        table_df = table_df.drop("panel", axis="columns")
        # reset index after sort
        table_df = table_df.reset_index()
        table_df = table_df.drop("index", axis="columns")
        column_list = table_df.columns.values.tolist()
        second = table_df.index[table_df["floor"] == "2nd"].tolist()
        first = table_df.index[table_df["floor"] == "1st"].tolist()
        basement = table_df.index[table_df["floor"] == "basement"].tolist()
        outside = table_df.index[table_df["floor"] == "outside"].tolist()
        data_list = table_df.values.tolist()
        data_list.insert(0, column_list)
        table = Table(data_list, style=[("GRID", (0, 0), (-1, -1), 1, colors.black)])
        if first:
            table.setStyle(
                TableStyle(
                    [("GRID", (0, first[0] + 1), (-1, first[-1] + 1), 2, colors.green)]
                )
            )
        if second:
            table.setStyle(
                TableStyle(
                    [("GRID", (0, second[0] + 1), (-1, second[-1] + 1), 2, colors.red)]
                )
            )
        if basement:
            table.setStyle(
                TableStyle(
                    [
                        (
                            "GRID",
                            (0, basement[0] + 1),
                            (-1, basement[-1] + 1),
                            2,
                            colors.blue,
                        )
                    ]
                )
            )
        if outside:
            table.setStyle(
                TableStyle(
                    [
                        (
                            "GRID",
                            (0, outside[0] + 1),
                            (-1, outside[-1] + 1),
                            2,
                            colors.brown,
                        )
                    ]
                )
            )

        elements.append(table)
        doc.build(elements)


if __name__ == "__main__":
    cli()
