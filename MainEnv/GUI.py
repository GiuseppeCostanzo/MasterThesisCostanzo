# Libraries
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter import Menu
import serial  
import json
import os
import time
import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkinter import filedialog

# Other files (must be in the same folder of GUI.py)
from Discretizer import LinearMovement
from Discretizer import SinusoidalMovement
from Discretizer import ComplexMovement
from Utility import Toolbox
import copy

# Global parameters, eventually to be set
usbport = 'COM5' # Usb port where arduino is connected 
arduino = None # Arduino communication instance
baud = 38400 # Baud - speed parameter for arduino comm. (MUST BE the same value in the arduino sketch)

# Internal usage
start_time = None # used to calculate the time start of the button
tree_view = [] #for visualizing the imported json in complex movement frame3

def save_movement(data):
    
    # Configura la finestra principale di Tkinter
    root = tk.Tk()
    root.withdraw()  # Nasconde la finestra principale di Tkinter
    root.attributes("-topmost", True)  # Imposta la finestra come topmost

    # Apre la finestra di dialogo di salvataggio
    file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")], parent=root)

    if file_path:
        # Scrive i dati JSON nel file selezionato
        with open(file_path, 'w', encoding='utf-8') as json_file:
            json.dump(data, json_file, ensure_ascii=False, indent=1)
        print(f"File JSON salvato in: {file_path}")
    else:
        print("Salvataggio annullato.")
    
    root.destroy()  # Chiude la finestra principale di Tkinter

# Apertura connessione seriale
def open_serial_port():
    global arduino 
    try:
        if arduino is None or not arduino.is_open:
            arduino = serial.Serial(port=usbport, baudrate=baud, timeout=.4) 
            time.sleep(2)
            return True
    except serial.SerialException as e:
        return False
        
        
# Funzione per la validazione dei campi di input della GUI
def on_validate(action, index, value_if_allowed, prior_value, text, validation_type, trigger_type, widget_name):
    if action == '1':  # Inserimento di un carattere
        if text in '0123456789.-+':
            try:
                # Converti il valore in un float
                int_value = int(value_if_allowed)
                # Verifica se il valore è compreso tra 0 e 100
                if 0 <= int_value <= 100:
                    return True
                else:
                    return False
            except ValueError:
                return False
        else:
            return False
    else:
        return True


# Funzione per la validazione del campo di input "time" della GUI (per i valori interi in millisecondi)
def on_validate2(action, index, value_if_allowed, prior_value, text, validation_type, trigger_type, widget_name):
    if action == '1':  # Inserimento di un carattere
        if text in '0123456789.-+':
            try:
                # Converti il valore in un int
                float_value = int(value_if_allowed)
                # Verifica se il valore è compreso tra 0 e 100.000 (100 secondi)
                if 0 <= float_value <= 100000:
                    return True
                else:
                    return False
            except ValueError:
                return False
        else:
            return False
    else:
        return True
    
# Funzione per validare campo input amplitude shift 
def validate_amp_shift(value):
    # Permetti stringa vuota per la cancellazione
    if value == "":
        return True
    try:
        # Se l'input è solo "-", permettilo temporaneamente
        if value == "-":
            return True
        # Converti il valore in float
        num = float(value)
        # Controlla se il numero è nel range [-1, 1]
        if -1 <= num <= 1:
            return True
        else:
            return False
    except ValueError:
        # Se non è un numero valido, blocca l'input
        return False
    
#Funzione per valdiare campi che accettano float (es. scala specifico)
def validate_float_input(text):
    if text.strip() == "":
        return True  # Accetta l'input vuoto
    try:
        float(text)
        return True
    except ValueError:
        return False

#create the tooltip info
def create_tooltip(widget, text):
    tooltip_window = None

    def show_tooltip(event):
        nonlocal tooltip_window
        if tooltip_window is not None:
            return
        x, y, _, _ = widget.bbox("insert")
        x += widget.winfo_rootx() + 25
        y += widget.winfo_rooty() + 25
        tooltip_window = tk.Toplevel(widget)
        tooltip_window.wm_overrideredirect(True)
        tooltip_window.wm_geometry(f"+{x}+{y}")
        label = tk.Label(tooltip_window, text=text, background="white", borderwidth=1, relief="solid")
        label.pack()

    def hide_tooltip(event):
        nonlocal tooltip_window
        if tooltip_window is not None:
            tooltip_window.destroy()
            tooltip_window = None

    widget.bind("<Enter>", show_tooltip)
    widget.bind("<Leave>", hide_tooltip)


# Funzione per il pulsante esegui movimento nel FRAME1 della GUI
def on_submit(gui_instance):
    packet = []
    for entry in gui_instance.entry_list1:
        try:
            #print(entry.get())
            value = int(entry.get())
            packet.append(value)
        except Exception as e:
            messagebox.showerror("Error", "Enter valid numeric values in all boxes")
            print("ERRORE",e)
            return
    
    if open_serial_port() is False:
        messagebox.showerror("Error", "Error while opening serial port")
        return
    # Comunicazione ad arduino dei valori
    # Mapping: thumb big - thumb little - index - middle - ring&pinky - forearm
    tool = Toolbox()
    fingers_data_mapped = tool.mapping(packet[0],packet[1],packet[2],packet[3],packet[4],packet[5])
    # Send values to arduino
    global arduino
    arduino.write(bytearray(fingers_data_mapped))


# Funzione per il salvataggio dei movimenti lineari in frame2
def on_save_linear(gui_instance,init_list,end_list,time_init,time_end,deltaT):
       
    # Il .get() si usa qui perchè sono delle entry che vengono passate. Se venisse usato a monte nella gui, i campi
    # sarebbero vuoti perchè non viene atteso il click del pulsante
    # Controlli (il controllo che siano numeri in un certo range viene fatto direttamente sui campi con altre funzioni)
    for i in range(len(init_list)):
        if init_list[i].get() == '' and  end_list[i].get() != '':
            messagebox.showerror("Error", "Fill in all or none of the fields for a servo motor")
            return      
        if init_list[i].get() != '' and  end_list[i].get() == '':  
            messagebox.showerror("Error", "Fill in all or none of the fields for a servo motor")
            return  
    
    # Controlli su istante iniziale e finale 
    if time_init.get() == '' or time_init.get() is None:
        messagebox.showerror("Error", "Insert an initial time")
        return
    if time_end.get() == '' or time_end.get() is None:
        messagebox.showerror("Error", "Insert a final time")
        return
    if(int(time_init.get()) >= int(time_end.get())):
        messagebox.showerror("Error", "Insert an initial time smaller than the final time")
        return
    
    init_list_unpacked = []
    end_list_unpacked = []
    for item in init_list:
        if item.get() == '':
            init_list_unpacked.append("NaN")
        else:  
            init_list_unpacked.append(item.get())
    init_list_unpacked.append(time_init.get())
            
    for item in end_list:
        if item.get() == '':
            end_list_unpacked.append("NaN")
        else:  
            end_list_unpacked.append(item.get())
    end_list_unpacked.append(time_end.get())

    dT = ""
    if deltaT.get() == '':
        dT = "70"
    else:
        dT = deltaT.get()
    
    #salvataggio nel json
    data = {
        "type": "linear",
        "values": [init_list_unpacked,end_list_unpacked,dT]
    }
    save_movement(data)
        
# Function to execute a saved movement
def execute_movement(mov):
    
    movement = None
    flag = False
    if isinstance(mov, dict):
        if mov['type'] == 'linear':
            d = LinearMovement(item=mov)
            movement, flag = d.discretize()
        
        if mov['type'] == 'sinusoidal':
            d = SinusoidalMovement(item=mov)
            movement, flag = d.discretize()
    else:
        d = ComplexMovement(item=mov)
        movement, flag = d.discretize()

    if flag is True:
        messagebox.showinfo("Info", "There are values ​​that exceed the range 0-100. A cut has been made")

    global start_time
    start_time = time.time()
    if open_serial_port() == False: #opening serial port
        messagebox.showerror("Error", "Error while opening the serial port")
        return
    
    for packet in range(len(movement)):
        # Comunicazione ad arduino dei valori
        # Mapping: thumb big - thumb little - index - middle - ring&pinky - forearm
        val = movement[packet][6]/1000
        while val > (time.time() - start_time):
            continue
        
        if packet < len(movement)-1:
            val = movement[packet+1][6]/1000
            if(val < (time.time() - start_time)):
                continue
        
        tool = Toolbox()
        fingers_data_mapped = tool.mapping(movement[packet][0],movement[packet][1],movement[packet][2],movement[packet][3],movement[packet][4],movement[packet][5])
        global arduino
        arduino.write(bytearray(fingers_data_mapped))       
        
          
#funzione per visualizzare un movimento in frame3
def visualize_movement(gui_instance,movement):

    result = None
    if isinstance(movement, dict):
        if movement['type'] == 'linear':
            d = LinearMovement(item=movement)
            result, flag = d.discretize()
        
        if movement['type'] == 'sinusoidal':
            d = SinusoidalMovement(item=movement)
            result, flag = d.discretize()
    else:
        d = ComplexMovement(item=movement)
        result, flag = d.discretize()

    # Creazione della finestra di input
    input_window = tk.Toplevel(gui_instance)
    input_window.title("Movement")
    input_window.geometry("700x800")
    input_window.pack_propagate(False)  # Per evitare che la finestra si ridimensioni in base al contenuto
    
    # Table (in input_window)
    headers = ["Thumb(B)", "Thumb(L)","Index","Middle","Ring/Pinky","Forearm","Time instant (ms)"]
    table = Toolbox.create_table(input_window, headers, result)
    table.pack(expand=True, fill="both")
    
    # Frame 2 (contiene checkbox+plot)
    frame2 = tk.Frame(input_window)
    frame2.pack(side="top", expand=True, fill="both", padx=1, pady=1)
    frame2.pack_propagate(True) 
    Toolbox.create_plot(frame2,result)
    
    if flag is True:
        messagebox.showinfo("Info", "There are values ​​that exceed the range 0-100. A cut has been made")

    
# import json
def import_json():
    # Open dialog box to select multiple JSON files
    file_paths = filedialog.askopenfilenames(filetypes=[("JSON files", "*.json")])
    if file_paths:
        try:
            global tree_view
            tree_view.clear()
            for file_path in file_paths:
                file_name = os.path.basename(file_path)
                with open(file_path, 'r', encoding='utf-8') as file:
                    data = json.load(file)
                    tree_view.append([file_name,data])
            return True
        except Exception as e:
            print(f"Error importing json: {e}")
    
    # At this point the window to select the files to be imported
    # has been opened and closed without doing anything
    return False
    
# Funzione per il salvataggio dei movimenti sinsuoidal in frame4
def on_save_sinusoidal(gui_instance,startTime,endTime,entries,deltaT):
    #entry_11 = entries[(row, column)].get() #access 
    
    #check empty values
    for row in range(0, 6):
        if entries[(row, 1)].get() == '' and entries[(row, 2)].get() == '' and entries[(row, 3)].get() == '' and entries[(row, 4)].get() == '' :
            continue
        elif entries[(row, 1)].get() != '' and entries[(row, 2)].get() != '' and entries[(row, 3)].get() != '' and entries[(row, 4)].get() != '' :
            continue
        else:
            messagebox.showerror("Error", "Fill all fields correctly. Fill in all or none of the fields for a servo motor")
            return 

            
    #check other values (start and end time)
    if startTime.get() == '' or startTime.get() is None:
        messagebox.showerror("Error", "Fill start time field")
        return
    
    if endTime.get() == '' or endTime.get() is None:
        messagebox.showerror("Error", "Fill end time field")
        return
    
    if(int(startTime.get()) >= int(endTime.get())):
        messagebox.showerror("Error", "Insert an initial time smaller than the final time")
        return
    
    dT = ""
    if deltaT.get() == '':
        dT = "70"
    else:
        dT = deltaT.get()
     
    # Struttura di salvataggio : 6 liste -> thumbB, thumbL, index, middle, ring/pinky, forearm 
    # al cui interno hanno 4 valori ognuno -> startTime, endTime, amplitude, freq., phase, y inizio, deltaT
    values = [[],[],[],[],[],[]]
    for row in range(0, 6):
        for column in range(1, 5):
            if entries[(row, column)].get() == '':
                values[(row)].append("NaN") # startTime, endTime, amplitude, freq, y_init are 0 if the entry is emptys
            else:
                values[(row)].append(entries[(row, column)].get())
    data = {
        "type": "sinusoidal",
        "values": [startTime.get(),endTime.get(),values[0],values[1],values[2],values[3],values[4],values[5],dT]
    } 
    save_movement(data) 

# Funzione per il salvataggio dei movimenti complessi in frame3
# Attenzione all'ordine di salvataggio nel json
def on_save_complex(itemsInput):
    items = list(itemsInput)
    if not items:
        messagebox.showerror("Error", "Import at least one movement")
        return False

    data = {
        "type": "complex",
        "values": []
    }

    id_visited = []
    def recursive_save(data, items, root):    
        nonlocal id_visited      

        level = 0 
        for element in items:
            if element["index"] == level and element["root"] == root and element["id"] not in id_visited:
                if element["type"] == "linear":
                    data["values"].append({
                        "type": "linear",
                        "values": element["values"]
                    })
                    level += 1
                    id_visited.append(element["id"])

                elif element["type"] == "sinusoidal":
                    data["values"].append({
                        "type": "sinusoidal",
                        "values": element["values"]
                    })
                    level += 1
                    id_visited.append(element["id"])

                elif element["type"] == "complex":
                    id_father = element["id"]  
                    sub_movements = {"type": "complex", "values": []}
                    res = recursive_save(sub_movements, items, root=id_father)
                    data["values"].append(res)
                    level += 1
                    id_visited.append(element["id"])
                else:
                    print("Error in recursive_save")
        return data
    
    items_copy = copy.deepcopy(items)
    items_copy = Toolbox.sort_and_structure2(items_copy)
    ris = recursive_save(data, items_copy, '')
    id_visited = []
    save_movement(ris)
    return True

# Return children of a complex movement (used in frame3)
def return_children(root, elements):
    # Trova i figli dell'elemento con l'id specificato
    children_ids = [element['id'] for element in elements if element.get('root') == root]
    
    # Ricorsivamente trova gli ID dei figli di ciascun figlio
    for child_id in children_ids:
        children_ids.extend(return_children(child_id, elements))
    
    return children_ids


# ------------------------------- GUI -----------------------------------------------------------------------------------------
class GUI(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Limb control interface")
        self.geometry("750x500")
        #self.resizable(0, 0)

        self.columnconfigure(0, weight=1)  # Prima colonna
        self.columnconfigure(1, weight=1)  # Seconda colonna
        
        # Frame creation
        self.frame1 = tk.Frame(self) #rapid_movement frame
        self.frame2 = tk.Frame(self) #linear movement frame
        self.frame3 = tk.Frame(self) #Complex movement frame
        self.frame4 = tk.Frame(self) #Sinusoidal movement frame 
        
        # Configuration of frame
        self.configure_frame1() # rapid_movement frame
        self.configure_frame2() #linear movement frame
        self.configure_frame3() #Complex movement frame
        self.configure_frame4() #Sinusoidal movement frame 
        
        # Configurazione menù
        self.configure_menu()
        
        # Mostra il primo frame all'avvio
        self.show_frame(self.frame1)

    # *************************************** FRAME 1 CONFIGURATION ***************************************************
    def configure_frame1(self):
        for i in range(8):
            self.frame1.grid_rowconfigure(i, weight=0)
        
        for i in range(3):
            self.frame1.grid_columnconfigure(i, weight=1)
        
        title = tk.Label(self.frame1, text="Rapid movement",font="8")
        title.grid(row=0,column=0,pady=40,sticky="s",columnspan=3)
        validate_cmd = self.frame1.register(on_validate)
        
        # Text1
        label1 = tk.Label(self.frame1, text="Thumb - big servo (0 - 100)%")
        label1.grid(row=1,column=0,sticky="e")
        thumb_big = tk.Entry(self.frame1, fg='black',validate="key", 
                             validatecommand=(validate_cmd, "%d", "%i", "%P", "%s", "%S", "%v", "%V", "%W"))
        thumb_big.configure(justify=tk.CENTER) 
        thumb_big.grid(row=1,column=1)
        
        # Text2
        label2 = tk.Label(self.frame1, text="Thumb - little servo (0 - 100)%")
        label2.grid(row=2,column=0,sticky="e")
        thumb_little = tk.Entry(self.frame1, fg='black',validate="key", 
                                validatecommand=(validate_cmd, "%d", "%i", "%P", "%s", "%S", "%v", "%V", "%W"))
        thumb_little.configure(justify=tk.CENTER) 
        thumb_little.grid(row=2,column=1,pady=5)

        # Text3
        label3 = tk.Label(self.frame1, text="Index finger (0 - 100)%")
        label3.grid(row=3,column=0,sticky="e")
        index_finger = tk.Entry(self.frame1, fg='black',validate="key", validatecommand=(validate_cmd, "%d", "%i", "%P", "%s", "%S", "%v", "%V", "%W"))
        index_finger.configure(justify=tk.CENTER) 
        index_finger.grid(row=3,column=1,pady=5)
        
        # Text4
        label4 = tk.Label(self.frame1, text="Middle finger (0 - 100)%")
        label4.grid(row=4,column=0,sticky="e")
        middle_finger = tk.Entry(self.frame1, fg='black',validate="key", 
                                 validatecommand=(validate_cmd, "%d", "%i", "%P", "%s", "%S", "%v", "%V", "%W"))
        middle_finger.configure(justify=tk.CENTER) 
        middle_finger.grid(row=4,column=1,pady=5)
        # Text5
        label5 = tk.Label(self.frame1, text="Ring and Pinky (0 - 100)%")
        label5.grid(row=5,column=0,sticky="e")
        ring_pinky = tk.Entry(self.frame1, fg='black',validate="key", 
                              validatecommand=(validate_cmd, "%d", "%i", "%P", "%s", "%S", "%v", "%V", "%W"))
        ring_pinky.configure(justify=tk.CENTER) 
        ring_pinky.grid(row=5,column=1,pady=5)
        
        # Text6
        label6 = tk.Label(self.frame1, text="Forearm (0 - 100)%")
        label6.grid(row=6,column=0,sticky="e")
        forearm = tk.Entry(self.frame1, fg='black',validate="key", 
                           validatecommand=(validate_cmd, "%d", "%i", "%P", "%s", "%S", "%v", "%V", "%W")) 
        forearm.configure(justify=tk.CENTER) 
        forearm.grid(row=6,column=1,pady=5)
        
        #Valori dei campi innestati nell'istanza self
        self.entry_list1 = [thumb_big, thumb_little, index_finger, middle_finger, ring_pinky,forearm]
        
        # Button
        button1 = tk.Button(self.frame1, text="Execute", height=1, width=10, font= 10, command=lambda: on_submit(self))
        button1.grid(row=7,column=0,pady=20,columnspan=3)

        info_icon = tk.Label(self.frame1, text="ℹ️", font=("Arial", 24))  
        info_icon.grid(row=0,column=1,pady=20,columnspan=3)
        create_tooltip(info_icon, "This section allows you to immediately assign and execute immediately a unique value for each servomotor")
        
        

    # ***************************** FRAME 2 - LINEAR MOVEMENT -CONFIGURATION *************************************************
    def configure_frame2(self):

        # Funzione per mostrare il placeholder
        def show_placeholder(entry, placeholder):
            if entry.get() == '':
                entry.insert(0, placeholder)
                entry.config(fg='grey')

        # Funzione per rimuovere il placeholder quando l'utente inizia a scrivere
        def remove_placeholder(event, entry, placeholder):
            if entry.get() == placeholder:
                entry.delete(0, tk.END)
                entry.config(fg='black')

        # Funzione per reinserire il placeholder se l'entry è vuota
        def check_placeholder(event, entry, placeholder):
            if entry.get() == '':
                show_placeholder(entry, placeholder)

        placeholder_text = "Default=50(NaN)"

        for i in range(12):
            self.frame2.grid_rowconfigure(i, weight=0)
        
        for i in range(4):
            self.frame2.grid_columnconfigure(i, weight=1)
        
        title = tk.Label(self.frame2, text="Linear movement",font="8")
        title.grid(row=0,column=0,pady=40,sticky="s",columnspan=4)
        validate_cmd = self.frame2.register(on_validate) #validation for values entries
        validate_cmd2 = self.frame2.register(on_validate2) #validation for time entries 
        
        label_start = tk.Label(self.frame2, text="Start position")
        label_start.grid(row=1,column=1,sticky='nsew')
        
        label_end = tk.Label(self.frame2, text="End position")
        label_end.grid(row=1,column=2,sticky='nsew')
        
        # *********** POLLICE - grande ***************************
        # Etichetta 
        label1 = tk.Label(self.frame2, text="Thumb - big servo (0 - 100)%")
        label1.grid(row=2,column=0,sticky='e')
        
        # entry - init position
        thumb_big_init = tk.Entry(self.frame2, fg='black',validate="key",
                             validatecommand=(validate_cmd, "%d", "%i", "%P", "%s", "%S", "%v", "%V", "%W"))

        thumb_big_init.configure(justify=tk.CENTER) 
        thumb_big_init.grid(row=2,column=1,padx=5)
        
        # entry - end position
        thumb_big_end = tk.Entry(self.frame2, fg='black',validate="key",
                             validatecommand=(validate_cmd, "%d", "%i", "%P", "%s", "%S", "%v", "%V", "%W"))
        thumb_big_end.configure(justify=tk.CENTER) 
        thumb_big_end.grid(row=2,column=2)
        
        
        # *********** POLLICE - piccolo ***************************
        label2 = tk.Label(self.frame2, text="Thumb - little servo (0 - 100)%")
        label2.grid(row=3,column=0,sticky='e')
        
        # entry - init position
        thumb_little_init = tk.Entry(self.frame2, fg='black',validate="key", 
                             validatecommand=(validate_cmd, "%d", "%i", "%P", "%s", "%S", "%v", "%V", "%W"))
        thumb_little_init.configure(justify=tk.CENTER) 
        thumb_little_init.grid(row=3,column=1,padx=5)
        
        # entry - end position
        thumb_little_end = tk.Entry(self.frame2, fg='black',validate="key", 
                             validatecommand=(validate_cmd, "%d", "%i", "%P", "%s", "%S", "%v", "%V", "%W"))
        thumb_little_end.configure(justify=tk.CENTER) 
        thumb_little_end.grid(row=3,column=2)

        
        # *********** INDICE ***************************
        label3 = tk.Label(self.frame2, text="Index (0 - 100)%")
        label3.grid(row=4,column=0,sticky='e')
        
        # entry - init position
        index_init = tk.Entry(self.frame2, fg='black',validate="key", 
                             validatecommand=(validate_cmd, "%d", "%i", "%P", "%s", "%S", "%v", "%V", "%W"))
        index_init.configure(justify=tk.CENTER) 
        index_init.grid(row=4,column=1,padx=5)
        
        # entry - end position
        index_end = tk.Entry(self.frame2, fg='black',validate="key", 
                             validatecommand=(validate_cmd, "%d", "%i", "%P", "%s", "%S", "%v", "%V", "%W"))
        index_end.configure(justify=tk.CENTER) 
        index_end.grid(row=4,column=2)
        
        
        # *********** MEDIO ***************************
        label4 = tk.Label(self.frame2, text="Middle (0 - 100)%")
        label4.grid(row=5,column=0,sticky='e')
        
        # entry - init position
        middle_init = tk.Entry(self.frame2, fg='black',validate="key", 
                             validatecommand=(validate_cmd, "%d", "%i", "%P", "%s", "%S", "%v", "%V", "%W"))
        middle_init.configure(justify=tk.CENTER) 
        middle_init.grid(row=5,column=1,padx=5)
        
        # entry - end position
        middle_end = tk.Entry(self.frame2, fg='black',validate="key", 
                             validatecommand=(validate_cmd, "%d", "%i", "%P", "%s", "%S", "%v", "%V", "%W"))
        middle_end.configure(justify=tk.CENTER) 
        middle_end.grid(row=5,column=2)
        
        
        # *********** ANULARE-MIGNOLO ***************************
        label5 = tk.Label(self.frame2, text="Ring-Pinky (0 - 100)%")
        label5.grid(row=6,column=0,sticky='e')
        
        # entry - init position
        ring_pinky_init = tk.Entry(self.frame2, fg='black',validate="key", 
                             validatecommand=(validate_cmd, "%d", "%i", "%P", "%s", "%S", "%v", "%V", "%W"))
        ring_pinky_init.configure(justify=tk.CENTER) 
        ring_pinky_init.grid(row=6,column=1,padx=5)
        
        # entry - end position
        ring_pinky_end = tk.Entry(self.frame2, fg='black',validate="key", 
                             validatecommand=(validate_cmd, "%d", "%i", "%P", "%s", "%S", "%v", "%V", "%W"))
        ring_pinky_end.configure(justify=tk.CENTER) 
        ring_pinky_end.grid(row=6,column=2)
        
        
        # *********** AVAMBRACCIO ***************************
        label6 = tk.Label(self.frame2, text="Forearm (0 - 100)%")
        label6.grid(row=7,column=0,sticky='e')
        
        # entry - init position
        forearm_init = tk.Entry(self.frame2, fg='black',validate="key", 
                             validatecommand=(validate_cmd, "%d", "%i", "%P", "%s", "%S", "%v", "%V", "%W"))
        forearm_init.configure(justify=tk.CENTER) 
        forearm_init.grid(row=7,column=1,padx=5)
        
        # entry - end position
        forearm_end = tk.Entry(self.frame2, fg='black',validate="key", 
                             validatecommand=(validate_cmd, "%d", "%i", "%P", "%s", "%S", "%v", "%V", "%W"))
        forearm_end.configure(justify=tk.CENTER) 
        forearm_end.grid(row=7,column=2)
        
        
        # *********** TEMPO ***************************
        label_start_time = tk.Label(self.frame2, text="Start time")
        label_start_time.grid(row=8,column=1,sticky='nsew',pady=10)
        
        label_end_time = tk.Label(self.frame2, text="End time")
        label_end_time.grid(row=8,column=2,sticky='nsew',pady=10)
        
        
        label7 = tk.Label(self.frame2, text="Time (milliseconds)")
        label7.grid(row=9,column=0,sticky='e')
        
        # entry - init time
        time_init = tk.Entry(self.frame2, fg='black',validate="key", 
                             validatecommand=(validate_cmd2, "%d", "%i", "%P", "%s", "%S", "%v", "%V", "%W"))
        time_init.configure(justify=tk.CENTER) 
        time_init.grid(row=9,column=1,padx=5)
        
        # entry - end time
        time_end = tk.Entry(self.frame2, fg='black',validate="key", 
                             validatecommand=(validate_cmd2, "%d", "%i", "%P", "%s", "%S", "%v", "%V", "%W"))
        time_end.configure(justify=tk.CENTER) 
        time_end.grid(row=9,column=2)
        
        # *********** DELTA T ***************************
        label8 = tk.Label(self.frame2, text="DeltaT (milliseconds) - default 70")
        label8.grid(row=10,column=0,sticky='e',pady=10)
        
        # entry - init time
        deltaT = tk.Entry(self.frame2, fg='black',validate="key", 
                             validatecommand=(validate_cmd2, "%d", "%i", "%P", "%s", "%S", "%v", "%V", "%W"))
        deltaT.configure(justify=tk.CENTER) 
        deltaT.grid(row=10,column=1,padx=5)
        
        #array dei valori di partenza
        init_list = [thumb_big_init,thumb_little_init,index_init,middle_init,
                     ring_pinky_init,forearm_init]
        
        #array dei valori fine
        end_list = [thumb_big_end,thumb_little_end,index_end,middle_end,
                    ring_pinky_end,forearm_end]
        
        # Button
        button1 = tk.Button(self.frame2, text="Save", height=1, width=10, font= 2,
                            command=lambda: on_save_linear(self,init_list,end_list,time_init,time_end,deltaT))
        button1.grid(row=11,column=0,pady=20,columnspan=4)

        info_icon = tk.Label(self.frame2, text="ℹ️", font=("Arial", 24))
        info_icon.grid(row=0,column=1,pady=20,columnspan=4)
        create_tooltip(info_icon, "This section allows you to save in json format a linear movement in your file system")

        
        
        
    # *************************************** FRAME 3 CONFIGURATION - Create complex movement*******************************************
    def configure_frame3(self):
        # elements_in_tree_view -> contiene gli elementi "base" della tree_view in modo sequenziale (non innestato) assieme
        # ad alcune info.
        # Alla selezione di un elemento, mi viene dunque restituito l'id dell'elemento selezionato. 
        
        # Viene fatta
        # una ricerca dentro questa lista che contiene dizionari che contiene varie info su ogni elemento del tree quali id,
        # indice, valori, tipo di movimento
        # p.s. Modificare un movimento complesso equivale a modificare singolarmente i suoi sub-elementi
        elements_in_tree_view = []
        
        #item attualmente selezionato
        selected_item_tree_view = None
        
        #id item selected
        id_item = None
        
        
        for i in range(12):
            self.frame3.grid_rowconfigure(i, weight=1)
        
        for i in range(5):
            self.frame3.grid_columnconfigure(i, weight=1)
            
        # Title
        title = ttk.Label(self.frame3, text="Create complex movements", font="8")
        title.grid(row=0,column=0,pady=20,columnspan=5)
        
        # Frame per Treeview scrollabile
        treeview_frame = tk.Frame(self.frame3)
        treeview_frame.grid(row=2, column=1, columnspan=4, rowspan=10, sticky='nsew',pady=15,padx=15)

        # Scrollbar
        scrollbar = ttk.Scrollbar(treeview_frame, orient='vertical')
        scrollbar.pack(side='right', fill='y')

        # Treeview***********
        tree = ttk.Treeview(treeview_frame, yscrollcommand=scrollbar.set)
        tree.pack(expand=True, fill='both')
        scrollbar.config(command=tree.yview)
        
        # *********** innner functions per editare un movimento, viene richiamata in modify ***********************************
        def modify_window(movement_type):
            if movement_type == "linear":
                nonlocal selected_item_tree_view
                new_window = tk.Toplevel(self)
                new_window.geometry("750x500")
                new_window.title("Modify linear movement")
                for i in range(12):
                    new_window.grid_rowconfigure(i, weight=0)

                for i in range(4):
                    new_window.grid_columnconfigure(i, weight=1)
    
                title = tk.Label(new_window, text="Linear movement",font="8")
                title.grid(row=0,column=0,pady=40,sticky="s",columnspan=4)
                validate_cmd = new_window.register(on_validate) #validation for values entries
                validate_cmd2 = new_window.register(on_validate2) #validation for time entries 

                label_start = tk.Label(new_window, text="Start position")
                label_start.grid(row=1,column=1,sticky='nsew')

                label_end = tk.Label(new_window, text="End position")
                label_end.grid(row=1,column=2,sticky='nsew')

                # *********** POLLICE - grande **********************************************
                # Etichetta 
                label1 = tk.Label(new_window, text="Thumb - big servo")
                label1.grid(row=2,column=0,sticky='e')

                # entry - init position
                thumb_big_init = tk.Entry(new_window, fg='black',validate="key",)
                a = selected_item_tree_view["values"][0][0]
                if a == "NaN":
                    a = ''
                thumb_big_init.insert(0, a)
                thumb_big_init.config(validatecommand=(validate_cmd, "%d", "%i", "%P", "%s", "%S", "%v", "%V", "%W"))
                thumb_big_init.configure(justify=tk.CENTER) 
                thumb_big_init.grid(row=2,column=1,padx=5) 

                # entry - end position
                thumb_big_end = tk.Entry(new_window, fg='black',validate="key")
                a = selected_item_tree_view["values"][1][0]
                if a == "NaN":
                    a = ''                
                thumb_big_end.insert(0, a)
                thumb_big_end.config(validatecommand=(validate_cmd, "%d", "%i", "%P", "%s", "%S", "%v", "%V", "%W"))
                thumb_big_end.configure(justify=tk.CENTER) 
                thumb_big_end.grid(row=2,column=2)


                # *********** POLLICE - piccolo ************************************************
                label2 = tk.Label(new_window, text="Thumb - little servo")
                label2.grid(row=3,column=0,sticky='e')

                # entry - init position
                thumb_little_init = tk.Entry(new_window, fg='black',validate="key")
                a = selected_item_tree_view["values"][0][1]
                if a == "NaN":
                    a = ''                
                thumb_little_init.insert(0, a)
                thumb_little_init.config(validatecommand=(validate_cmd, "%d", "%i", "%P", "%s", "%S", "%v", "%V", "%W"))
                
                thumb_little_init.configure(justify=tk.CENTER) 
                thumb_little_init.grid(row=3,column=1,padx=5)

                # entry - end position
                thumb_little_end = tk.Entry(new_window, fg='black',validate="key")
                a = selected_item_tree_view["values"][1][1]
                if a == "NaN":
                    a = ''                
                thumb_little_end.insert(0, a)
                thumb_little_end.config(validatecommand=(validate_cmd, "%d", "%i", "%P", "%s", "%S", "%v", "%V", "%W"))
                thumb_little_end.configure(justify=tk.CENTER) 
                thumb_little_end.grid(row=3,column=1,padx=5)
                thumb_little_end.configure(justify=tk.CENTER) 
                thumb_little_end.grid(row=3,column=2)


                # *********** INDICE ***************************
                label3 = tk.Label(new_window, text="Index")
                label3.grid(row=4,column=0,sticky='e')

                # entry - init position
                index_init = tk.Entry(new_window, fg='black',validate="key")
                a = selected_item_tree_view["values"][0][2]
                if a == "NaN":
                    a = ''                
                index_init.insert(0, a)
                index_init.config(validatecommand=(validate_cmd, "%d", "%i", "%P", "%s", "%S", "%v", "%V", "%W"))
                index_init.configure(justify=tk.CENTER) 
                index_init.grid(row=4,column=1,padx=5)

                # entry - end position
                index_end = tk.Entry(new_window, fg='black',validate="key")
                a = selected_item_tree_view["values"][1][2]
                if a == "NaN":
                    a = ''                
                index_end.insert(0, a)
                index_end.config(validatecommand=(validate_cmd, "%d", "%i", "%P", "%s", "%S", "%v", "%V", "%W"))
                index_end.configure(justify=tk.CENTER) 
                index_end.grid(row=4,column=2)


                # *********** MEDIO ***************************
                label4 = tk.Label(new_window, text="Middle")
                label4.grid(row=5,column=0,sticky='e')

                # entry - init position
                middle_init = tk.Entry(new_window, fg='black',validate="key")
                a = selected_item_tree_view["values"][0][3]
                if a == "NaN":
                    a = ''                
                middle_init.insert(0, a)
                middle_init.config(validatecommand=(validate_cmd, "%d", "%i", "%P", "%s", "%S", "%v", "%V", "%W"))
                middle_init.configure(justify=tk.CENTER) 
                middle_init.grid(row=5,column=1,padx=5)

                # entry - end position
                middle_end = tk.Entry(new_window, fg='black',validate="key")
                a = selected_item_tree_view["values"][1][3]
                if a == "NaN":
                    a = ''                
                middle_end.insert(0, a)
                middle_end.config(validatecommand=(validate_cmd, "%d", "%i", "%P", "%s", "%S", "%v", "%V", "%W"))
                middle_end.configure(justify=tk.CENTER) 
                middle_end.grid(row=5,column=2)


                # *********** ANULARE-MIGNOLO ***************************
                label5 = tk.Label(new_window, text="Ring-Pinky")
                label5.grid(row=6,column=0,sticky='e')

                # entry - init position
                ring_pinky_init = tk.Entry(new_window, fg='black',validate="key")
                a = selected_item_tree_view["values"][0][4]
                if a == "NaN":
                    a = ''                
                ring_pinky_init.insert(0, a)
                ring_pinky_init.config(validatecommand=(validate_cmd, "%d", "%i", "%P", "%s", "%S", "%v", "%V", "%W"))
                ring_pinky_init.configure(justify=tk.CENTER) 
                ring_pinky_init.grid(row=6,column=1,padx=5)

                # entry - end position
                ring_pinky_end = tk.Entry(new_window, fg='black',validate="key")
                a = selected_item_tree_view["values"][1][4]
                if a == "NaN":
                    a = ''                
                ring_pinky_end.insert(0, a)
                ring_pinky_end.config(validatecommand=(validate_cmd, "%d", "%i", "%P", "%s", "%S", "%v", "%V", "%W"))
                ring_pinky_end.configure(justify=tk.CENTER) 
                ring_pinky_end.grid(row=6,column=2)
                
                # *********** AVAMBRACCIO ***************************
                label6 = tk.Label(new_window, text="Forearm")
                label6.grid(row=7,column=0,sticky='e')

                # entry - init position
                forearm_init = tk.Entry(new_window, fg='black',validate="key")
                a = selected_item_tree_view["values"][0][5]
                if a == "NaN":
                    a = ''                
                forearm_init.insert(0, a)
                forearm_init.config(validatecommand=(validate_cmd, "%d", "%i", "%P", "%s", "%S", "%v", "%V", "%W"))
                forearm_init.configure(justify=tk.CENTER) 
                forearm_init.grid(row=7,column=1,padx=5)

                # entry - end position
                forearm_end = tk.Entry(new_window, fg='black',validate="key")
                a = selected_item_tree_view["values"][1][5]
                if a == "NaN":
                    a = ''                
                forearm_end.insert(0, a)
                forearm_end.config(validatecommand=(validate_cmd, "%d", "%i", "%P", "%s", "%S", "%v", "%V", "%W"))
                forearm_end.configure(justify=tk.CENTER) 
                forearm_end.grid(row=7,column=2)


                # *********** TEMPO ***************************
                label_start_time = tk.Label(new_window, text="Start time (millis)")
                label_start_time.grid(row=8,column=1,sticky='nsew',pady=10)

                label_end_time = tk.Label(new_window, text="End time (millis)")
                label_end_time.grid(row=8,column=2,sticky='nsew',pady=10)


                label7 = tk.Label(new_window, text="Time")
                label7.grid(row=9,column=0,sticky='e')

                # entry - init time
                time_init = tk.Entry(new_window, fg='black',validate="key")
                a = selected_item_tree_view["values"][0][6]
                time_init.insert(0, a)
                time_init.config(validatecommand=(validate_cmd2, "%d", "%i", "%P", "%s", "%S", "%v", "%V", "%W"))
                time_init.configure(justify=tk.CENTER) 
                time_init.grid(row=9,column=1,padx=5)

                # entry - end time
                time_end = tk.Entry(new_window, fg='black',validate="key")
                a = selected_item_tree_view["values"][1][6]
                time_end.insert(0, a)
                time_end.config(validatecommand=(validate_cmd2, "%d", "%i", "%P", "%s", "%S", "%v", "%V", "%W"))
                time_end.configure(justify=tk.CENTER) 
                time_end.grid(row=9,column=2)

                # *********** DELTA T ***************************
                label8 = tk.Label(new_window, text="DeltaT (default 70ms)")
                label8.grid(row=10,column=0,sticky='e',pady=10)

                # entry delta t
                deltaT = tk.Entry(new_window, fg='black',validate="key")
                a = selected_item_tree_view["values"][2]
                deltaT.insert(0, a)
                deltaT.config(validatecommand=(validate_cmd2, "%d", "%i", "%P", "%s", "%S", "%v", "%V", "%W"))
                deltaT.configure(justify=tk.CENTER) 
                deltaT.grid(row=10,column=1,padx=5)

                # Array dei valori di partenza
                init_list = [thumb_big_init,thumb_little_init,index_init,middle_init,
                             ring_pinky_init,forearm_init]

                #array dei valori fine
                end_list = [thumb_big_end,thumb_little_end,index_end,middle_end,
                            ring_pinky_end,forearm_end]

                # function for saving modified values
                def save_l(init_list,end_list,time_init,time_end,deltaT):

                    #check values on the entries
                    for i in range(len(init_list)):
                        if init_list[i].get() == '' and  end_list[i].get() != '':
                            messagebox.showerror("Error", "Fill in all or none of the fields for a servo motor")
                            return      
                        if init_list[i].get() != '' and  end_list[i].get() == '':  
                            messagebox.showerror("Error", "Fill in all or none of the fields for a servo motor")
                            return  
                
                    # Controlli su istante iniziale e finale 
                    if time_init.get() == '' or time_init.get() is None:
                        messagebox.showerror("Error", "Insert an initial time")
                        return
                    if time_end.get() == '' or time_end.get() is None:
                        messagebox.showerror("Error", "Insert a final time")
                        return
                    if(int(time_init.get()) >= int(time_end.get())):
                        messagebox.showerror("Error", "Insert an initial time smaller than the final time")
                        return
                    
                    #using .get() over the input fields for get the values
                    init_list_unpacked = []
                    end_list_unpacked = []
                    for item in init_list:
                        if item.get() == '':
                            init_list_unpacked.append("NaN")
                        else:  
                            init_list_unpacked.append(item.get())
                    init_list_unpacked.append(time_init.get())
                            
                    for item in end_list:
                        if item.get() == '':
                            end_list_unpacked.append("NaN")
                        else:  
                            end_list_unpacked.append(item.get())
                    end_list_unpacked.append(time_end.get())

                    nonlocal elements_in_tree_view
                    nonlocal selected_item_tree_view
                    nonlocal new_window
                    for element in elements_in_tree_view:
                        if element["id"] == selected_item_tree_view["id"]:
                            element["values"][0] = init_list_unpacked
                            element["values"][1] = end_list_unpacked
                            dT = ""
                            if deltaT.get() == '':
                                dT = "70"
                            else:
                                dT = deltaT.get()
                            element["values"][2] = dT
                            new_window.destroy()
                            return
                    print("ERROR, the selected item does not exists")
                    new_window.destroy()
                    return
                

                # Button in new window for saving changes
                button1 = tk.Button(new_window, text="Save", height=1, width=10, font= 2,command=lambda:save_l(init_list,end_list,time_init,time_end,deltaT))
                button1.grid(row=11,column=0,pady=20,columnspan=4)

            if movement_type == "sinusoidal": #**********************************************
                #nonlocal selected_item_tree_view
                new_window = tk.Toplevel(self)
                new_window.geometry("750x500")
                new_window.title("Modify sinusoidal movement")
                for i in range(13):
                    new_window.grid_rowconfigure(i, weight=0)
                
                for i in range(7):
                    new_window.grid_columnconfigure(i, weight=1)
                    
                #validation functions for entries (only digit)
                validate_entries = new_window.register(on_validate2)
                validate_amp = new_window.register(validate_amp_shift)
                
                title = tk.Label(new_window, text="Sinusoidal movement",font="8")
                title.grid(row=0, column=0, pady=20, padx=2, columnspan=7)
                
                # amplitude, frequency, phase, deltaT, y_init
                
                amplitude_label = tk.Label(new_window, text="Amplitude(0-100)")
                amplitude_label.grid(row=1, column=1)
                
                frequency_label = tk.Label(new_window, text="Frequency(mHz)")
                frequency_label.grid(row=1, column=2)
                
                phase_label = tk.Label(new_window, text="Amp. Shift(-1,1)")
                phase_label.grid(row=1, column=3)
                
                y_init_label = tk.Label(new_window, text="Start value(0-100)")
                y_init_label.grid(row=1, column=4)
                
                # Label a sinistra della griglia per ogni riga
                thumb_B_label = tk.Label(new_window, text= "Thumb(B)")
                thumb_B_label.grid(row=2, column=0, padx=5, pady=5,sticky="e")
                
                thumb_L_label = tk.Label(new_window, text= "Thumb(L)")
                thumb_L_label.grid(row=3, column=0, padx=5, pady=5,sticky="e")
                
                index_label = tk.Label(new_window, text= "Index")
                index_label.grid(row=4, column=0, padx=5, pady=5,sticky="e")
                
                middle_label = tk.Label(new_window, text= "Middle")
                middle_label.grid(row=5, column=0, padx=5, pady=5,sticky="e")
                
                TL_label = tk.Label(new_window, text= "Thumb/Little")
                TL_label.grid(row=6, column=0, padx=5, pady=5,sticky="e")
                
                forearm_label = tk.Label(new_window, text= "Forearm")
                forearm_label.grid(row=7, column=0, padx=5, pady=5,sticky="e")
                
                # Dizionario per memorizzare gli entry
                entries = {}

                # Creazione della griglia 4x4=16 campi di input (a cui vi si accede come fosse una matrice)
                for i in range(2, 8):
                    for j in range(1, 5):
                        #entry = None
                        entry = tk.Entry(new_window, width=15, validate="key")
                        a = selected_item_tree_view["values"][i][j-1] #accesso
                        if a == "NaN":
                            a = ''                        
                        entry.insert(0,a)
                        if j==3:
                            entry.config(validatecommand=(validate_amp, "%P"))
                        else:
                            entry.config(validatecommand=(validate_entries, "%d", "%i", "%P", "%s", "%S", "%v", "%V", "%W"))
                        entry.grid(row=i, column=j, padx=10, pady=5)
                        # Salva l'entry nel dizionario con una chiave unica
                        entries[((i-2), j)] = entry
                
                deltaT_label = tk.Label(new_window, text="deltaT (ms)")
                deltaT_label.grid(row=10, column=1,pady=10,sticky="s")
                
                startTime_label = tk.Label(new_window, text="Start time(ms)")
                startTime_label.grid(row=10, column=2,pady=10,sticky="s")
                
                endTime_label = tk.Label(new_window, text="End time(ms)")
                endTime_label.grid(row=10, column=3,pady=10,sticky="s")
                
                #entry deltaT
                deltaT_entry = tk.Entry(new_window,width=15, validate="key")
                a = selected_item_tree_view["values"][8]
                deltaT_entry.insert(0,a)
                deltaT_entry.config(validatecommand=(validate_entries, "%d", "%i", "%P", "%s", "%S", "%v", "%V", "%W"))
                deltaT_entry.grid(row=11, column=1, padx=5, pady=5)
                
                #entry startTime
                startTime_entry = tk.Entry(new_window,width=15, validate="key")
                a = selected_item_tree_view["values"][0]
                startTime_entry.insert(0,a)
                startTime_entry.config(validatecommand=(validate_entries, "%d", "%i", "%P", "%s", "%S", "%v", "%V", "%W"))
                startTime_entry.grid(row=11, column=2, padx=5, pady=5)
                
                #entry endTime
                endTime_entry = tk.Entry(new_window,width=15, validate="key")
                a = selected_item_tree_view["values"][1]
                endTime_entry.insert(0,a)
                endTime_entry.config(validatecommand=(validate_entries, "%d", "%i", "%P", "%s", "%S", "%v", "%V", "%W"))
                endTime_entry.grid(row=11, column=3, padx=5, pady=5)
                
                # Funzione per la modifica dei movimenti sinsuoidal 
                def save_s(gui_instance,startTime,endTime,entries,deltaT):
                    #entry_11 = entries[(row, column)].get() #access 
                    
                    #check empty values
                    for row in range(0, 6):
                        if entries[(row, 1)].get() == '' and entries[(row, 2)].get() == '' and entries[(row, 3)].get() == '' and entries[(row, 4)].get() == '' :
                            continue
                        elif entries[(row, 1)].get() != '' and entries[(row, 2)].get() != '' and entries[(row, 3)].get() != '' and entries[(row, 4)].get() != '' :
                            continue
                        else:
                            messagebox.showerror("Error", "Fill in all or none of the fields for a servo motor")
                            return  
                    
                    if startTime.get() == '' or startTime.get() is None:
                        messagebox.showerror("Error", "Fill start time field")
                        return
                    
                    if endTime.get() == '' or endTime.get() is None:
                        messagebox.showerror("Error", "Fill end time field")
                        return
                    
                    if(int(startTime.get()) >= int(endTime.get())):
                        messagebox.showerror("Error", "Insert an initial time smaller than the final time")
                        return
                    
                    
                    # struttura di salvataggio : 6 liste -> thumbB, thumbL, index, middle, ring/pinky, forearm 
                    # al cui interno hanno 4 valori ognuno (amplitude, freq, phase, y_inizio) -> startTime, endTime, lista[i], deltaT
                    nonlocal elements_in_tree_view
                    nonlocal selected_item_tree_view
                    nonlocal new_window

                    for element in elements_in_tree_view:
                        if element["id"] == selected_item_tree_view["id"]:
                            for i in range(2, 8):
                                #print(element["values"][i])
                                #print("------")
                                for j in range(0, 4):
                                    if entries[(i-2, j+1)].get() == '':
                                        element["values"][i][j] = "NaN" # startTime, endTime, amplitude, freq, y_init are NaN if the entry is emptys
                                    else:
                                        element["values"][i][j] = entries[(i-2, j+1)].get()

                            element["values"][0] = startTime.get()
                            element["values"][1] = endTime.get()
                            dT = ""
                            if deltaT.get() == '':
                                dT = "70"
                            else:
                                dT = deltaT.get()
                            element["values"][8] = dT
                            new_window.destroy()
                            return
                    print("Error in save_s sinusoidal")
                    return

                # Button in new window for saving changes
                button1 = tk.Button(new_window, text="Save", height=1, width=10, font= 2,
                                command=lambda: save_s(self,startTime_entry,endTime_entry,entries,deltaT_entry))
                button1.grid(row=12,column=0,pady=20, padx=15, columnspan=7)

        
        
        # funzione per modificare i valori di un movimento base
        def modify():
            #print(selected_item_tree_view)
            if selected_item_tree_view is None:
                messagebox.showerror("Error", "Select a movement")
                return 
            if selected_item_tree_view["type"] == "linear":
                modify_window("linear")
                return
                
            if selected_item_tree_view["type"] == "sinusoidal":
                modify_window("sinusoidal")
                return
                
            if selected_item_tree_view["type"] == "complex":
                messagebox.showinfo("Info", "To change the values of a complex movement, act on the basic movements that make it up")
                return
            

        # function for scaling of a movement of 1.5x, 2x or 0.5x
        # value is a float
        def scale(value):

            def scale_linear(value,id_element):
                element_to_work = None
                for e in elements_in_tree_view:
                    if e['id'] == id_element:
                        element_to_work = e
                        break
                #update the selected movement
                init = int(element_to_work["values"][0][6])
                end = int(element_to_work["values"][1][6])
                new_end = (end - init)*value
                #subst. in the new end
                element_to_work["values"][1][6] = init + int(new_end)  

                #update the ram
                for mov in elements_in_tree_view:
                    if mov["id"] == element_to_work["id"]:
                        mov = element_to_work.copy()
                        break                              
                return
            
            def scale_sinusoidal(value,id_element):
                element_to_work = None
                for e in elements_in_tree_view:
                    if e['id'] == id_element:
                        element_to_work = e
                        break
                #update the selected movement
                init = int(element_to_work["values"][0])
                end = int(element_to_work["values"][1])
                new_end = (end - init)*value
                #subst. in the new end
                element_to_work["values"][1] = init + int(new_end)
                
                #modify the frequency
                for i,val in enumerate(element_to_work["values"]):
                    if i>=2 and i<=7:
                        val[1] = str(float(val[1])/value)

                #update the ram
                for mov in elements_in_tree_view:
                    if mov["id"] == element_to_work["id"]:
                        mov = element_to_work.copy()
                        break
                return
                                                  
            if selected_item_tree_view is None:
                messagebox.showerror("Error", "Select a movement")
                return
            
            #check the type of the selected movement
            type = selected_item_tree_view["type"]

            if type == "linear":
                scale_linear(value,selected_item_tree_view['id'])
                messagebox.showinfo("Info", "Updated movement")
                return
            
            if type == "sinusoidal":
                scale_sinusoidal(value,selected_item_tree_view['id'])
                messagebox.showinfo("Info", "Updated movement")
                return

            if type == "complex":
                ids = return_children(selected_item_tree_view["id"], elements_in_tree_view) #only leaves
                #calculation min start e max end
                min_start = 999999
                for submov in elements_in_tree_view:
                    if submov['id'] in ids:
                        #smallest min_start 
                        if submov['type'] == 'sinusoidal':
                            var = int(submov['values'][0])
                            if var <= min_start:
                                min_start = var

                        if submov['type'] == 'linear':
                            var = int(submov['values'][0][-1])
                            if var <= min_start:
                                min_start = var  

                for submov in elements_in_tree_view:
                    if submov['id'] in ids:
                        if submov['type'] == 'sinusoidal':
                            end = int(submov['values'][1])
                            start = int(submov['values'][0])
                            range = end - start
                            new_start = min_start + (start - min_start)*value
                            new_end = new_start + range

                            submov['values'][1] = str(int(new_end))
                            submov['values'][0] = str(int(new_start))
                            scale_sinusoidal(value,submov['id'])

                        if submov['type'] == 'linear':   
                            end = int(submov['values'][1][6])
                            start = int(submov['values'][0][6])
                            range = end - start
                            new_start = min_start + (start - min_start)*value
                            new_end = new_start + range
                            submov['values'][1][6] = str(int(new_end))
                            submov['values'][0][6] = str(int(new_start))    
                            scale_linear(value,submov['id'])                           

                messagebox.showinfo("Info", "Updated complex movement")
                return

        ## function for scaling of a movement of a specific value
        def scale_specific():
            if selected_item_tree_view is None:
                messagebox.showerror("Error", "Select a movement")
                return
            
            def on_click_specific(window_instance,entry):
                input = entry.get()
                if input == "" or input is None:
                    messagebox.showerror("Error", "The entry was empty")
                    window_instance.destroy()
                    return
                else:
                    window_instance.destroy()
                    scale(float(input))
                    return
            
            input_window = tk.Toplevel(self)
            input_window.title("Insert specific value")
            input_window.geometry("300x100")  

            # input entry
            float_validator = input_window.register(validate_float_input)

            entry = tk.Entry(input_window, width=30, validate="key", validatecommand=(float_validator, '%P'))  
            entry.pack(pady=20)  
            button = tk.Button(input_window, text="Submit", width=10, command=lambda: on_click_specific(input_window,entry))
            button.pack(pady=10)

        #flip linear movement
        def flip_linear(item):
            pos_start = item['values'][0][:-1]
            pos_end = item['values'][1][:-1]

            item['values'][0][:-1] = pos_end
            item['values'][1][:-1] = pos_start

            for mov in elements_in_tree_view:
                if mov["id"] == item["id"]:
                    mov = item.copy()
                    break
            return
        

        #Newphase=1-{ [(end_time-start_time)*freq-int((end_time-start_time)*freq)] *2+oldphase}
        #flip sinusoidal movement
        def flip_sinusoidal(item):
            values = item['values']
            t_end = float(values[1])
            t_start = float(values[0])
            for i, val in enumerate(values):
                if i>=2 and i<=7 and (val[1] != "NaN"):

                    frequency = float(val[1])
                    oldphase = float(val[2])
                    new_phase = 1 - (((t_end - t_start)*frequency-int((t_end - t_start)*frequency))*2+oldphase)

                    if new_phase < -1:
                        new_phase = new_phase +2
                    if new_phase > 1:
                        new_phase = new_phase -2
                    val[2] = str(new_phase)
            return   


        def flip_complex(item):
            ids = return_children(item['id'], elements_in_tree_view) #only leaves
            #calculation min start e max end
            min_start = 999999
            max_end = -1
            for submov in elements_in_tree_view:
                if submov['id'] in ids:
                    #smallest min_start 
                    if submov['type'] == 'sinusoidal':
                        var = int(submov['values'][0])
                        if var <= min_start:
                            min_start = var

                    if submov['type'] == 'linear':
                        var = int(submov['values'][0][-1])
                        if var <= min_start:
                            min_start = var         

                    #biggest max_end
                    if submov['type'] == 'sinusoidal':
                        var = int(submov['values'][1])
                        if var >= max_end:
                            max_end = var

                    if submov['type'] == 'linear':
                        var = int(submov['values'][1][-1])
                        if var >= max_end:
                            max_end = var    

            t_center = min_start + ((max_end-min_start)/2)

            for submov in elements_in_tree_view:
                if submov['id'] in ids:
                    if submov['type'] == 'sinusoidal':
                        new_end = (2*t_center)-int(submov['values'][0])
                        new_start = t_center + (t_center - int(submov['values'][1]))
                        submov['values'][0] = str(int(new_start))
                        submov['values'][1] = str(int(new_end))
                        flip_sinusoidal(submov)
      
                    if submov['type'] == 'linear':
                        new_end = (2*t_center)-int(submov['values'][0][6])
                        new_start = t_center + (t_center - int(submov['values'][1][6]))
                        submov['values'][0][6] = str(int(new_start))
                        submov['values'][1][6] = str(int(new_end))
                        flip_linear(submov)
            
        #inverte i valori del movimento
        def flip(selected_item):
            if selected_item is None:
                messagebox.showerror("Error", "Select a movement")
                return
            
            if selected_item['type'] == "linear":
                flip_linear(selected_item)
                messagebox.showinfo("Info", "Updated movement")
                return
            
            if selected_item['type'] == "sinusoidal":
                flip_sinusoidal(selected_item)     
                messagebox.showinfo("Info", "Updated movement")
                return
            
            if selected_item_tree_view['type'] == "complex":
                flip_complex(selected_item)
                messagebox.showinfo("Info", "Updated movement")
                return


            
        #update the indexes (levels) of the elements in treeview (called on import json or click "up" or "down", "delete_item" e "import_json")
        def update_index():
            nonlocal tree
            for item in elements_in_tree_view:
                item['index'] = tree.index(item['id'])
                current_text = tree.item(item['id'], 'text')

                if ")" in current_text:
                    current_text = current_text[3:]
                
                updated_text = str(item['index']) + ") " + current_text
                tree.item(item['id'], text=updated_text)

        
        # Used to see if the json import operation was successful, and then populate the treeview
        def import_json_inner():
            # Recursive reading of the json
            def recursive_reading(father_id, t_w):
                for movement in t_w:
                    if(movement[1]['type'] == 'linear'):  
                        a = " - Type: Linear movement"
                        b = movement[0]
                        c = b + a 
                        id_element = None
                        if father_id is None:
                            id_element = tree.insert("", "end", text=c)
                        else:
                            id_element = tree.insert(father_id, "end", text=c)
                        elements_in_tree_view.append({"id":id_element,"values":(movement[1]['values']),
                                                          "type":"linear","index":None, "root":(tree.parent(id_element))})
                        
                    elif(movement[1]['type'] == 'sinusoidal'):
                        a = " - Type: Sinusoidal movement"
                        b = movement[0]
                        c = b + a
                        id_element = None
                        if father_id is None:
                            id_element = tree.insert("", "end", text=c)
                        else:
                            id_element = tree.insert(father_id, "end", text=c)
                        elements_in_tree_view.append({"id":id_element,"values":(movement[1]['values']),
                                                          "type":"sinusoidal","index":None,"root":(tree.parent(id_element))})
                    
                    elif(movement[1]['type'] == 'complex'):
                        # se il movimento è complesso, faccio una copia di una nuova lista
                        # che popolo con i sotto-movimenti che passo ricorsivamente a 
                        # recursive_reading
                        a = " - Type: Complex movement"
                        b = movement[0]
                        c = b + a
                        id_element = None
                        if father_id is None:
                            id_element = tree.insert("", "end", text=c)
                        else:
                            id_element = tree.insert(father_id, "end", text=c)

                        elements_in_tree_view.append({"id":id_element,"type":"complex","index":None,"root":(tree.parent(id_element))})
                        twc = []
                        for a in (movement[1]['values']):
                            #recursive tree_view reconstruction
                            twc.append([">",a])
                        #recursion
                        recursive_reading(id_element,twc)
                        #father_id = None

            if import_json() is True:
                #tree.delete(*tree.get_children()) #empty the treeview
                #nonlocal elements_in_tree_view
                #elements_in_tree_view.clear() #empty the RAM
                global tree_view
                recursive_reading(None, tree_view)
                update_index() #updating indexes
            else:
                return        
        
        # move a selected element of the treeview up
        def move_up():
            selected_item = tree.selection()
            if selected_item:
                item_id = selected_item[0]
                parent_id = tree.parent(item_id)
                index = tree.index(item_id)
                if index > 0:
                    tree.move(item_id, parent_id, index-1)
                update_index()
                    
        # move a selected element of the treeview down  
        def move_down():
            selected_item = tree.selection()
            if selected_item:
                item_id = selected_item[0]
                parent_id = tree.parent(item_id)
                index = tree.index(item_id)
                children = tree.get_children(parent_id)
                if index < len(children) - 1:
                    tree.move(item_id, parent_id, index+1)
                update_index()
        
        
        # Function called when an element of the treeview is selected
        # it saves selected motion information in selected_item_tree_view
        def on_tree_select(event):
            if len(tree.selection()) == 0:
                #print("tupla vuota in on_tree_select")
                return
            
            nonlocal id_item
            id_item = tree.selection()[0] #id dell'item selezionato
            #elements_in_tree_view è una list di dizionari
            for element in elements_in_tree_view:
                if id_item == element["id"]:
                    nonlocal selected_item_tree_view
                    #selected_item_tree_view.clear()
                    selected_item_tree_view = element.copy()
                    return

        def delete_item_recursive(id_item):
            nonlocal elements_in_tree_view

            # Trova il dizionario con l'id specificato
            dizionario = next((d for d in elements_in_tree_view if d['id'] == id_item), None)
            
            # Se il dizionario non esiste, non facciamo nulla
            if not dizionario:
                return
            
            # Se il dizionario è di tipo 'c', rimuoviamo anche i suoi figli
            if dizionario['type'] == 'complex':
                figli_da_rimuovere = [d['id'] for d in elements_in_tree_view if d.get('root') == id_item]
                
                # Rimozione ricorsiva per ogni figlio
                for figlio_id in figli_da_rimuovere:
                    delete_item_recursive(figlio_id)
            
            # Rimuoviamo il dizionario con l'id specificato
            elements_in_tree_view[:] = [d for d in elements_in_tree_view if d['id'] != id_item]


        #delete an item from treeview 
        def delete_item(idItem):
            if idItem is None:
                messagebox.showerror("Error", "Select a movement to delete")
                return

            nonlocal selected_item_tree_view
            father_id = None
            if selected_item_tree_view['root'] != '' :
                children = return_children(selected_item_tree_view['root'],elements_in_tree_view)
                if len(children) == 1:
                    father_id = selected_item_tree_view['root']
       
            tree.delete(idItem) #delete the element from the treeview
            delete_item_recursive(idItem)
            if father_id is not None:
                delete_item(father_id)
            update_index()
            selected_item_tree_view = None
            nonlocal id_item
            id_item = None
            return
    
        #empty elements_in_tree_view(ram) and tree_view 
        def clear_all():
            nonlocal id_item
            nonlocal elements_in_tree_view   
            nonlocal tree
            id_item = None
            tree.delete(*tree.get_children()) #empty the treeview
            elements_in_tree_view.clear() #empty the RAM
            
        def find_elements(elements, target_id):
            # Trova il dizionario con l'id specificato
            target_dict = next((elem for elem in elements if elem['id'] == target_id), None)
            if target_dict is None:
                return []

            # Inizia la lista con il dizionario trovato
            result = [target_dict]

            # Trova i figli ricorsivamente
            for elem in elements:
                if elem['root'] == target_id:
                    result.extend(find_elements(elements, elem['id']))
            return result

        # Visualize a selected movement in frame3
        def vis_mov(gui_instance,movement):
            if movement is None:
                messagebox.showerror("Error", "Select or import a movement correctly")
                return 
            
            if selected_item_tree_view['type'] == "complex":
                result = find_elements(elements_in_tree_view, selected_item_tree_view['id'])
                visualize_movement(gui_instance,result)
            else:
                visualize_movement(gui_instance, selected_item_tree_view)
            return
        

        def visualize_final_movement(gui_instance,movements):
            if not movements:
                messagebox.showerror("Error", "Import at least one movement")
                return 
            visualize_movement(gui_instance,movements)
            return
        
        def exe_mov(movement):
            if movement is None:
                messagebox.showerror("Error", "Select or import a movement correctly")
                return 
            
            if selected_item_tree_view['type'] == "complex":
                result = find_elements(elements_in_tree_view, selected_item_tree_view['id'])
                execute_movement(result)
            else:
                execute_movement(selected_item_tree_view)
            return

        file_button = ttk.Menubutton(self.frame3, text="Edit")
        file_button.grid(row=1, column=0)
        file_menu = Menu(file_button, tearoff=0)
        file_button['menu'] = file_menu
        file_menu.add_command(label="Import JSON", command=import_json_inner)
        file_menu.add_command(label="Modify", command=modify)
        
        modify_menu = Menu(file_menu, tearoff=0)
        modify_menu.add_command(label="1.5x",command=lambda: scale(1.5))
        modify_menu.add_command(label="2x",command=lambda: scale(2.0))
        modify_menu.add_command(label="0.5x",command=lambda: scale(0.5))
        modify_menu.add_command(label="Specific",command=lambda: scale_specific())
        file_menu.add_cascade(label="Scale", menu=modify_menu)
        
        file_menu.add_command(label="Flip", command=lambda: flip(selected_item_tree_view))
        
        tree.bind("<<TreeviewSelect>>", on_tree_select)
        
        # Buttons
        button_execute = tk.Button(self.frame3, text="Execute",
                                 command=lambda: exe_mov(selected_item_tree_view))
        button_execute.grid(row=1,column=1)
        
        button_visualize = tk.Button(self.frame3, text="Visualize", 
                                     command=lambda: vis_mov(self.frame3, selected_item_tree_view))
        button_visualize.grid(row=1,column=2)
        
        button_delete = tk.Button(self.frame3, text="Delete", command=lambda: delete_item(id_item))
        button_delete.grid(row=1,column=3)

        button_clear_all = tk.Button(self.frame3, text="Clear all", command=lambda: clear_all())
        button_clear_all.grid(row=1,column=4)
        
        button_up = tk.Button(self.frame3, text="Up",command=move_up)
        button_up.grid(row=4,column=0)
        
        button_down = tk.Button(self.frame3, text="Down",command=move_down)
        button_down.grid(row=5,column=0)
        
        button_save = tk.Button(self.frame3, text="Save",command=lambda: on_save_complex(elements_in_tree_view))
        button_save.grid(row=8,column=0)

        button_vis_fin = tk.Button(self.frame3, text="Visualize final movement", 
                                   command=lambda: visualize_final_movement(self.frame3,elements_in_tree_view))
        button_vis_fin.grid(row=9,column=0)

        info_icon = tk.Label(self.frame3, text="ℹ️", font=("Arial", 24))  
        info_icon.grid(row=0, column=0)
        create_tooltip(info_icon, 
            "This section allows you to create and save in JSON format a complex movement " +
            "in your file system, by importing other movements from the filesystem. " +
            "Each movement ‘overwrites’ the previous movement by numbering")




    # *************************************** FRAME 4 - SINUSOIDAL MOVEMENT **********************************************
    def configure_frame4(self):
        
        for i in range(13):
            self.frame4.grid_rowconfigure(i, weight=0)
        
        for i in range(7):
            self.frame4.grid_columnconfigure(i, weight=1)
            
        #validation functions for entries (only digit)
        validate_entries = self.frame4.register(on_validate2)

        validate_amp = self.frame4.register(validate_amp_shift)
        
        title = tk.Label(self.frame4, text="Sinusoidal movement",font="8")
        title.grid(row=0, column=0, pady=20, padx=2, columnspan=7)
        
        # amplitude, frequency, phase, deltaT, y_init
        
        amplitude_label = tk.Label(self.frame4, text="Amplitude (0-100)")
        amplitude_label.grid(row=1, column=1)
        
        frequency_label = tk.Label(self.frame4, text="Frequency (mHz)")
        frequency_label.grid(row=1, column=2)
        
        phase_label = tk.Label(self.frame4, text="Phase (-1,1)")
        phase_label.grid(row=1, column=3)
        
        y_init_label = tk.Label(self.frame4, text="Offset (0-100)")
        y_init_label.grid(row=1, column=4)
        
        # Label a sinistra della griglia per ogni riga
        thumb_B_label = tk.Label(self.frame4, text= "Thumb(B)")
        thumb_B_label.grid(row=2, column=0, padx=5, pady=5,sticky="e")
        
        thumb_L_label = tk.Label(self.frame4, text= "Thumb(L)")
        thumb_L_label.grid(row=3, column=0, padx=5, pady=5,sticky="e")
        
        index_label = tk.Label(self.frame4, text= "Index")
        index_label.grid(row=4, column=0, padx=5, pady=5,sticky="e")
        
        middle_label = tk.Label(self.frame4, text= "Middle")
        middle_label.grid(row=5, column=0, padx=5, pady=5,sticky="e")
        
        TL_label = tk.Label(self.frame4, text= "Ring/Pinky")
        TL_label.grid(row=6, column=0, padx=5, pady=5,sticky="e")
        
        forearm_label = tk.Label(self.frame4, text= "Forearm")
        forearm_label.grid(row=7, column=0, padx=5, pady=5,sticky="e")
        
        # Dizionario per memorizzare gli entry
        entries = {}

        # Creazione della griglia 4x4=16 campi di input (a cui vi si accede come fosse una matrice)
        for i in range(2, 8):
            for j in range(1, 5):
                if j == 3:
                    entry = tk.Entry(self.frame4, width=15, validate="key",
                                 validatecommand=(validate_amp, '%P'))
                else:
                    entry = tk.Entry(self.frame4, width=15, validate="key",
                                    validatecommand=(validate_entries, "%d", "%i", "%P", "%s", "%S", "%v", "%V", "%W"))
                entry.grid(row=i, column=j, padx=10, pady=5)
                # Salva l'entry nel dizionario con una chiave unica
                entries[((i-2), j)] = entry
            
        
        deltaT_label = tk.Label(self.frame4, text="DeltaT(ms) - default 70")
        deltaT_label.grid(row=10, column=1,pady=10,sticky="s")
        
        startTime_label = tk.Label(self.frame4, text="Start time(ms)")
        startTime_label.grid(row=10, column=2,pady=10,sticky="s")
        
        endTime_label = tk.Label(self.frame4, text="End time(ms)")
        endTime_label.grid(row=10, column=3,pady=10,sticky="s")
        
        #entry deltaT
        deltaT_entry = tk.Entry(self.frame4,width=15, validate="key",
                               validatecommand=(validate_entries, "%d", "%i", "%P", "%s", "%S", "%v", "%V", "%W"))
        deltaT_entry.grid(row=11, column=1, padx=5, pady=5)
        
        #entry startTime
        startTime_entry = tk.Entry(self.frame4,width=15, validate="key",
                                  validatecommand=(validate_entries, "%d", "%i", "%P", "%s", "%S", "%v", "%V", "%W"))
        startTime_entry.grid(row=11, column=2, padx=5, pady=5)
        
        #entry endTime
        endTime_entry = tk.Entry(self.frame4,width=15, validate="key",
                                validatecommand=(validate_entries, "%d", "%i", "%P", "%s", "%S", "%v", "%V", "%W"))
        endTime_entry.grid(row=11, column=3, padx=5, pady=5)
        
        # Button
        button1 = tk.Button(self.frame4, text="Save", height=1, width=10, font= 2,
                           command=lambda: on_save_sinusoidal(self,startTime_entry,endTime_entry,entries,deltaT_entry))
        button1.grid(row=12,column=0,pady=20, padx=15, columnspan=7)

        info_icon = tk.Label(self.frame4, text="ℹ️", font=("Arial", 24))  
        info_icon.grid(row=0, column=2, pady=20, padx=2, columnspan=7)
        create_tooltip(info_icon, "This section allows you to save in json format a sinusoidal movement in your file system")
        
        
        
    # dropdown main menu (menù a tendina principale)
    def configure_menu(self):

        menubar = tk.Menu(self)
        self.config(menu=menubar)
        frame_menu = tk.Menu(menubar, tearoff=0)
        
        # Option "Rapid Movement"
        frame_menu.add_command(label="Rapid movement", command=lambda: self.show_frame(self.frame1))
        
        # Sub-menu of "Create simple movement"
        # -> "Linear movement"
        # ->"Sinusoidal movement"
        submenu_simple_movement = tk.Menu(frame_menu, tearoff=0)
        submenu_simple_movement.add_command(label="Linear movement", command=lambda: self.show_frame(self.frame2))
        submenu_simple_movement.add_command(label="Sinusoidal movement",  command=lambda: self.show_frame(self.frame4))
        frame_menu.add_cascade(label="Create simple movement", menu=submenu_simple_movement)
        
        # Option "Saved movements"
        frame_menu.add_command(label="Create complex movements", command=lambda: self.show_frame(self.frame3))
        
        # Option "Shutdown"
        frame_menu.add_command(label="Shutdown", command=lambda: self.close())
        
        menubar.add_cascade(label="Menù", menu=frame_menu)

    
    
    # Nasconde tutti i frame e mostra solo quello specificato in input
    def show_frame(self, frame):
        #Riaggiorno il frame3 sempre essendo un frame dinamico
        #self.configure_frame3()
        
        self.frame1.pack_forget()
        self.frame2.pack_forget()
        self.frame3.pack_forget()
        self.frame4.pack_forget()
        frame.pack(expand=True, fill='both')
       
    # Closing program and serial communication (shutdown option)
    def close(self):
        global arduino
        if arduino is not None:
            arduino.close()
            print("Closed serial connection")
        self.destroy() 
     
    # Empty a frame of its contents/widget. Use for update frame3 (or other frame if necessary)
    # Namely use it before re-populating a frame
    def empty_frame(self, frame): 
        for widget in frame.winfo_children():
            widget.destroy()
        
        
if __name__ == "__main__":
    app = GUI()
    app.mainloop()
