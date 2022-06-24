x, y, i = [0, 0, 0]
new = []
with open("borá_edgelist.tsv") as file:
    for line in file:
        _line = line.split(' ')
        print(_line)