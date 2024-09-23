import numpy as np
import matplotlib.pyplot as plt
import tkinter as tk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from Discretizer import PreDiscr
from Utility import Toolbox


# elements_in_tree_view
'''elements_in_tree_view = [
 #{'id': 'I001', 'type': 'complex', 'index': 0, 'root': ''},
 #{'id': 'I002', 'values': [['80', '10', '20', '30', '100', '20', '1200'], ['10', '20', '30', '40', '50', '100', '2000'], '100'], 'type': 'linear', 'index': 2, 'root': 'I001'},
 #{'id': 'I003', 'values': ['400', '800', ['10', '2000', '0', '50'], ['5', '2000', '0', '70'], ['10', '2000', '0', '30'], ['5', '2000', '0', '90'], ['5', '2000', '0', '10'], ['10', '2000', '0', '80'], '70'], 'type': 'sinusoidal', 'index': 0, 'root': 'I001'},
 #{'id': 'I005', 'values': ['5', '2200', ['10', '10', '0', '50'], ['20', '10', '0', '50'], ['30', '10', '0', '50'], ['40', '10', '0', '50'], ['50', '10', '0', '50'], ['5', '2000', '0', '50'], '50'], 'type': 'sinusoidal', 'index': 0, 'root': 'I004'},
 #{'id': 'I006', 'values': [['20', '40', '100', '50', '0', '40', '500'], ['88', '60', '0', '10', '100', '90', '1500'], '80'], 'type': 'linear', 'index': 1, 'root': 'I004'},
 #{'id': 'I007', 'values': [['0', '0', '0', '0', '0', '0', '600'], ['100', '0', '0', '0', '0', '0', '1000'], '40'], 'type': 'linear', 'index': 1, 'root': 'I001'},
 {'id': 'I008', 'values': [['50', '60', '70', '20', '40', '10', '900'], ['90', '100', '40', '0', '10', '10', '1500'], '30'], 'type': 'linear', 'index': 1, 'root': ''},
 #{'id': 'I004', 'type': 'complex', 'index': 3, 'root': 'I001'}
]'''

elements_in_tree_view = [
{'id': 'I008', 'values': [['50', '60', '70', '20', '40', '10', '6000'], ['90', '100', '40', '0', '10', '10', '12000'], '30'], 'type': 'linear', 'index': 1, 'root': ''},
{'id': 'I009', 'values': ['0', '10000', ['15', '1000', '0', '50'], ['5', '1000', '0', '70'], ['10', '1000', '0', '30'], ['5', '1000', '0', '90'], ['5', '1000', '0', '10'], ['10', '2000', '0', '80'], '70'], 'type': 'sinusoidal', 'index': 0, 'root': ''},
]



final_result = PreDiscr.pre_discretize(elements_in_tree_view)


print(final_result)
# Creazione della finestra Tkinter
root = tk.Tk()
root.title("Visualizing complex movement")

# Creazione del plot
Toolbox.create_plot(root, final_result)

# Avvio dell'interfaccia grafica Tkinter
root.mainloop()

'''
if np.any(np.isnan(servomotors_values)):
            valori_validi = trova_valore_valido(funzioni[:i], t)
            servomotors_values = np.where(np.isnan(servomotors_values), valori_validi, servomotors_values)'''
