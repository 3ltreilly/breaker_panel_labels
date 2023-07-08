"""Make color coded pdf of your circuit breaker labels

Returns:
    pdf: PDF of labels
"""
import math
from pathlib import Path
import re
from tkinter import filedialog
import tkinter as tk

import click
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate
from reportlab.platypus import Table
from reportlab.platypus import TableStyle


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


def set_floor_color(the_canvas, row):
    """Set box color based on floor

    Args:
        c (report_lab_obj): report lab canvas
        row (array): row from csv file
    """
    if row.floor == "basement":
        the_canvas.setStrokeColor(colors.blue)
    elif row.floor == "1st":
        the_canvas.setStrokeColor(colors.green)
    elif row.floor == "2nd":
        the_canvas.setStrokeColor(colors.red)
    elif row.floor == "outside":
        the_canvas.setStrokeColor(colors.brown)
    else:
        the_canvas.setStrokeColor(colors.gray)


# inputs
BOX_W = 2 * inch
BOX_H = inch
start_point = [0, 11 * inch]  # top of page
BOX_LINE = 6
FUDGE = 32
# THE_FONT = "Courier"
THE_FONT = "Helvetica"


@click.command()
@click.argument("csv_file", type=click.Path(exists=True), required=False)
def cli(csv_file):
    """Make color coded brake panel label

    Args:
        csv_file (str): file with panel info.
    """
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

    # Get unique list of panels in the csv.  Output separate set of files
    # for each panel listed
    panels = df.panel.unique()

    for panel in panels:
        label_file = f"{csv_file.stem}_{panel}_labels.pdf"
        table_file = f"{csv_file.stem}_{panel}_table.pdf"
        can = canvas.Canvas(label_file)
        for _index, row in df.iterrows():
            if row.panel != panel:
                continue
            # check for 20th breaker
            if row.number >= 21:
                start_point = [BOX_W * 2, 10 * inch + 11 * inch]
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
            x = start_point[0] + paper_col * BOX_W

            set_floor_color(can, row)
            # set line details in the rect call or can set them before
            can.setLineWidth(BOX_LINE)
            # make rounded corners
            can.setLineJoin(1)
            can.rect(x + FUDGE, y, BOX_W - FUDGE, BOX_H, fill=0)

            textobject = can.beginText(x + BOX_LINE + FUDGE, y + BOX_H - BOX_LINE * 2)
            textobject.setFont(THE_FONT, 10)
            # add room name
            try:
                room_name = row.room.strip().capitalize()
            except AttributeError:
                room_name = ""
            text_width = stringWidth(room_name, THE_FONT, 10)  # get length of string
            cur_offset = (
                (BOX_W - FUDGE) / 2 - text_width / 2 - BOX_LINE
            )  # fake a horizontal center layout
            textobject.moveCursor(cur_offset, 0)
            textobject.setFont(THE_FONT + "-Bold", 10)  # make bold
            textobject.textLine(room_name)  # set name
            textobject.moveCursor(-cur_offset, 0)
            textobject.setFont(THE_FONT, 10)

            for circuit in circuits:
                textobject.textLine(circuit.strip().capitalize())
            can.drawText(textobject)
            # make circuit number label
            circ_num_obj = can.beginText(x + BOX_LINE, y + BOX_H / 2 - BOX_LINE + 5)
            circ_num_obj.setFont(THE_FONT, 19)
            circ_num_obj.textLine(str(row.number))
            # add amp number
            if row.amp:
                circ_num_obj.setFont(THE_FONT, 6)
                circ_num_obj.textLine(row.amp)
                circ_num_obj.textLine("Amps")
            # add Emporia tracking number
            if row.vue_number:
                tweak = [-3, -1]
                if len(row.vue_number) == 1:
                    can.drawString(
                        x + BOX_W - 10 + tweak[0], y + 10 + tweak[1], row.vue_number
                    )
                    can.setLineWidth(2)
                    can.setStrokeColor(colors.darkblue)
                    can.circle(
                        x + BOX_W - 8 + tweak[0], y + 13 + tweak[1], 0.1 * inch, fill=0
                    )
                else:
                    can.drawString(
                        x + BOX_W - 15 + tweak[0], y + 10 + tweak[1], row.vue_number
                    )
                    can.setLineWidth(2)
                    can.setStrokeColor(colors.darkblue)
                    can.circle(
                        x + BOX_W - 10 + tweak[0],
                        y + 13 + tweak[1],
                        0.13 * inch,
                        fill=0,
                    )
            can.drawText(circ_num_obj)
        can.showPage()
        can.save()

        doc = SimpleDocTemplate(
            csv_file.with_name(table_file).as_posix(),
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
