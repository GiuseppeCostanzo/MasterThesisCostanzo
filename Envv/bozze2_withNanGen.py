import numpy as np
import matplotlib.pyplot as plt
import tkinter as tk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from Discretizer import LinearMovement 
from Discretizer import SinusoidalMovement

# Parametri da preparare prima di chiamare il discretize
deltaT = 50  # intervallo di campionamento in millisecondi
t_end = 6000  # time end
t_start = 0  # time start

# Funzione di pre-discretizzazione come fornita
def pre_discretize_base(item):
    if item is None:
        return None

    if len(item) == 0:  # Se la lunghezza del dizionario è 0, è vuoto oppure è None
        return None
    
    if item["type"] == "linear":
        values = item["values"] #values(movement) of the item 
        
        start_time = int(values[0][6])
        end_time = int(values[1][6])

        start_pos = []
        for i in range(0,len(values[0])-1):
            start_pos.append(int(values[0][i]))

        end_pos = []
        for i in range(0,len(values[1])-1):
            end_pos.append(int(values[1][i]))

        deltaT = int(values[2]) 
        linMov = LinearMovement(start_time,end_time,start_pos,end_pos,deltaT)
        #movement to visualize/execute
        movement = linMov.discretize().tolist()
        return movement
        
    if item["type"] == "sinusoidal":
        values = item["values"] #values(movement) of the item   
        start_time = int(values[0])
        end_time = int(values[1])
        deltaT = int(values [8])
        
        amplitude = []
        for i in range(2,8):
            amplitude.append(int(values[i][0]))
            
        frequency = []
        for i in range(2,8):
            frequency.append(int(values[i][1]))
        
        phase = []
        for i in range(2,8):
            phase.append(int(values[i][2]))
        
        start_value_y = []
        for i in range(2,8):
            start_value_y.append(int(values[i][3]))
        
        sinMov = SinusoidalMovement(start_time,end_time,amplitude,frequency,phase,start_value_y,deltaT)
        movement = sinMov.discretize().tolist()
        return movement
    
# elements_in_tree_view
elements_in_tree_view = [
 {'id': 'I002', 'values': [['80', '10', '20', '30', '100', '20', '0'], ['10', '20', '30', '40', '50', '100', '1000'], '50'], 'type': 'linear', 'index': 0, 'root': 'I001'},
 {'id': 'I003', 'values': ['1200', '2000', ['60', '20', '0', '50'], ['70', '20', '0', '50'], ['80', '20', '0', '50'], ['90', '20', '0', '50'], ['100', '20', '0', '50'], ['110', '20', '0', '50'], '50'], 'type': 'sinusoidal', 'index': 1, 'root': 'I001'},
 {'id': 'I004', 'type': 'complex', 'index': 2, 'root': 'I001'},
 {'id': 'I005', 'values': ['400', '1200', ['10', '10', '0', '50'], ['20', '10', '0', '50'], ['30', '10', '0', '50'], ['40', '10', '0', '50'], ['50', '10', '0', '50'], ['60', '10', '0', '50'], '50'], 'type': 'sinusoidal', 'index': 0, 'root': 'I004'},
 {'id': 'I006', 'values': [['20', '40', '100', '50', '0', '25', '0'], ['88', '60', '0', '10', '100', '5', '3000'], '50'], 'type': 'linear', 'index': 1, 'root': 'I004'},
 {'id': 'I007', 'values': [['10', '20', '30', '40', '50', '40', '400'], ['50', '60', '70', '80', '90', '60', '500'], '50'], 'type': 'linear', 'index': 2, 'root': 'I004'}
]




# Funzione per trovare il valore valido precedente
'''def trova_valore_valido(elements_in_tree_view, t):
    for element in reversed(elements_in_tree_view):
        movimento = pre_discretize_base(element)
        if movimento is None:
            continue
        for val in movimento:
            if val[0] == t:
                return val[1]
    return np.nan'''

# ----------Campionamento e combinazione degli elementi inelements_in_tree_view----------

#crea un array della stessa lunghezza di t_totale riempito con NaN. 
# Questo array conterrà i valori combinati delle elements_in_tree_view.
# Array 2D per tutti i valori di servomotore
#y_totale = np.full((len(t_totale), 5), np.nan, dtype=float)

# Preparazione dell'output
output = []

# Generazione dell'array di tempi
t_totale = np.arange(t_start, t_end + deltaT, deltaT)

#DEVO CAMPIONARE CON IL DELTA T PIù PICCOLO!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
#----> al momento nei valori di prova ci sono deltaT tutti uguali a 50
for funzione in elements_in_tree_view:
    movimento = pre_discretize_base(funzione)
    if movimento is None:
        continue
    for row in movimento:
        t = row[-1]  # l'ultimo elemento di ogni riga è l'istante temporale
        servomotori = row[:6]  # i primi 5 elementi sono i valori dei servomotori
        
        idx = int((t - t_start) // deltaT)
        if idx >= len(t_totale):
            continue
        
        if np.any(np.isnan(servomotori)):
            #valori_validi = trova_valore_valido(elements_in_tree_view[:elements_in_tree_view.index(funzione)], t)
            #servomotori = np.where(np.isnan(servomotori), valori_validi, servomotori)
            print("da gestire")
            exit
        
        # Aggiungi i valori e il tempo alla lista output
        output.append(np.append(servomotori, t))

# Convertiamo l'output in una lista di numpy.ndarray
output = [np.array(row) for row in output]


# Creazione del plot
def create_plot(master, movement):
    figure = Figure(figsize=(50, 50), dpi=75)
    #plot = figure.add_subplot(111)
    plot = figure.add_axes([0.08, 0.13, 0.85, 0.85])

    headers_y = ["Thumb(B)", "Thumb(L)", "Index", "Middle", "Ring/Pinky", "Forearm"]
    temp_inst = [row[-1] for row in movement]
    servo_values = [row[:-1] for row in movement]

    lines = [] 
    for i in range(6):
        valori_y = [val[i] for val in servo_values]
        line, = plot.plot(temp_inst, valori_y, label=headers_y[i])
        lines.append(line)

    plot.set_xlabel('Time instant (ms)')
    plot.set_ylabel('Values')

    # Function to update plot based on checkbox selection
    def update_plot():
        for i, line in enumerate(lines):
            if checkboxes_state[i].get():
                line.set_visible(True)
            else:
                line.set_visible(False)
        figure.canvas.draw()
    
    frame3 = tk.Frame(master)
    frame3.pack(side="left", expand=False, fill="y")
    
    # Create checkboxes
    checkboxes_state = []  # To store the checkbox states
    for i in range(6):
        var = tk.BooleanVar(value=True)  # True by default, you can set to False if needed
        checkboxes_state.append(var)
        checkbox = tk.Checkbutton(frame3, text=headers_y[i], variable=var, command=update_plot)
        checkbox.grid(row=i, column=0, sticky="w") 

    plot.legend(fontsize='small')
    plot.grid(True)

    canvas = FigureCanvasTkAgg(figure, master)
    canvas.get_tk_widget().pack(expand=True, fill="both")
    
# Creazione della finestra Tkinter
root = tk.Tk()
root.title("Visualizing complex movement")

# Creazione del plot
create_plot(root, output)
#print(output)
# Avvio dell'interfaccia grafica Tkinter
root.mainloop()
