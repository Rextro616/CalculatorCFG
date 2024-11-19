from flask import Flask, render_template, request
from lark import Lark, Token, Transformer, Tree
import matplotlib
matplotlib.use('Agg')  # Establece el backend 'Agg' para evitar la interfaz gráfica
import matplotlib.pyplot as plt

import os

app = Flask(__name__)

# Gramática para la calculadora
grammar = """
?start: expr
?expr: term
     | expr "+" term   -> add
     | expr "-" term   -> sub
?term: factor
     | term "*" factor -> mul
     | term "/" factor -> div
?factor: NUMBER        -> number
       | "(" expr ")"  -> parens
NUMBER: /\d+(\.\d+)?/
%ignore " "            
"""

# Analizador (Parser)
parser = Lark(grammar, start='start', parser='lalr')

# Transformador para construir el árbol
class CalculateTree(Transformer):
    def number(self, args):
        return float(args[0])

    def parens(self, args):
        return args[0]
    
    def add(self, args):
        return args[0] + args[1]

    def sub(self, args):
        return args[0] - args[1]

    def mul(self, args):
        return args[0] * args[1]

    def div(self, args):
        if args[1] == 0:
            raise ValueError("División por cero")
        return args[0] / args[1]

# Función para limpiar el árbol
def clean_tree(tree):
    if isinstance(tree, Tree):
        return (tree.data, [clean_tree(child) for child in tree.children])
    elif isinstance(tree, Token):
        return float(tree) if tree.type == "NUMBER" else str(tree)
    else:
        return tree

# Función para dibujar el árbol con Matplotlib
def draw_tree(node, x=0, y=0, x_offset=1.5, y_offset=1, graph=None):
    """Dibuja un árbol utilizando Matplotlib."""
    if graph is None:
        fig, graph = plt.subplots(figsize=(10, 6))

    if isinstance(node, tuple):  # Nodo con hijos
        label = str(node[0])
        graph.text(x, y, label, ha='center', bbox=dict(boxstyle="round", facecolor="lightblue"))
        for i, child in enumerate(node[1], start=1):
            new_x = x + x_offset * (i - (len(node[1]) / 2))  # Espaciado entre hijos
            new_y = y - y_offset
            graph.plot([x, new_x], [y - 0.1, new_y + 0.1], color="black")  # Línea entre nodos
            draw_tree(child, new_x, new_y, x_offset / 2, y_offset, graph)
    else:  # Nodo hoja
        graph.text(x, y, str(node), ha='center', bbox=dict(boxstyle="round", facecolor="lightgreen"))

    graph.axis("off")
    return graph

@app.route("/", methods=["GET", "POST"])
def index():
    tree_path = None
    error = None
    result = None
    
    if request.method == "POST":
        expression = request.form['expression']
        try:
            # Generar el árbol sintáctico
            tree = parser.parse(expression)
            parsed_tree = clean_tree(tree)

            # Calcular el resultado
            transformer = CalculateTree()
            result = transformer.transform(tree)
            
            # Dibujar el árbol
            fig = draw_tree(parsed_tree)
            tree_path = "static/tree.png"
            plt.savefig(tree_path)
            plt.close()
        except Exception as e:
            error = f"Error al procesar la expresión: {e}"

    return render_template("index.html", tree_path=tree_path, result=result, error=error)

if __name__ == "__main__":
    app.run(debug=True)
