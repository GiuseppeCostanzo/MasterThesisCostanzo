import numpy as np
from abc import ABC, abstractmethod
from Utility import Toolbox


class PreDiscr():

    # Prepare the data for discretization, and then call the corresponding discretize
    # Parameter in input "item" is the selected item (dict)
    def pre_discretize(item):
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
            movement = (linMov.discretize()).tolist()
            
            # Check if e > 100 (escludendo l'ultima colonna)
            exists_cut_values = any((val > 100 or val < 0) for row in movement for val in row[:-1])

            if exists_cut_values:
                for subrow in movement:
                    for i in range(len(subrow) - 1):  # - 1 for exclude the last column
                        if subrow[i] > 100:
                            subrow[i] = 100
                        elif subrow[i] < 0:
                            subrow[i] = 0
            return movement, exists_cut_values
            
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

            # Check if e > 100 (escludendo l'ultima colonna)
            exists_cut_values = any((val > 100 or val < 0) for row in movement for val in row[:-1])

            if exists_cut_values:
                for subrow in movement:
                    for i in range(len(subrow) - 1):  # - 1 for exclude the last column
                        if subrow[i] > 100:
                            subrow[i] = 100
                        elif subrow[i] < 0:
                            subrow[i] = 0
            return movement, exists_cut_values




# Abstract father class
class Movement(ABC):
    def __init__(self, startTime, endTime):
        self.startTime = startTime
        self.endTime = endTime
        #L=(np.round((self.endTime-self.startTime)/deltaT)+1).astype(np.int64)
        #self.DiscreteMov=None

    @abstractmethod
    def discretize(self):
        pass

# fromPos and toPos are two lists
class LinearMovement(Movement):
    def __init__(self, startTime, endTime, fromPos, toPos, deltaT=70):
        super().__init__(startTime, endTime)
        self.fromPos = fromPos
        self.toPos = toPos
        self.deltaT = deltaT
        
    def discretize(self):
        # Calcola il numero di intervalli discreti
        L = int(np.round((self.endTime - self.startTime) / self.deltaT)) + 1

        # Genera array di tempi discreti per il set corrente di parametri
        tempi_discreti = (np.linspace(self.startTime, self.endTime, L)).astype(np.int64)

        # Restituisce numeri equidistanti in un intervallo specificato L 
        posizioni_discrete = (np.linspace(self.fromPos[5], self.toPos[5], L)).astype(np.int64)
        
        # Impila gli array
        matrice_discretizzata = np.vstack((posizioni_discrete, tempi_discreti))

        # Il for è al contrario, va dall'ultimo elemento al primo per mantenere l'ordine stabilito del sistema
        for i in range(4,-1,-1):
            nuove_posizioni = (np.linspace(self.fromPos[i], self.toPos[i], L)).astype(np.int64)
            # Impila gli array
            matrice_discretizzata = np.vstack((nuove_posizioni,matrice_discretizzata))
        return matrice_discretizzata.T

class SinusoidalMovement(Movement):
    # startTime, endTime in MILLISECONDS
    # amplitude in (0-100)
    # frequency in HZ
    # phase(or amplitude shift) in RADIANT (-1,1)
    # deltaT sampling period in SECONDS (periodo di campionamento in secondi) - 0.065
    # y_init starting point of the sinusoid on the y axis
    def __init__(self, startTime, endTime, amplitude, frequency, phase, y_init,deltaT=70):
        super().__init__(startTime, endTime)
        self.amplitude = amplitude
        a = np.array(frequency)
        self.frequency = (a/1000).tolist()
        self.phase = phase
        self.deltaT = deltaT/1000 # Periodo di campionamento (riporto in secondi)
        self.y_init = y_init
        
    def discretize(self):
        # Converte gli istanti di tempo da millisecondi a secondi per il calcolo
        self.startTime = self.startTime / 1000
        self.endTime = self.endTime / 1000

        # Genera un array di tempi da startTime a end_time con intervalli di deltaT(periodo di campionamento)
        t = np.arange(self.startTime, self.endTime, self.deltaT)
        t_millis = t*1000 #per l'output si usano i millisecondi
        
        column1 = self.amplitude[5] * np.sin(2 * np.pi * self.frequency[5] * t + self.phase[5]) + self.y_init[5]
        y = np.vstack((column1,t_millis)) 
        for i in range(4,-1,-1):
            
            # Calcola i valori della sinusoide
            # y è un array di valori che rappresentano l'ampiezza della sinusoide in corrispondenza di ciascun istante di tempo t
            # self.y_init è l'offset che permette all'utente di decidere su quale valore y iniziare
            column_i = self.amplitude[i] * np.sin(2 * np.pi * self.frequency[i] * t + self.phase[i]) + self.y_init[i] 
            y = np.vstack((column_i,y))
            
        matrix = y.astype(np.int64) #to int
        return matrix.T 
    
class ComplexMovement(Movement):
        def __init__(self, startTime, endTime, all_movements):
            super().__init__(startTime, endTime)
            self.all_movements = all_movements

        def discretize(self):
            # SAMPLING
            r = Toolbox.sort_and_structure(self.all_movements)
            # Sort the dictionary w.r.t to index(level) 
            # Delete the "head" of a complex movements (does not contain values)
            result_without_head_complex = [diz for diz in r if diz.get("type") != "complex"]

            # Discretize all the submovements
            result_discr = []
            for mov in result_without_head_complex:
                result_discr.append(PreDiscr.pre_discretize(mov)) #deltaT più piccolo

            
            
