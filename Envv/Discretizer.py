import numpy as np
from abc import ABC, abstractmethod
from Utility import Toolbox

# Abstract father class
class Movement(ABC):
    def __init__(self, startTime, endTime):
        self.startTimePassed = startTime
        self.endTimePassed = endTime
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

        if item is None:
            raise TypeError("The 'item' parameter cannot be None")
        
        self.item = item
        self.values = item["values"] # values of the item (movement)
        self.flag = False
        self.deltaT = deltaT
        self.startTime = int(self.values[0][6]) #take the start time from the item (json)
        self.endTime = int(self.values[1][6])  #take the end time from the item (json)
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

    def discretize(self):
        # Some check
        if all(var is None for var in [self.startTimePassed, self.endTimePassed, self.deltaT]):      
            self.deltaT = int(self.values[2]) #take the deltaT from item (json)
       
        elif all(var is not None for var in [self.startTimePassed, self.endTimePassed, self.deltaT]):
            self.flag = True
        else:
            raise TypeError("All arguments must be null or all non-null")

        # Discretize
        # Genera un array di tempi da startTime a end_time con intervalli di deltaT(periodo di campionamento)
        discrete_times = np.arange(self.startTime, self.endTime+self.deltaT, self.deltaT)

        #L_external = None
        discrete_times_external = None
        if self.flag is True:

            discrete_times_external = np.arange(self.startTimePassed, self.endTimePassed+self.deltaT, self.deltaT)

        discrete_positions = None
        # Restituisce numeri equidistanti in un intervallo specificato L 
        if np.isnan(self.fromPos[5]) and np.isnan(self.toPos[5]):
            discrete_positions = (np.linspace(self.fromPos[5], self.toPos[5], len(discrete_times)))
        elif not np.isnan(self.fromPos[5]) and not np.isnan(self.toPos[5]):
            discrete_positions = (np.linspace(self.fromPos[5], self.toPos[5], len(discrete_times))).astype(np.int64)
        else:
            raise ValueError("Error in LinearDiscretize. fromPos and toPos must both be nan or both not NaN")

        # Impila gli array
        discretized_matrix = np.vstack((discrete_positions, discrete_times))

        # Il for è al contrario, va dall'ultimo elemento al primo per mantenere l'ordine stabilito del sistema
        for i in range(4,-1,-1):
            new_positions = None
            if np.isnan(self.fromPos[i]) and np.isnan(self.toPos[i]):
                new_positions = (np.linspace(self.fromPos[i], self.toPos[i], len(discrete_times)))
            elif not np.isnan(self.fromPos[i]) and not np.isnan(self.toPos[i]):
                new_positions = (np.linspace(self.fromPos[i], self.toPos[i], len(discrete_times))).astype(np.int64)
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
        else:
            num_rows = len(discrete_times_external)
            num_cols = 7
            large_matrix = np.full((num_rows, num_cols), np.nan)
            start_time = result[0, -1]  # ritorna il primo istante di tempo nella matrice piccola
            start_index = round((start_time - self.startTimePassed) / self.deltaT)
            large_matrix[start_index:start_index + result.shape[0], :] = result
            large_matrix[:, -1] = discrete_times_external
            return large_matrix, exists_cut_values

class SinusoidalMovement(Movement):
    # startTime, endTime in MILLISECONDS
    # amplitude in (0-100)
    # frequency in HZ
    # phase(or amplitude shift) in RADIANT (-1,1)
    # deltaT sampling period in SECONDS (periodo di campionamento in secondi) - 0.065
    # y_init starting point of the sinusoid on the y axis
    def __init__(self, startTime=None, endTime=None, deltaT=None, item=None):
        super().__init__(startTime, endTime)

        if item is None:
            raise TypeError("The 'item' parameter cannot be None")
        
        self.item = item
        self.values = item["values"] # values of the item (movement)  
        self.deltaT = deltaT
        self.flag = False
        self.startTime = int(self.values[0]) #take the start time from the item
        self.endTime = int(self.values[1]) #...
        
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


    def discretize(self):
        if all(var is None for var in [self.startTimePassed, self.endTimePassed, self.deltaT]):      
            self.deltaT = (int(self.values[8])) #take the deltaT from item (json) - to second
        elif all(var is not None for var in [self.startTimePassed, self.endTimePassed, self.deltaT]):
            self.deltaT = self.deltaT     
            self.flag = True      
        else:
            raise TypeError("All arguments must be null or all non-null")
        
        # Converte gli istanti di tempo da millisecondi a secondi per il calcolo
        #self.startTime = self.startTime / 1000
        #self.endTime = self.endTime / 1000

        # Genera un array di tempi da startTime a end_time con intervalli di deltaT(periodo di campionamento)
        t = np.arange(self.startTime, self.endTime+self.deltaT, self.deltaT)
        #t_millis = t*1000 #per l'output si usano i millisecondi
        #print(t_millis)

        t_external = None
        #t_millis_external = None
        if self.flag is True:
            #self.startTimePassed = self.startTimePassed / 1000
            #self.endTimePassed = self.endTimePassed / 1000

            t_external = np.arange(self.startTimePassed, self.endTimePassed+self.deltaT, self.deltaT)
            #t_millis_external = t_external*1000 #per l'output si usano i millisecondi

        #first element
        column1 = self.amplitude[5] * np.sin(2 * np.pi * self.frequency[5] * (t/1000) + (self.phase[5]*np.pi)) + self.y_init[5]
        y = np.vstack((column1,t)) 
        for i in range(4,-1,-1):
            
            # Calcola i valori della sinusoide
            # y è un array di valori che rappresentano l'ampiezza della sinusoide in corrispondenza di ciascun istante di tempo t
            # self.y_init è l'offset che permette all'utente di decidere su quale valore y iniziare
            column_i = self.amplitude[i] * np.sin(2 * np.pi * self.frequency[i] * (t/1000) + (self.phase[i]*np.pi)) + self.y_init[i] 
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
        else:
            num_rows = len(t_external)
            num_cols = 7
            large_matrix = np.full((num_rows, num_cols), np.nan)
            start_time = result[0, -1]  # ritorna il primo istante di tempo nella matrice piccola
            start_index = int((start_time - self.startTimePassed) / (self.deltaT)) #indice di partenza per posizionare la matrice piccola
            large_matrix[start_index:start_index + result.shape[0], :] = result
            large_matrix[:, -1] = t_external #metto gli istanti di tempo esterni
            return large_matrix, exists_cut_values



    
# item must be a list of dictionary (elements_in_tree_view)
class ComplexMovement(Movement):
        def __init__(self, startTime=None, endTime=None, deltaT=None, item=None):
            super().__init__(startTime, endTime)

            if item is None:
                raise TypeError("The 'item' parameter cannot be None")
            
            self.deltaT = deltaT
            self.item = item

        def discretize(self):
            if all(var is None for var in [self.startTimePassed, self.endTimePassed, self.deltaT]):    
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
                

                result =  np.full((rows, 7), np.nan)
                for submov in result_without_head_complex:
                    m2 = None
                    if submov['values'] == 'linear':
                        d = LinearMovement(t_start,t_end,deltaT,submov)
                        result = np.where(np.isnan(result), result, d)

            elif all(var is not None for var in [self.startTimePassed, self.endTimePassed, self.deltaT]):
                print("gestire")

            else:
                raise TypeError("All arguments must be null or all non-null")

            return None,None
            
            
