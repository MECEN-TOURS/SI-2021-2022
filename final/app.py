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
        self._init_symboles()
        self._init_svg_formule()

    def _init_symboles(self):
        """Initialise les différentes expressions utiles."""
        self.sa = sp.Symbol("a")
        self.sb = sp.Symbol("b")
        self.sd = sp.Symbol("d")
        self.sR = sp.Symbol("R")
        self.sp1 = sp.Symbol("p_1")
        self.sp2 = sp.Symbol("p_2")
        self.sq1 = sp.Symbol("q_1")
        self.sq2 = sp.Symbol("q_2")
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

    def _init_svg_formule(self):
        u = sp.latex(self.sU)
        pdf = latextools.render_snippet(f"$\\max U={u}$")
        pdf.as_svg().as_drawing(scale=2).saveSvg("assets/utilite.svg")

    def _calcule_point_critique(self) -> tuple[float, float]:
        solution = sp.solve(
            [self.sU.diff(self.sq1), self.sU.diff(self.sq2)], [self.sq1, self.sq2]
        )
        sol_q1 = solution[self.sq1]
        sol_q2 = solution[self.sq2]
        substitutions = {
            self.sa: self.a,
            self.sb: self.b,
            self.sd: self.d,
            self.sR: self.R,
            self.sp1: self.p1,
            self.sp2: self.p2,
        }
        q1 = sol_q1.subs(substitutions)
        q2 = sol_q2.subs(substitutions)
        return float(q1), float(q2)

    def utilite(self, x):
        """Fonction d'utilite numérique à maximiser."""
        q1, q2 = x
        return (
            self.R
            + (self.a - self.p1) * q1
            + (self.a - self.p2) * q2
            - (self.b * (q1 ** 2 + q2 ** 2) + 2 * self.d * q1 * q2) / 2
        )

    def contrainte(self, x):
        """Fonction de contrainte numérique qui doit rester positive."""
        q1, q2 = x
        return self.R - q1 * self.p1 - q2 * self.p2

    def _echantillonne(self):
        q1s = np.linspace(0, self.R / self.p1, 100)
        q2s = np.linspace(0, self.R / self.p2, 100)
        Q1, Q2 = np.meshgrid(q1s, q2s)
        U = self.utilite([Q1, Q2])
        masque = self.contrainte([Q1, Q2]) < 0
        U[masque] = None
        return q1s, q2s, U

    def genere_contour(self):
        Q1, Q2, U = probleme._echantillonne()
        try:
            M = np.nanmax(U)
        except TypeError:
            M = self.R
        return go.Contour(x=Q1, y=Q2, z=U, contours=dict(start=0, end=M))

    def genere_max(self):
        q1, q2 = self._calcule_point_critique()
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


def genere_slider(parametre: str, valeur: float) -> html.Div:
    if parametre == "d":
        m = -5
        M = 5
    else:
        m = 1
        M = 10
    return html.Div(
        children=[
            html.Label(
                f"{parametre}={probleme.a}",
                id=f"affichage_{parametre}",
                style={"textAlign": "center"},
            ),
            dcc.Slider(id=parametre, value=valeur, min=m, max=M, step=0.2),
        ]
    )


def genere_apparence(app, probleme) -> html.Div:
    return html.Div(
        children=[
            html.H1(
                "Prise de décision du consommateur",
                id="Titre",
                style={"textAlign": "center"},
            ),
            html.Div(
                html.Img(src=app.get_asset_url("utilite.svg")),
                id="Formule",
                style=dict(textAlign="center"),
            ),
            html.Div(
                children=[
                    html.Div(
                        children=[
                            genere_slider(parametre="a", valeur=probleme.a),
                            genere_slider(parametre="b", valeur=probleme.b),
                            genere_slider(parametre="d", valeur=probleme.d),
                            genere_slider(parametre="R", valeur=probleme.R),
                            genere_slider(parametre="p1", valeur=probleme.p1),
                            genere_slider(parametre="p2", valeur=probleme.p2),
                        ],
                        style={"flex": 1},
                    ),
                    dcc.Graph(id="Figure", figure=probleme.genere_figure()),
                ],
                style={"display": "flex", "flex-direction": "row"},
            ),
        ]
    )


app = dash.Dash()
probleme = Probleme()
app.layout = genere_apparence(app, probleme)


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
    probleme.a = a
    probleme.b = b
    probleme.d = d
    probleme.R = R
    probleme.p1 = p1
    probleme.p2 = p2
    return (
        probleme.genere_figure(),
        f"a={probleme.a}",
        f"b={probleme.b}",
        f"d={probleme.d}",
        f"R={probleme.R}",
        f"p1={probleme.p1}",
        f"p2={probleme.p2}",
    )


app.run_server(debug=True)
