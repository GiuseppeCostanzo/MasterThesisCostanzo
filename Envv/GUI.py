# Libraries
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter import Menu
import serial  
import json
import os
import time
import functools
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkinter import filedialog
import copy

# Customized classes for linear and sinusoidal movements (in the same folder)
from Movement_file_class import LinearMovement 
from Movement_file_class import SinusoidalMovement

# Global parameters, eventually to be set
usbport = 'COM7' # Usb port where arduino is connected 
arduino = None # Arduino communication instance
baud = 38400 # Baud - speed parameter for arduino comm. (MUST BE the same value in the arduino sketch)

# Internal usage
start_time = None # used to calculate the time start of the button)
tree_view = [] #for visualizing the imported json in complex movement frame3

# This 2 functions maps an input value (in range 0-100) to the corresponding value on the servo, accordingly to the 
# configuration on the json file


# GENERAL MAPPING
def mapping(thumb_big_value, thumb_little_value, index_finger_value, middle_finger_value, ringPinky_value, forearm_value):
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
        fingers_data_mapped.append(calculus(input_values[i],start,stop))
        i = i+1
        
    return fingers_data_mapped
        
def calculus(val,start,stop):
    if start==0:
        return int((val/100)*stop)
    else:
        new_stop = stop - start
        return int(((val/100)*new_stop)+start)  


# FUNZIONE PER SALVARE UN MOVIMENTO
# Struttura di salvataggio: thumb_big, thumb_little, index, middle, ringPinky, forearm, time
# Movement deve essere una list di list (matrice)

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
            json.dump(data, json_file, ensure_ascii=False)
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
    fingers_data_mapped = mapping(packet[0],packet[1],packet[2],packet[3],packet[4],packet[5])
    # Send values to arduino
    global arduino
    arduino.write(bytearray(fingers_data_mapped))


# Funzione per il salvataggio dei movimenti lineari in frame2
def on_save_linear(gui_instance,init_list,end_list,time_init,time_end,deltaT):
       
    #il .get() si usa qui perchè sono delle entry che vengono passate. Se venisse usato a monte nella gui, i campi
    # sarebbero vuoti perchè non viene atteso il click del pulsante
    # Controlli (il controllo che siano numeri in un certo range viene fatto direttamente sui campi con altre funzioni)
    for item in init_list:
        if item.get() == '' or item.get() is None:
            messagebox.showerror("Error", "Fill all init fields")
            return
            
    for item in end_list:
        if item.get() == '' or item.get() is None:
            messagebox.showerror("Error", "Fill all end fields ")
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
        init_list_unpacked.append(item.get())
    init_list_unpacked.append(time_init.get())
            
    for item in end_list:
        end_list_unpacked.append(item.get())
    end_list_unpacked.append(time_end.get())
        
    #salvataggio nel json
    data = {
        "type": "linear",
        "values": [init_list_unpacked,end_list_unpacked,deltaT.get()]
    }
    save_movement(data)
    
# Classe per la creazione della tabella per visualizzare i movimenti in FRAME 3
class Table(tk.Frame):
    def __init__(self, master, headers, data):
        super().__init__(master)
        self.headers = headers
        self.data = data
        self.create_table()

    def create_table(self):
        self.tree = ttk.Treeview(self, columns=self.headers, show="headings")

        # Aggiunta header
        for header in self.headers:
            self.tree.heading(header, text=header, anchor="center")
            self.tree.column(header, width=80)

        for row in self.data:
            self.tree.insert("", "end", values=row)

        # Scrollbar
        vsb = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")

        self.tree.pack(expand=True, fill="both")
        
        
#legge valori dal movements.json che contiene i movimenti salvati***********************
def read_json():
    try:
        with open("movements.json", 'r') as file:
            data = json.load(file)
        return data
    except FileNotFoundError:
        print("File not found")
        return None
    except json.JSONDecodeError as e:
        print("Parsing error in the json file:", e)
        return None
        
# Prepare the data for discretization, and then call the corresponding discretize **************************
def pre_discretize(item):
    
    if len(item) == 0:  # Se la lunghezza del dizionario è 0, è vuoto
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
        movement = (linMov.discretize()).tolist()
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
        movement = (sinMov.discretize()).tolist()
        return movement
        
   
    if item["type"] == "complex":
        print("movimento complesso")
        
        
# funzione per eseguire un movimento salvato **************************************************************
def execute_movement(item):
    print(item)
    movement = pre_discretize(item)
    if movement is None:
        messagebox.showerror("Error", "Select or import a movement")
        return 
        
    
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
        
        fingers_data_mapped = mapping(movement[packet][0],movement[packet][1],movement[packet][2],movement[packet][3],movement[packet][4],movement[packet][5])
        
        global arduino
        arduino.write(bytearray(fingers_data_mapped))       
        
        
        
        
    
#funzione per visualizzare un movimento in frame3*************************************************************
def visualize_movement(gui_instance,item):
    movement_name="Movement"
    movement = pre_discretize(item)
    if movement is None:
        messagebox.showerror("Error", "Select or import a movement")
        return 
    
    
    # Creazione della finestra di input
    input_window = tk.Toplevel(gui_instance)
    input_window.title(movement_name)
    input_window.geometry("700x800")
    input_window.pack_propagate(False)  # Per evitare che la finestra si ridimensioni in base al contenuto
    
    # Table (in input_window)
    headers = ["Thumb(B)", "Thumb(L)","Index","Middle","Ring/Pinky","Forearm","Time instant (ms)"]
    table = Table(input_window, headers, movement)
    table.pack(expand=True, fill="both")
    
    # Frame 2 (contiene checkbox+plot)
    frame2 = tk.Frame(input_window)
    frame2.pack(side="top", expand=True, fill="both", padx=1, pady=1)
    frame2.pack_propagate(True) 
    create_plot(frame2,movement)
    
def create_plot(master, movement):
    #figure = Figure(figsize=(8, 6), dpi=75)
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



    
# funzione per eliminare un movimento
def delete_movement(gui_instance,movement_to_delete):
    
    # Carica i dati esistenti dal file JSON se esiste
    if os.path.exists("movements.json"):
        #Se il file esiste, apro il file
        with open("movements.json", 'r') as file_json:
            dati = json.load(file_json)
            
        if movement_to_delete in dati:
            del dati[movement_to_delete]
            
            # Save the updated dictionary
            with open("movements.json", "w") as json_file:
                json.dump(dati, json_file)
                
            #Re-call the frame3 for the update
            gui_instance.show_frame(gui_instance.frame3)
            return True
            
        else:
            print(f"The movement '{movement_to_delete}' does not exists")
            return False
    else:
        print("The file movements.json does not exists")
        return False
    
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
        for column in range(1, 5):
            if entries[(row, column)].get() == '' or entries[(row, column)].get() is None:
                messagebox.showerror("Error", "Fill all fields")
                return
    if startTime.get() == '' or startTime.get() is None:
        messagebox.showerror("Error", "Fill start time field")
        return
    
    if endTime.get() == '' or endTime.get() is None:
        messagebox.showerror("Error", "Fill end time field")
        return
    
     
    #struttura di salvataggio : 6 liste -> thumbB, thumbL, index, middle, ring/pinky, forearm 
    # al cui interno hanno 4 valori ognuno -> startTime, endTime, amplitude, freq., phase, y inizio, deltaT
    values = [[],[],[],[],[],[]]
    for row in range(0, 6):
        for column in range(1, 5):
            values[(row)].append(entries[(row, column)].get())
    data = {
        "type": "sinusoidal",
        "values": [startTime.get(),endTime.get(),values[0],values[1],values[2],values[3],values[4],values[5],deltaT.get()]
    } 
    save_movement(data) 




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
        label1 = tk.Label(self.frame1, text="Thumb - big servo")
        label1.grid(row=1,column=0,sticky="e")
        thumb_big = tk.Entry(self.frame1, fg='black',validate="key", 
                             validatecommand=(validate_cmd, "%d", "%i", "%P", "%s", "%S", "%v", "%V", "%W"))
        thumb_big.configure(justify=tk.CENTER) 
        thumb_big.grid(row=1,column=1)
        
        # Text2
        label2 = tk.Label(self.frame1, text="Thumb - little servo")
        label2.grid(row=2,column=0,sticky="e")
        thumb_little = tk.Entry(self.frame1, fg='black',validate="key", 
                                validatecommand=(validate_cmd, "%d", "%i", "%P", "%s", "%S", "%v", "%V", "%W"))
        thumb_little.configure(justify=tk.CENTER) 
        thumb_little.grid(row=2,column=1,pady=5)

        
        # Text3
        label3 = tk.Label(self.frame1, text="Index finger")
        label3.grid(row=3,column=0,sticky="e")
        index_finger = tk.Entry(self.frame1, fg='black',validate="key", validatecommand=(validate_cmd, "%d", "%i", "%P", "%s", "%S", "%v", "%V", "%W"))
        index_finger.configure(justify=tk.CENTER) 
        index_finger.grid(row=3,column=1,pady=5)
        
        # Text4
        label4 = tk.Label(self.frame1, text="Middle finger")
        label4.grid(row=4,column=0,sticky="e")
        middle_finger = tk.Entry(self.frame1, fg='black',validate="key", 
                                 validatecommand=(validate_cmd, "%d", "%i", "%P", "%s", "%S", "%v", "%V", "%W"))
        middle_finger.configure(justify=tk.CENTER) 
        middle_finger.grid(row=4,column=1,pady=5)
        # Text5
        label5 = tk.Label(self.frame1, text="Ring and Pinky")
        label5.grid(row=5,column=0,sticky="e")
        ring_pinky = tk.Entry(self.frame1, fg='black',validate="key", 
                              validatecommand=(validate_cmd, "%d", "%i", "%P", "%s", "%S", "%v", "%V", "%W"))
        ring_pinky.configure(justify=tk.CENTER) 
        ring_pinky.grid(row=5,column=1,pady=5)
        
        # Text6
        label6 = tk.Label(self.frame1, text="Forearm")
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
        
        

    # ***************************** FRAME 2 - LINEAR MOVEMENT -CONFIGURATION *************************************************
    def configure_frame2(self):
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
        label1 = tk.Label(self.frame2, text="Thumb - big servo")
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
        label2 = tk.Label(self.frame2, text="Thumb - little servo")
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
        label3 = tk.Label(self.frame2, text="Index")
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
        label4 = tk.Label(self.frame2, text="Middle")
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
        label5 = tk.Label(self.frame2, text="Ring-Pinky")
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
        label6 = tk.Label(self.frame2, text="Forearm")
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
        label_start_time = tk.Label(self.frame2, text="Start time (millis)")
        label_start_time.grid(row=8,column=1,sticky='nsew',pady=10)
        
        label_end_time = tk.Label(self.frame2, text="End time (millis)")
        label_end_time.grid(row=8,column=2,sticky='nsew',pady=10)
        
        
        label7 = tk.Label(self.frame2, text="Time")
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
        label8 = tk.Label(self.frame2, text="DeltaT (default 70ms)")
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
                thumb_big_init.insert(0, a)
                thumb_big_init.config(validatecommand=(validate_cmd, "%d", "%i", "%P", "%s", "%S", "%v", "%V", "%W"))
                thumb_big_init.configure(justify=tk.CENTER) 
                thumb_big_init.grid(row=2,column=1,padx=5) 

                # entry - end position
                thumb_big_end = tk.Entry(new_window, fg='black',validate="key")
                a = selected_item_tree_view["values"][1][0]
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
                thumb_little_init.insert(0, a)
                thumb_little_init.config(validatecommand=(validate_cmd, "%d", "%i", "%P", "%s", "%S", "%v", "%V", "%W"))
                
                thumb_little_init.configure(justify=tk.CENTER) 
                thumb_little_init.grid(row=3,column=1,padx=5)

                # entry - end position
                thumb_little_end = tk.Entry(new_window, fg='black',validate="key")
                a = selected_item_tree_view["values"][1][1]
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
                index_init.insert(0, a)
                index_init.config(validatecommand=(validate_cmd, "%d", "%i", "%P", "%s", "%S", "%v", "%V", "%W"))
                index_init.configure(justify=tk.CENTER) 
                index_init.grid(row=4,column=1,padx=5)

                # entry - end position
                index_end = tk.Entry(new_window, fg='black',validate="key")
                a = selected_item_tree_view["values"][1][2]
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
                middle_init.insert(0, a)
                middle_init.config(validatecommand=(validate_cmd, "%d", "%i", "%P", "%s", "%S", "%v", "%V", "%W"))
                middle_init.configure(justify=tk.CENTER) 
                middle_init.grid(row=5,column=1,padx=5)

                # entry - end position
                middle_end = tk.Entry(new_window, fg='black',validate="key")
                a = selected_item_tree_view["values"][1][3]
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
                ring_pinky_init.insert(0, a)
                ring_pinky_init.config(validatecommand=(validate_cmd, "%d", "%i", "%P", "%s", "%S", "%v", "%V", "%W"))
                ring_pinky_init.configure(justify=tk.CENTER) 
                ring_pinky_init.grid(row=6,column=1,padx=5)

                # entry - end position
                ring_pinky_end = tk.Entry(new_window, fg='black',validate="key")
                a = selected_item_tree_view["values"][1][4]
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
                forearm_init.insert(0, a)
                forearm_init.config(validatecommand=(validate_cmd, "%d", "%i", "%P", "%s", "%S", "%v", "%V", "%W"))
                forearm_init.configure(justify=tk.CENTER) 
                forearm_init.grid(row=7,column=1,padx=5)

                # entry - end position
                forearm_end = tk.Entry(new_window, fg='black',validate="key")
                a = selected_item_tree_view["values"][1][5]
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

                #array dei valori di partenza
                init_list = [thumb_big_init,thumb_little_init,index_init,middle_init,
                             ring_pinky_init,forearm_init]

                #array dei valori fine
                end_list = [thumb_big_end,thumb_little_end,index_end,middle_end,
                            ring_pinky_end,forearm_end]

                # function for saving modified values
                def save_l(init_list,end_list,time_init,time_end,deltaT):

                    for item in init_list:
                        if item.get() == '' or item.get() is None:
                            messagebox.showerror("Error", "Fill all init fields")
                            return
                        
                    for item in end_list:
                        if item.get() == '' or item.get() is None:
                            messagebox.showerror("Error", "Fill all end fields ")
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
                        init_list_unpacked.append(item.get())
                    init_list_unpacked.append(time_init.get())
                            
                    for item in end_list:
                        end_list_unpacked.append(item.get())
                    end_list_unpacked.append(time_end.get())

                    nonlocal elements_in_tree_view
                    nonlocal selected_item_tree_view
                    nonlocal new_window
                    for element in elements_in_tree_view:
                        if element["id"] == selected_item_tree_view["id"]:
                            element["values"][0] = init_list_unpacked
                            element["values"][1] = end_list_unpacked
                            element["values"][2] = deltaT.get()
                            new_window.destroy()
                            return
                    print("ERROR, the selected item does not exists")
                    new_window.destroy()
                    return
                # Button (save in RAM - elements_in_tree_view)
                button1 = tk.Button(new_window, text="Save", height=1, width=10, font= 2,command=lambda:save_l(init_list,end_list,time_init,time_end,deltaT))
                button1.grid(row=11,column=0,pady=20,columnspan=4)

            if movement_type == "sinusoidal":
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
                        entry = tk.Entry(new_window, width=15, validate="key",
                                        validatecommand=(validate_entries, "%d", "%i", "%P", "%s", "%S", "%v", "%V", "%W"))
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
                deltaT_entry = tk.Entry(new_window,width=15, validate="key",
                                    validatecommand=(validate_entries, "%d", "%i", "%P", "%s", "%S", "%v", "%V", "%W"))
                deltaT_entry.grid(row=11, column=1, padx=5, pady=5)
                
                #entry startTime
                startTime_entry = tk.Entry(new_window,width=15, validate="key",
                                        validatecommand=(validate_entries, "%d", "%i", "%P", "%s", "%S", "%v", "%V", "%W"))
                startTime_entry.grid(row=11, column=2, padx=5, pady=5)
                
                #entry endTime
                endTime_entry = tk.Entry(new_window,width=15, validate="key",
                                        validatecommand=(validate_entries, "%d", "%i", "%P", "%s", "%S", "%v", "%V", "%W"))
                endTime_entry.grid(row=11, column=3, padx=5, pady=5)
                
                # Funzione per la modifica dei movimenti sinsuoidal 
                def save_s(gui_instance,startTime,endTime,entries,deltaT):
                    #entry_11 = entries[(row, column)].get() #access 
                    
                    #check empty values
                    for row in range(0, 6):
                        for column in range(1, 5):
                            if entries[(row, column)].get() == '' or entries[(row, column)].get() is None:
                                messagebox.showerror("Error", "Fill all fields")
                                return
                    if startTime.get() == '' or startTime.get() is None:
                        messagebox.showerror("Error", "Fill start time field")
                        return
                    
                    if endTime.get() == '' or endTime.get() is None:
                        messagebox.showerror("Error", "Fill end time field")
                        return
                    
                    
                    # struttura di salvataggio : 6 liste -> thumbB, thumbL, index, middle, ring/pinky, forearm 
                    # al cui interno hanno 4 valori ognuno (amplitude, freq, phase, y_inizio) -> startTime, endTime, lista[i], deltaT
                    values = [[],[],[],[],[],[]]
                    for row in range(0, 6):
                        for column in range(1, 5):
                            values[(row)].append(entries[(row, column)].get())
                    '''data = {
                        "type": "sinusoidal",
                        "values": [startTime.get(),endTime.get(),values[0],values[1],values[2],values[3],values[4],values[5],deltaT.get()]
                    } 
                    save_movement(data) '''

                # Button
                button1 = tk.Button(new_window, text="Save", height=1, width=10, font= 2)
                                #command=lambda: on_save_sinusoidal(self,startTime_entry,endTime_entry,entries,deltaT_entry))
                button1.grid(row=12,column=0,pady=20, padx=15, columnspan=7)

        
        
        # inner functions
        # funzione per editare un movimento
        def modify():
            print(selected_item_tree_view)
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
                return;
            
            
            
            
            
            
                
                
            
            
        #funzione per modificare un movimento in modo rapido  
        #l'idea è quella di poter modificare tutti i movimenti base
        #Di un movimento complesso dunque posso scalare 
        def scale():
            print("scale")
            
        #inverte i valori del movimento
        def flip():
            print("flip")
            
        # salva un movimento complesso
        def save_complex_movement():
            print("da implementare")
            
        
        # return the index on the treeview (level) of an element in the treeview given the id of the item
        def get_index_by_id(item_id):
            nonlocal tree
            if item_id in tree.get_children():
                index = tree.index(item_id)
                return index
            else:
                return None
            
        #update the indexes (levels) of the elements in treeview (called on import json or click "up" or "down")
        def update_index():
            for element in elements_in_tree_view:
                element["index"] = get_index_by_id(element["id"])
        
        # Used to see if the json import operation was successful, and then populate the treeview
        def import_json_inner():
            
            # Recursive reading of the json
            def recursive_reading(father_id, t_w):
                for movement in t_w:
                    if(movement[1]['type'] == 'linear'):    
                        if father_id is None:
                            a = " - Type: Linear movement"
                            b = movement[0]
                            c = b + a
                            id_element = tree.insert("", "end", text=c)
                            elements_in_tree_view.append({"id":id_element,"values":(movement[1]['values']),
                                                          "type":"linear","index":None, "root":(tree.parent(id_element))})
                        else:
                            a = " Type: Linear movement"
                            b = movement[0]
                            c = b + a
                            id_element = tree.insert(father_id, "end", text=c)
                            elements_in_tree_view.append({"id":id_element,"values":(movement[1]['values']),
                                                          "type":"linear","index":None,"root":(tree.parent(id_element))})
                        
                    elif(movement[1]['type'] == 'sinusoidal'):
                        if father_id is None:
                            a = " - Type: Sinusoidal movement"
                            b = movement[0]
                            c = b + a
                            id_element = tree.insert("", "end", text=c)
                            elements_in_tree_view.append({"id":id_element,"values":(movement[1]['values']),
                                                          "type":"sinusoidal","index":None,"root":(tree.parent(id_element))})
                        else:
                            a = " Type: Sinusoidal movement"
                            b = movement[0]
                            c = b + a
                            id_element = tree.insert(father_id, "end", text=c)
                            elements_in_tree_view.append({"id":id_element,"values":(movement[1]['values']),
                                                          "type":"sinusoidal","index":None,"root":(tree.parent(id_element))})
                        
                    
                    elif(movement[1]['type'] == 'complex'):
                        # se il movimento è complesso, faccio una copia una nuova lista
                        # che popolo con i sotto-movimenti che passo ricorsivamente a 
                        # recursive_reading
                        if father_id is None:
                            a = " - Type: Complex movement"
                            b = movement[0]
                            c = b + a
                            id_element = tree.insert("", "end", text=c)
                            elements_in_tree_view.append({"id":id_element,"values":(movement[1]['values']),
                                                          "type":"complex","index":None,"root":(tree.parent(id_element))})
                            twc = []
                            for a in (movement[1]['values']):
                                #recursive tree_view reconstruction
                                twc.append(["->",a])
                            #recursion
                            recursive_reading(id_element,twc)
                            father_id = None
                        else:
                            a = " Type: Complex movement"
                            b = movement[0]
                            c = b + a
                            id_element = tree.insert(father_id, "end", text=c)
                            elements_in_tree_view.append({"id":id_element,"values":(movement[1]['values']),
                                                          "type":"complex","index":None,"root":(tree.parent(id_element))})
                            twc = []
                            for a in (movement[1]['values']):
                                #recursive tree_view reconstruction
                                twc.append(["->",a])
                            #recursion
                            recursive_reading(id_element,twc)
                            father_id = None
                
                update_index()
                #print(elements_in_tree_view)
            if import_json() is True:
                tree.delete(*tree.get_children()) #empty the treeview
                global tree_view
                recursive_reading(None, tree_view)
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
                #print(elements_in_tree_view)
                    
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
                #print(elements_in_tree_view)
        
        
        # Function called when an element of the treeview is selected
        # it saves selected motion information in selected_item_tree_view
        def on_tree_select(event):
            if len(tree.selection()) == 0:
                print("tupla vuota in on_tree_select")
                return
            
            nonlocal id_item
            id_item = tree.selection()[0] #id dell'item selezionato
            #elements_in_tree_view è una list di dizionari
            for element in elements_in_tree_view:
                if id_item == element["id"]:
                    nonlocal selected_item_tree_view
                    #selected_item_tree_view.clear()
                    selected_item_tree_view = element.copy()
                    print(selected_item_tree_view)
                    return
              
        #delete an item from treeview 
        def delete_item():
            nonlocal id_item
            nonlocal elements_in_tree_view
            if id_item is None:
                messagebox.showerror("Error", "Select a movement to delete")
                return
            for item in tree.selection():
                tree.selection_remove(item)
            tree.delete(id_item)
            #elimino l'elemento anche da elements_in_tree_view
            elements_in_tree_view = [dizionario for dizionario in elements_in_tree_view if id_item not in dizionario]
            #print(elements_in_tree_view)
                    
            
        # Aggiungere Menubuttons al frame
        file_button = ttk.Menubutton(self.frame3, text="Edit")
        file_button.grid(row=1, column=0)
        file_menu = Menu(file_button, tearoff=0)
        file_button['menu'] = file_menu
        file_menu.add_command(label="Import JSON", command=import_json_inner)
        file_menu.add_command(label="Modify", command=modify)
        
        # Creazione del sottomenu per "Scale"
        modify_menu = Menu(file_menu, tearoff=0)
        modify_menu.add_command(label="1.5x")
        modify_menu.add_command(label="2x")
        modify_menu.add_command(label="0.5x")
        modify_menu.add_command(label="Specific")
        file_menu.add_cascade(label="Scale", menu=modify_menu)
        
        file_menu.add_command(label="Flip", command=flip)
        
        tree.bind("<<TreeviewSelect>>", on_tree_select)
        
        # Buttons
        button_execute = tk.Button(self.frame3, text="Execute",
                                 command=lambda: execute_movement(selected_item_tree_view))
        button_execute.grid(row=1,column=1)
        
        button_visualize = tk.Button(self.frame3, text="Visualize", #command=functools.partial(aa))
                                     command=lambda: visualize_movement(self.frame3, selected_item_tree_view))
        button_visualize.grid(row=1,column=2)
        
        button_delete = tk.Button(self.frame3, text="Delete",
                                 command=delete_item)
        button_delete.grid(row=1,column=3)
        
        button_up = tk.Button(self.frame3, text="Up",command=move_up)
        button_up.grid(row=4,column=0)
        
        button_down = tk.Button(self.frame3, text="Down",command=move_down)
        button_down.grid(row=5,column=0)
        
        button_save = tk.Button(self.frame3, text="Save",command=save_complex_movement)
        button_save.grid(row=8,column=0)
        
        


    # *************************************** FRAME 4 - SINUSOIDAL MOVEMENT **********************************************
    def configure_frame4(self):
        
        for i in range(13):
            self.frame4.grid_rowconfigure(i, weight=0)
        
        for i in range(7):
            self.frame4.grid_columnconfigure(i, weight=1)
            
        #validation functions for entries (only digit)
        validate_entries = self.frame4.register(on_validate2)
        
        title = tk.Label(self.frame4, text="Sinusoidal movement",font="8")
        title.grid(row=0, column=0, pady=20, padx=2, columnspan=7)
        
        # amplitude, frequency, phase, deltaT, y_init
        
        amplitude_label = tk.Label(self.frame4, text="Amplitude(0-100)")
        amplitude_label.grid(row=1, column=1)
        
        frequency_label = tk.Label(self.frame4, text="Frequency(mHz)")
        frequency_label.grid(row=1, column=2)
        
        phase_label = tk.Label(self.frame4, text="Amp. Shift(-1,1)")
        phase_label.grid(row=1, column=3)
        
        y_init_label = tk.Label(self.frame4, text="Start value(0-100)")
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
        
        TL_label = tk.Label(self.frame4, text= "Thumb/Little")
        TL_label.grid(row=6, column=0, padx=5, pady=5,sticky="e")
        
        forearm_label = tk.Label(self.frame4, text= "Forearm")
        forearm_label.grid(row=7, column=0, padx=5, pady=5,sticky="e")
        
        # Dizionario per memorizzare gli entry
        entries = {}

        # Creazione della griglia 4x4=16 campi di input (a cui vi si accede come fosse una matrice)
        for i in range(2, 8):
            for j in range(1, 5):
                entry = tk.Entry(self.frame4, width=15, validate="key",
                                 validatecommand=(validate_entries, "%d", "%i", "%P", "%s", "%S", "%v", "%V", "%W"))
                entry.grid(row=i, column=j, padx=10, pady=5)
                # Salva l'entry nel dizionario con una chiave unica
                entries[((i-2), j)] = entry
            
        
        
        deltaT_label = tk.Label(self.frame4, text="deltaT (ms)")
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
