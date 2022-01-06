import re

def load_labels(path_to_labels):
    labels = {}
    index = 1
    
    with open(path_to_labels, 'r') as File:
        file = File.readlines() #Reading all the lines from File
        if not re.split(r'[\s\,]+', file[0])[0].isnumeric():
            index = 1
            for line in file: #Reading line-by-line
                labels[index] = line.strip()
                index = index + 1
        else:
            for line in file: #Reading line-by-line
                words = re.split(r'[\s\,]+', line) #Splitting lines in words using space or comma character as separator
                labels[int(words[0])] = words[1]
    return labels