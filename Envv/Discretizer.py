import numpy as np
from abc import ABC, abstractmethod
from Utility import Toolbox


class PreDiscr():

    # Prepare the data for discretization, and then call the corresponding discretize
    # Parameter in input "item" is the selected item (dict)
    def pre_discretize(item, deltaT=None):
        if item is None:
            return None

        if len(item) == 0:  # Se la lunghezza del dizionario/lista  è 0, è vuoto oppure è None
            return None
        
        #if the item instance is a dictionary, implies that is a simple movement
        # otherwise is a list of dictionary and so a complex movement
        if isinstance(item, dict):
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
                
                # for complex movement - smaller deltaT passed
                if deltaT is None:
                    deltaT = int(values[2]) 

                linMov = LinearMovement(start_time,end_time,start_pos,end_pos,deltaT)
                #movement to visualize/execute
                movement = (linMov.discretize()).tolist()
                
                # Check if e > 100 (escludendo l'ultima colonna) - exist_cut_values: bool
                exists_cut_values = False
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
                if deltaT is None:
                    deltaT = int(values[8])
                
                amplitude = []
                for i in range(2,8):
                    amplitude.append(int(values[i][0]))
                    
                frequency = []
                for i in range(2,8):
                    frequency.append(int(values[i][1]))
                
                phase = []
                for i in range(2,8):
                    phase.append(float(values[i][2]))
                
                start_value_y = []
                for i in range(2,8):
                    start_value_y.append(int(values[i][3]))
                
                sinMov = SinusoidalMovement(start_time,end_time,amplitude,frequency,phase,start_value_y,deltaT)
                movement = (sinMov.discretize()).tolist()

                # Check if e > 100 (escludendo l'ultima colonna)
                exists_cut_values = False
                exists_cut_values = any((val > 100 or val < 0) for row in movement for val in row[:-1])

                if exists_cut_values:
                    for subrow in movement:
                        for i in range(len(subrow) - 1):  # - 1 for exclude the last column
                            if subrow[i] > 100:
                                subrow[i] = 100
                            elif subrow[i] < 0:
                                subrow[i] = 0
                return movement, exists_cut_values

        elif isinstance(item, list):
            # SAMPLING

            # Sort the dictionary w.r.t to index(level) 
            r = Toolbox.sort_and_structure(item)

            # Delete the "head" of a complex movements (does not contain values)
            result_without_head_complex = [diz for diz in r if diz.get("type") != "complex"]

            
            # Smallest deltaT, t_start and t_end calculation
            deltaT = 999999
            t_start = 999999
            t_end = -1
            for movement in result_without_head_complex:
                var = int(movement['values'][-1])
                if var <= deltaT:
                    deltaT = var
                
                #smallest t_start 
                if movement['type'] == 'sinusoidal':
                    var = int(movement['values'][0])
                    if var <= t_start:
                        t_start = var

                if movement['type'] == 'linear':
                    var = int(movement['values'][0][-1])
                    if var <= t_start:
                        t_start = var         

                #biggest t_end
                if movement['type'] == 'sinusoidal':
                    var = int(movement['values'][1])
                    if var >= t_end:
                        t_end = var

                if movement['type'] == 'linear':
                    var = int(movement['values'][1][-1])
                    if var >= t_end:
                        t_end = var  

            complexMov = ComplexMovement(t_start, t_end, deltaT, result_without_head_complex)
            movement = complexMov.discretize()
            return movement

        else:
            print("Error in the pre-discretizer")
            return None              


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
# item is the selected item in the gui (dict)
class LinearMovement(Movement):
    def __init__(self, startTime=None, endTime=None, deltaT=None, item=None):
        super().__init__(startTime, endTime)

        self.flag = False
        if item is None:
            raise TypeError("The 'item' parameter cannot be None")

        self.item = item
        self.values = item["values"] # values of the item (movement)

        self.fromPos = [] #take all start pos
        for i in range(0,len(self.values[0])-1):
            if self.values[0][i] == 'NaN':
                self.fromPos.append(np.nan)
            else:
                self.fromPos.append(int(self.values[0][i]))

        self.toPos = [] #take all end pos
        for i in range(0,len(self.values[1])-1):
            if self.values[1][i] == 'NaN':
                self.toPos.append(np.nan)
            else:
                self.toPos.append(int(self.values[1][i]))

        self.deltaT = deltaT

    def discretize(self):
        # Some check
        if all(var is None for var in [self.startTime, self.endTime, self.deltaT]):      
            self.startTime = int(self.values[0][6]) #take the start time from the item
            self.endTime = int(self.values[1][6])  #take the end time from the item    
            self.deltaT = int(self.values[2]) #take the deltaT
       
        elif all(var is not None for var in [self.startTime, self.endTime, self.deltaT]):
            self.flag = True
        else:
            raise TypeError("All arguments must be null or all non-null")

        # Discretize
        # Calcola il numero di intervalli discreti
        L = int(np.round((self.endTime - self.startTime) / self.deltaT)) + 1

        # Genera array di tempi discreti per il set corrente di parametri
        discrete_times = (np.linspace(self.startTime, self.endTime, L)).astype(np.int64)

        discrete_positions = None
        print(len(self.fromPos))
        print(len(self.toPos))
        # Restituisce numeri equidistanti in un intervallo specificato L 
        if np.isnan(self.fromPos[5]) and np.isnan(self.toPos[5]):
            discrete_positions = (np.linspace(self.fromPos[5], self.toPos[5], L))
        elif not np.isnan(self.fromPos[5]) and not np.isnan(self.toPos[5]):
            discrete_positions = (np.linspace(self.fromPos[5], self.toPos[5], L)).astype(np.int64)
        else:
            raise ValueError("Error in LinearDiscretize. fromPos and toPos must both be nan or both not NaN")

        # Impila gli array
        discretized_matrix = np.vstack((discrete_positions, discrete_times))

        # Il for è al contrario, va dall'ultimo elemento al primo per mantenere l'ordine stabilito del sistema
        for i in range(4,-1,-1):

            new_positions = None
            if np.isnan(self.fromPos[i]) and np.isnan(self.toPos[i]):
                new_positions = (np.linspace(self.fromPos[i], self.toPos[i], L))
            elif not np.isnan(self.fromPos[i]) and not np.isnan(self.toPos[i]):
                new_positions = (np.linspace(self.fromPos[i], self.toPos[i], L)).astype(np.int64)
            else:
                raise ValueError("Error in LinearDiscretize. fromPos and toPos must both be nan or both not NaN")
            
            # Impila gli array
            discretized_matrix = np.vstack((new_positions,discretized_matrix))

        result = discretized_matrix.T

        # exists_cut_values boolean for the warning in the gui
        exists_cut_values = False
        exists_cut_values = any((val > 100 or val < 0) for row in result for val in row[:-1])
        # clip values >100 and <0
        if exists_cut_values:
            result[:, :-1] = np.clip(result[:, :-1], 0, 100)

        if self.flag is False:
            # Sostituzione dei NaN con 50 se la funzione è stata direttamente chiamata dalla GUI (e quindi non siamo in un 
            # contesto di una movimento complesso più esterno)
            result = np.nan_to_num(result, nan=50)
            result = result.astype(np.int64)

        return result, exists_cut_values

class SinusoidalMovement(Movement):
    # startTime, endTime in MILLISECONDS
    # amplitude in (0-100)
    # frequency in HZ
    # phase(or amplitude shift) in RADIANT (-1,1)
    # deltaT sampling period in SECONDS (periodo di campionamento in secondi) - 0.065
    # y_init starting point of the sinusoid on the y axis
    def __init__(self, startTime=None, endTime=None, deltaT=None, item=None):
        super().__init__(startTime, endTime)

        self.flag = False
        if item is None:
            raise TypeError("The 'item' parameter cannot be None")
        
        self.item = item
        self.values = item["values"] # values of the item (movement)  
        
        self.amplitude = []
        for i in range(2,8):
            if self.values[i][0] == 'NaN':
                self.amplitude.append(np.nan)
            else:
                self.amplitude.append(int(self.values[i][0]))
            
        temp  = []
        for i in range(2,8):
            if self.values[i][1] == 'NaN':
                temp.append(np.nan)
            else:
                temp.append(int(self.values[i][1]))
        a = np.array(temp)
        self.frequency = a/1000 #Converting from sampling period to sampling rate
        
        self.phase = []
        for i in range(2,8):
            if self.values[i][2] == 'NaN':
                 self.phase.append(np.nan)
            else:
                self.phase.append(float(self.values[i][2]))
        
        self.y_init = []
        for i in range(2,8):
            if self.values[i][3] == 'NaN':
                self.y_init.append(np.nan)
            else:
                self.y_init.append(int(self.values[i][3]))

        self.deltaT = deltaT

    def discretize(self):
        if all(var is None for var in [self.startTime, self.endTime, self.deltaT]):      
            self.startTime = int(self.values[0]) #take the start time from the item
            self.endTime = int(self.values[1]) #...
            self.deltaT = (int(self.values[8]))/1000 #in secondi
        elif all(var is not None for var in [self.startTime, self.endTime, self.deltaT]):
            self.deltaT = self.deltaT/1000     
            self.flag = True      
        else:
            raise TypeError("All arguments must be null or all non-null")
        
        # Converte gli istanti di tempo da millisecondi a secondi per il calcolo
        self.startTime = self.startTime / 1000
        self.endTime = self.endTime / 1000

        # Genera un array di tempi da startTime a end_time con intervalli di deltaT(periodo di campionamento)
        t = np.arange(self.startTime, self.endTime, self.deltaT)
        t_millis = t*1000 #per l'output si usano i millisecondi

        #first element
        column1 = self.amplitude[5] * np.sin(2 * np.pi * self.frequency[5] * t + (self.phase[5]*np.pi)) + self.y_init[5]
        y = np.vstack((column1,t_millis)) 
        for i in range(4,-1,-1):
            
            # Calcola i valori della sinusoide
            # y è un array di valori che rappresentano l'ampiezza della sinusoide in corrispondenza di ciascun istante di tempo t
            # self.y_init è l'offset che permette all'utente di decidere su quale valore y iniziare
            column_i = self.amplitude[i] * np.sin(2 * np.pi * self.frequency[i] * t + (self.phase[i]*np.pi)) + self.y_init[i] 
            y = np.vstack((column_i,y))

        result = y.T
        
        # exists_cut_values boolean for the warning in the gui
        exists_cut_values = False
        exists_cut_values = any((val > 100 or val < 0) for row in result for val in row[:-1])
        # clip values >100 and <0
        if exists_cut_values:
            result[:, :-1] = np.clip(result[:, :-1], 0, 100)

        if self.flag is False:
            # Sostituzione dei NaN con 50 se la funzione è stata direttamente chiamata dalla GUI (e quindi non siamo in un 
            # contesto di una movimento complesso più esterno)
            result = np.nan_to_num(result, nan=50)
            result = result.astype(np.int64)

        return result, exists_cut_values
    
# item must be a list of dictionary (elements_in_tree_view)
class ComplexMovement(Movement):
        def __init__(self, startTime, endTime, deltaT, item):
            super().__init__(startTime, endTime)

            if item is None:
                raise TypeError("The 'item' parameter cannot be None")
            self.deltaT = deltaT
            self.item = item

        def discretize(self):
            if all(var is None for var in [self.startTime, self.endTime, self.deltaT]):    
                # Sort the dictionary w.r.t to index(level) 
                r = Toolbox.sort_and_structure(self.item)

                # Delete the "head" of a complex movements (does not contain values)
                result_without_head_complex = [diz for diz in r if diz.get("type") != "complex"]

                
                # Smallest deltaT, t_start and t_end calculation
                deltaT = 999999
                t_start = 999999
                t_end = -1
                for movement in result_without_head_complex:
                    var = int(movement['values'][-1])
                    if var <= deltaT:
                        deltaT = var
                    
                    #smallest t_start 
                    if movement['type'] == 'sinusoidal':
                        var = int(movement['values'][0])
                        if var <= t_start:
                            t_start = var

                    if movement['type'] == 'linear':
                        var = int(movement['values'][0][-1])
                        if var <= t_start:
                            t_start = var         

                    #biggest t_end
                    if movement['type'] == 'sinusoidal':
                        var = int(movement['values'][1])
                        if var >= t_end:
                            t_end = var

                    if movement['type'] == 'linear':
                        var = int(movement['values'][1][-1])
                        if var >= t_end:
                            t_end = var  

            return 
            
            
