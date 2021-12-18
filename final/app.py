#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""Description.

Dashboard pour la visualisation d'un problème de concurrence.
"""
import latextools
import numpy as np
import plotly.graph_objects as go
import sympy as sp
from dataclasses import dataclass
import dash
from dash import dcc
from dash import html


@dataclass
class Probleme:
    a: float = 10.0
    b: float = 3.5
    d: float = -0.5
    R: float = 8.0
    p1: float = 1.0
    p2: float = 0.5

    def __post_init__(self):
        if self.a <= 0 or self.b <= 0 or self.R <= 0 or self.p1 <= 0 or self.p2 <= 0:
            raise ValueError("les coefficients hors d doivent être positifs.")
        if self.b <= abs(self.d):
            raise ValueError("on doit avoir |d| < b.")
        self._gen_symbolique()
        self._gen_svg()

    def _gen_symbolique(self):
        (
            self.sa,
            self.sb,
            self.sd,
            self.sR,
            self.sp1,
            self.sp2,
            self.sq1,
            self.sq2,
        ) = sp.symbols("a b d R p_1 p_2 q_1 q_2")
        self.sU = (
            self.sR
            + self.sq1 * (self.sa - self.sp1)
            + self.sq2 * (self.sa - self.sp2)
            - (
                self.sb * self.sq1 ** 2
                + self.sb * self.sq2 ** 2
                + 2 * self.sd * self.sq1 * self.sq2
            )
            / 2
        )

    def _gen_svg(self):
        u = sp.latex(self.sU)
        pdf = latextools.render_snippet(f"$\\max U={u}$")
        pdf.as_svg().as_drawing(scale=2).saveSvg("assets/utilite.svg")

    def _point_critique(self):

        solution = sp.solve(
            [self.sU.diff(self.sq1), self.sU.diff(self.sq2)], [self.sq1, self.sq2]
        )
        substitutions = {
            self.sa: self.a,
            self.sb: self.b,
            self.sd: self.d,
            self.sR: self.R,
            self.sp1: self.p1,
            self.sp2: self.p2,
        }
        q1 = solution[self.sq1].subs(substitutions)
        q2 = solution[self.sq2].subs(substitutions)
        return float(q1), float(q2)

    def utilite(self, x):
        q1, q2 = x
        return (
            self.R
            + (self.a - self.p1) * q1
            + (self.a - self.p2) * q2
            - (self.b * (q1 ** 2 + q2 ** 2) + 2 * self.d * q1 * q2) / 2
        )

    def contrainte(self, x):
        q1, q2 = x
        return self.R - q1 * self.p1 - q2 * self.p2

    def echantillon(self):
        q1s = np.linspace(0, self.R / self.p1, 100)
        q2s = np.linspace(0, self.R / self.p2, 100)
        Q1, Q2 = np.meshgrid(q1s, q2s)
        U = self.utilite([Q1, Q2])
        masque = self.contrainte([Q1, Q2]) < 0
        U[masque] = None
        return q1s, q2s, U

    def genere_contour(self):
        Q1, Q2, U = p.echantillon()
        try:
            M = np.nanmax(U)
        except TypeError:
            M = self.R
        return go.Contour(x=Q1, y=Q2, z=U, contours=dict(start=0, end=M))

    def genere_max(self):
        q1, q2 = self._point_critique()
        return go.Scatter(
            x=[q1],
            y=[q2],
            mode="markers",
            marker=dict(size=10, color="Black", opacity=0.5),
        )

    def genere_figure(self):
        return go.Figure(
            data=[self.genere_contour(), self.genere_max()],
            layout={
                "width": 600,
                "height": 600,
            },
        )


app = dash.Dash()
p = Probleme()
app.layout = html.Div(
    children=[
        html.H1(
            "Prise de décision du consommateur",
            id="Titre",
            style={"textAlign": "center"},
        ),
        html.Div(
            html.Img(src=app.get_asset_url("utilite.svg")),
            style=dict(textAlign="center"),
        ),
        html.Div(
            children=[
                html.Div(
                    children=[
                        html.Div(
                            children=[
                                html.Label(
                                    f"a={p.a}",
                                    id="affichage_a",
                                    style={"textAlign": "center"},
                                ),
                                dcc.Slider(id="a", value=p.a, min=1, max=10, step=0.5),
                            ]
                        ),
                        html.Div(
                            children=[
                                html.Label(
                                    f"b={p.b}",
                                    id="affichage_b",
                                    style={"textAlign": "center"},
                                ),
                                dcc.Slider(id="b", value=p.b, min=1, max=10, step=0.5),
                            ]
                        ),
                        html.Div(
                            children=[
                                html.Label(
                                    f"d={p.d}",
                                    id="affichage_d",
                                    style={"textAlign": "center"},
                                ),
                                dcc.Slider(id="d", value=p.d, min=-1, max=1, step=0.1),
                            ]
                        ),
                        html.Div(
                            children=[
                                html.Label(
                                    f"R={p.R}",
                                    id="affichage_R",
                                    style={"textAlign": "center"},
                                ),
                                dcc.Slider(id="R", value=p.R, min=1, max=10, step=0.5),
                            ]
                        ),
                        html.Div(
                            children=[
                                html.Label(
                                    f"p1={p.p1}",
                                    id="affichage_p1",
                                    style={"textAlign": "center"},
                                ),
                                dcc.Slider(
                                    id="p1", value=p.p1, min=0.05, max=1, step=0.05
                                ),
                            ]
                        ),
                        html.Div(
                            children=[
                                html.Label(
                                    f"p2={p.p2}",
                                    id="affichage_p2",
                                    style={"textAlign": "center"},
                                ),
                                dcc.Slider(
                                    id="p2", value=p.p2, min=0.05, max=1, step=0.05
                                ),
                            ]
                        ),
                    ],
                    style={"flex": 1},
                ),
                dcc.Graph(id="Figure", figure=p.genere_figure()),
            ],
            style={"display": "flex", "flex-direction": "row"},
        ),
    ]
)


@app.callback(
    [
        dash.Output("Figure", "figure"),
        dash.Output("affichage_a", "children"),
        dash.Output("affichage_b", "children"),
        dash.Output("affichage_d", "children"),
        dash.Output("affichage_R", "children"),
        dash.Output("affichage_p1", "children"),
        dash.Output("affichage_p2", "children"),
    ],
    [
        dash.Input("a", "value"),
        dash.Input("b", "value"),
        dash.Input("d", "value"),
        dash.Input("R", "value"),
        dash.Input("p1", "value"),
        dash.Input("p2", "value"),
    ],
)
def mise_a_jour(a, b, d, R, p1, p2):
    p.a = a
    p.b = b
    p.d = d
    p.R = R
    p.p1 = p1
    p.p2 = p2
    return (
        p.genere_figure(),
        f"a={p.a}",
        f"b={p.b}",
        f"d={p.d}",
        f"R={p.R}",
        f"p1={p.p1}",
        f"p2={p.p2}",
    )


app.run_server(debug=True)
