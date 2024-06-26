import numpy as np
import matplotlib.pyplot as plt
import tkinter as tk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from Discretizer import LinearMovement 
from Discretizer import SinusoidalMovement
from Utility import Toolbox

# Parametri da preparare prima di chiamare il discretize
deltaT = 50  # intervallo di campionamento in millisecondi
t_end = 6000  # time end
t_start = 0  # time start

# single_movement di pre-discretizzazione come fornita
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
 {'id': 'I001', 'type': 'complex', 'index': 0, 'root': ''},
 #{'id': 'I002', 'values': [['80', '10', '20', '30', '100', '20', '0'], ['10', '20', '30', '40', '50', '100', '1000'], '50'], 'type': 'linear', 'index': 2, 'root': 'I001'},
 {'id': 'I003', 'values': ['0', '1000', ['10', '2000', '0', '50'], ['5', '2000', '0', '70'], ['10', '2000', '0', '30'], ['5', '2000', '0', '90'], ['5', '2000', '0', '10'], ['10', '2000', '0', '80'], '50'], 'type': 'sinusoidal', 'index': 0, 'root': 'I001'},
 #{'id': 'I005', 'values': ['0', '1000', ['10', '10', '0', '50'], ['20', '10', '0', '50'], ['30', '10', '0', '50'], ['40', '10', '0', '50'], ['50', '10', '0', '50'], ['5', '2000', '0', '50'], '50'], 'type': 'sinusoidal', 'index': 0, 'root': 'I004'},
 #{'id': 'I006', 'values': [['20', '40', '100', '50', '0', '40', '500'], ['88', '60', '0', '10', '100', '90', '1500'], '50'], 'type': 'linear', 'index': 1, 'root': 'I004'},
 {'id': 'I007', 'values': [['10', '20', '30', '40', '50', '60', '800'], ['50', '60', '70', '80', '90', '80', '1000'], '50'], 'type': 'linear', 'index': 1, 'root': 'I001'},
 #{'id': 'I008', 'values': [['80', '10', '20', '30', '100', '20', '0'], ['10', '20', '30', '40', '50', '100', '1000'], '50'], 'type': 'linear', 'index': 1, 'root': ''},
 #{'id': 'I004', 'type': 'complex', 'index': 3, 'root': 'I001'}
]




# ----------CAMPIONAMENTO---------------

#PHASE 1) 
# Sort the dictionary w.r.t to index(level) 
r = Toolbox.sort_and_structure(elements_in_tree_view)
#print(r)

# Delete the "head" of a complex movements (does not contain values)
result_without_head_complex = [diz for diz in r if diz.get("type") != "complex"]
#print(result)
# Discretize all the submovements
result_discr = []
for mov in result_without_head_complex:
    result_discr.append(pre_discretize_base(mov))


#for a in result_discr:
#    print(a)
#    print("--------------------------")

#FASE 2) Costruzione della single_movement complessa
#*************DEVO CAMPIONARE CON IL DELTA T PIù PICCOLO!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
#----> al momento nei valori di prova ci sono deltaT tutti uguali a 50

# Generazione dell'array di tempi
t_totale = np.arange(t_start, t_end + deltaT, deltaT)
output = []


def recursive_nan_reading(positions, row, index, result_discr):
    end = False
    if(index == 0):
        end = True

    values = result_discr[index][row]
    new_values = []
    for i,a in enumerate(values):
        if(i==positions[i]):
            new_values.append(a)

    if end == True:
        return new_values #!!!!!! gestire (può ritornare dei NaN)
    
    new_positions = []
    if(np.any(np.isnan(new_values))):
        for i,el in new_values:
            if np.isnan(el):
                new_positions.append(positions[i]) 
        
        return recursive_nan_reading(new_positions, row, index-1, result_discr)  
    else:
        return new_values







#result_discr list di list
for i, single_movement in enumerate(result_discr):

    t_next_start = t_end
    if i + 1 < len(result_discr):
        # Determina il tempo di inizio della single_movement successiva.
        t_next_start = int(result_without_head_complex[i + 1]["values"][0][6] if result_without_head_complex[i + 1]["type"] == "linear" else result_without_head_complex[i + 1]["values"][0])
    
    for row in single_movement:
        current_istant = row[-1]
        if current_istant >= t_next_start:
            break  # Interrompe il campionamento della single_movement corrente e passa alla successiva
                    # se si raggiunge il tempo di inizio della single_movement successiva.
        
        #gestire i NaN
        servomotors_values = row[:6] 

        # Se esiste un valore dei servomotors_values tale per cui almeno uno loro è NaN, devo guardare il corrsipondente 
        # valore nella funzione precedente
        if(np.any(np.isnan(servomotors_values))):
            #from 0 to 5 (included)
            nan_positions = np.where(np.isnan(servomotors_values))[0]
            values = recursive_nan_reading(nan_positions, row, i-1, result_discr)
        #print(result_discr[i])
        #print("-----------------------------------")
        # Aggiunta valori + istante di tempo tempo alla lista output (costruzione del campionamento)
        output.append(np.append(servomotors_values, current_istant))

    
# Creazione della finestra Tkinter
root = tk.Tk()
root.title("Visualizing complex movement")

# Creazione del plot
Toolbox.create_plot(root, output)

# Avvio dell'interfaccia grafica Tkinter
root.mainloop()

'''
if np.any(np.isnan(servomotors_values)):
            valori_validi = trova_valore_valido(funzioni[:i], t)
            servomotors_values = np.where(np.isnan(servomotors_values), valori_validi, servomotors_values)
'''
