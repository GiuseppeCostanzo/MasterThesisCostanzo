#occhio al loop

def process_element(lst, index):
    # Base case: if index is out of bounds, return
    if index < 0 or index >= len(lst):
        return
    
    # Analizzare l'elemento corrente
    element = lst[index]
    print(f"Processing element at index {index}: {element}")
    
    # Condizione per fare backtrack sull'elemento precedente
    if element == 'backtrack':
        print(f"Backtracking from index {index}")
        process_element(lst, index - 1)  # Backtrack sull'elemento precedente
    else:
        print(f"Moving forward from index {index}")
        process_element(lst, index + 1)  # Vai all'elemento successivo

# Esempio di lista
lst = ['a', 'b', 'backtrack', 'c', 'backtrack', 'd']

# Iniziare il ciclo dalla posizione 0
process_element(lst, 0)

