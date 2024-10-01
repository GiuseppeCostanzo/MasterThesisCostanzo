# This Utility.py contains various classes and functions to support the GUI

from tkinter import ttk
import tkinter as tk
import json
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import copy

class Toolbox(tk.Frame): 

    # Create table to display numerical values in "View a movement"
    def create_table(gui_instance, headers, data):
        frame = tk.Frame(gui_instance)
        frame.pack(expand=True, fill="both")

        tree = ttk.Treeview(frame, columns=headers, show="headings")

        # Aggiunta header
        for header in headers:
            tree.heading(header, text=header, anchor="center")
            tree.column(header, width=80)

        # Aggiunta dati
        data_new = data.tolist()
        for row in data_new:
            tree.insert("", "end", values=row)

        # Scrollbar
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        tree.pack(expand=True, fill="both")
        return frame

    # This 2 functions (calculus and mapping) maps an input value (in range 0-100) to the corresponding value on the servo,
    # accordingly to the configuration on the json file
    def calculus(val,start,stop):
        if start==0:
            return int((val/100)*stop)
        else:
            new_stop = stop - start
            return int(((val/100)*new_stop)+start)  

    def mapping(self,thumb_big_value, thumb_little_value, index_finger_value, middle_finger_value, ringPinky_value, forearm_value):
        with open("config.json", "r") as json_file:
        #Load the contents of the JSON file into a Python dictionary
            data = json.load(json_file)
        
        #thumb - big servo
        thumb_big = data["thumb_big"]
        
        #thumb - little servo
        thumb_little = data["thumb_little"]
        
        #index_finger servo
        index_finger = data["index_finger"]

        #middle_finger servo
        middle_finger = data["middle_finger"]
    
        #ring_finger servo
        ring_pinky = data["ring_pinky"]
    
        #forearm servo
        forearm = data["forearm"]

        #All inputs
        input_values = [thumb_big_value, thumb_little_value, index_finger_value, middle_finger_value, ringPinky_value, forearm_value]
        #All range
        fingers_data = [thumb_big, thumb_little, index_finger, middle_finger, ring_pinky,forearm]
        fingers_data_mapped = []
        i = 0
        for single_finger in fingers_data:
            start = single_finger["range_from"]
            stop = single_finger["range_to"]
            fingers_data_mapped.append(self.calculus(input_values[i],start,stop))
            i = i+1
            
        return fingers_data_mapped

    # Used in discretize complex movement
    def sort_and_structure(data):
        data_copied = copy.deepcopy(data)
        # Identificare la radice 
        # Filtra solo i dizionari di tipo 'complex'
        dict_complex = [d for d in data_copied if d['type'] == 'complex']

        if len(dict_complex) == 1:
            dizionario_diverso = dict_complex[0]
            for d in data_copied:
                if d['id'] == dizionario_diverso['id']:
                    d['root'] = ''
                    break
        elif len(dict_complex) > 1:
            
            # Trova le roots
            roots = {d['root'] for d in dict_complex}

            if len(roots) == 2:
            # Trova la root che appare più volte
                root_comune = max(roots, key=lambda r: sum(1 for d in dict_complex if d['root'] == r))

                dizionario_diverso = next((d for d in dict_complex if d['root'] != root_comune), None)
                if dizionario_diverso:
                    # Aggiorna la root nel dizionario originale
                    for d in data_copied:
                        if d['id'] == dizionario_diverso['id']:
                            d['root'] = ''
                            break
            else:
                print("Error in sort_and_Structure 1")
                root_comune = None
        else:
            print("Error in sort_and_structure 2")

        # Ordina la lista di dizionari in base all'indice
        sorted_data = sorted(data_copied, key=lambda x: int(x['index']))
        
        # Dizionario per trovare rapidamente un elemento per id
        id_map = {item['id']: item for item in sorted_data}
        
        # Dizionario per mantenere la struttura gerarchica
        hierarchy = {}

        # Funzione ricorsiva per costruire la gerarchia e lista ordinata
        def add_children(parent):
            children = [item for item in sorted_data if item['root'] == parent['id']]
            parent['children'] = children
            for child in children:
                add_children(child)
        
        # Trova gli elementi radice (quelli senza root)
        roots = [item for item in sorted_data if item['root'] == '']

        # Costruisce la gerarchia per ogni elemento radice
        for root in roots:
            add_children(root)
            hierarchy[root['id']] = root
        
        # Funzione per creare la lista ordinata dalla struttura gerarchica
        def build_ordered_list(node, ordered_list):
            ordered_list.append(node)
            for child in node.get('children', []):
                build_ordered_list(child, ordered_list)
            # Rimuovi il campo children per mantenere la struttura originale
            node.pop('children', None)

        ordered_list = []
        for root in roots:
            build_ordered_list(root, ordered_list)
        
        return ordered_list
    

    def sort_and_structure2(data):

        # Ordina la lista di dizionari in base all'indice
        sorted_data = sorted(data, key=lambda x: int(x['index']))
        
        # Dizionario per trovare rapidamente un elemento per id
        id_map = {item['id']: item for item in sorted_data}
        
        # Dizionario per mantenere la struttura gerarchica
        hierarchy = {}

        # Funzione ricorsiva per costruire la gerarchia e lista ordinata
        def add_children(parent):
            children = [item for item in sorted_data if item['root'] == parent['id']]
            parent['children'] = children
            for child in children:
                add_children(child)
        
        # Trova gli elementi radice (quelli senza root)
        roots = [item for item in sorted_data if item['root'] == '']

        # Costruisce la gerarchia per ogni elemento radice
        for root in roots:
            add_children(root)
            hierarchy[root['id']] = root
        
        # Funzione per creare la lista ordinata dalla struttura gerarchica
        def build_ordered_list(node, ordered_list):
            ordered_list.append(node)
            for child in node.get('children', []):
                build_ordered_list(child, ordered_list)
            # Rimuovi il campo children per mantenere la struttura originale
            node.pop('children', None)

        ordered_list = []
        for root in roots:
            build_ordered_list(root, ordered_list)
        
        return ordered_list
    
    # Crea plot
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
        plot.set_ylabel('Servo Value')

        plot.set_ylim(0, 100)

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


