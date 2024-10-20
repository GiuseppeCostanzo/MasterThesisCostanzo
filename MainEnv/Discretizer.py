import numpy as np
from abc import ABC, abstractmethod
from Utility import Toolbox

# Abstract father class
class Movement(ABC):
    def __init__(self, startTime, endTime):
        self.startTimePassed = startTime
        self.endTimePassed = endTime

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
        if all(var is None for var in [self.startTimePassed, self.endTimePassed, self.deltaT]):      
            self.deltaT = int(self.values[2]) #take the deltaT from item (json)   
        elif all(var is not None for var in [self.startTimePassed, self.endTimePassed, self.deltaT]):
            self.flag = True
        else:
            raise TypeError("All arguments must be null or all non-null")

        # Generates an array of times from startTime to end_time with deltaT intervals (sampling period)
        discrete_times = np.arange(self.startTime, self.endTime+self.deltaT, self.deltaT)
        discrete_times_external = None
        if self.flag is True:
            discrete_times_external = np.arange(self.startTimePassed, self.endTimePassed+self.deltaT, self.deltaT)
        discrete_positions = None 
        if np.isnan(self.fromPos[5]) and np.isnan(self.toPos[5]):
            discrete_positions = (np.linspace(self.fromPos[5], self.toPos[5], len(discrete_times)))
        elif not np.isnan(self.fromPos[5]) and not np.isnan(self.toPos[5]):
            discrete_positions = (np.linspace(self.fromPos[5], self.toPos[5], len(discrete_times))).astype(np.int64)
        else:
            raise ValueError("Error in LinearDiscretize. fromPos and toPos must both be nan or both not NaN")
        # Stack arrays
        discretized_matrix = np.vstack((discrete_positions, discrete_times))

        # The for is in reverse, it goes from the last element to the first to maintain the established order
        for i in range(4,-1,-1):
            new_positions = None
            if np.isnan(self.fromPos[i]) and np.isnan(self.toPos[i]):
                new_positions = (np.linspace(self.fromPos[i], self.toPos[i], len(discrete_times)))
            elif not np.isnan(self.fromPos[i]) and not np.isnan(self.toPos[i]):
                new_positions = (np.linspace(self.fromPos[i], self.toPos[i], len(discrete_times))).astype(np.int64)
            else:
                raise ValueError("Error in LinearDiscretize. fromPos and toPos must both be nan or both not NaN")          
            # Stack arrays
            discretized_matrix = np.vstack((new_positions,discretized_matrix))
        result = discretized_matrix.T

        # exists_cut_values is a boolean flag for the warning in the gui
        exists_cut_values = False
        exists_cut_values = any((val > 100 or val < 0) for row in result for val in row[:-1])
        # clip values >100 and <0
        if exists_cut_values:
            result[:, :-1] = np.clip(result[:, :-1], 0, 100)

        if self.flag is False:
            # Replacing NaN with 50 if the function was directly called from the GUI (and thus we are not in a 
            # context of a more external complex movement)
            result = np.nan_to_num(result, nan=50)
            result = result.astype(np.int64)
            return result, exists_cut_values
        
        else:
            num_rows = len(discrete_times_external)
            num_cols = 7
            large_matrix = np.full((num_rows, num_cols), np.nan)
            start_time = result[0, -1]  # returns the first instant of time in the small matrix
            start_index = int((start_time - self.startTimePassed) / self.deltaT)
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
                temp.append(float(self.values[i][1]))
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
        t = np.arange(self.startTime, self.endTime+self.deltaT, self.deltaT)
        t_external = None
        if self.flag is True:
            t_external = np.arange(self.startTimePassed, self.endTimePassed+self.deltaT, self.deltaT)
        column1 = self.amplitude[5] * np.sin(2 * np.pi * self.frequency[5] * (t/1000) + (self.phase[5]*np.pi)) + self.y_init[5]
        y = np.vstack((column1,t)) 
        for i in range(4,-1,-1):        
            # Calculates the values of the sine wave
            column_i = self.amplitude[i] * np.sin(2 * np.pi * self.frequency[i] * (t/1000) + (self.phase[i]*np.pi)) + self.y_init[i] 
            y = np.vstack((column_i,y))
        result = y.T
        exists_cut_values = False
        exists_cut_values = any((val > 100 or val < 0) for row in result for val in row[:-1])
        # clip values >100 and <0
        if exists_cut_values:
            result[:, :-1] = np.clip(result[:, :-1], 0, 100)

        if self.flag is False:
            result = np.nan_to_num(result, nan=50)
            result = result.astype(np.int64)
            return result, exists_cut_values
        else:
            num_rows = len(t_external)
            num_cols = 7
            large_matrix = np.full((num_rows, num_cols), np.nan)
            start_time = result[0, -1] 
            start_index = int((start_time - self.startTimePassed) / (self.deltaT)) 
            large_matrix[start_index:start_index + result.shape[0], :] = result
            large_matrix[:, -1] = t_external 
            return large_matrix, exists_cut_values

    
# item must be a list of dictionary (elements_in_tree_view)
class ComplexMovement(Movement):
        def __init__(self, item=None):

            if item is None:
                raise TypeError("The 'item' parameter cannot be None")
            
            self.item = item

        def discretize(self):  

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
            
            discrete_times_external = np.arange(t_start, t_end+deltaT, deltaT)
            result =  np.full((len(discrete_times_external), 7), np.nan)
            result[:, -1] = discrete_times_external
            flag_cut = False
            for submov in result_without_head_complex:
                if submov['type'] == 'linear':
                    d = LinearMovement(t_start,t_end,deltaT,submov)
                    sub_matrix,flag_return = d.discretize()
                    result = np.where(np.isnan(sub_matrix), result, sub_matrix)
                    if flag_return is True:
                        flag_cut = True
                if submov['type'] == 'sinusoidal':
                    d = SinusoidalMovement(t_start,t_end,deltaT,submov)
                    sub_matrix,flag_return = d.discretize()
                    result = np.where(np.isnan(sub_matrix), result, sub_matrix)
                    if flag_return is True:
                        flag_cut = True

            #If the first row of the final matrix contains any nans, it is replaced with a rest value of 50
            result[0, :] = np.where(np.isnan(result[0, :]), 50, result[0, :])
            # Replace the NaN values ​​with the last non-Nan value
            for i in range(1, result.shape[0]):  
                for j in range(result.shape[1]):  
                    if np.isnan(result[i, j]):  
                        result[i, j] = result[i-1, j]  
            return result.astype(np.int64), flag_cut


            
            
