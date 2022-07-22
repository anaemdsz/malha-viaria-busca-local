from pickletools import optimize
from pprint import pprint
from datetime import datetime, timedelta
from yaml import parse


#filenames = ['./len_output_chape.txt', './len_output_ufsc.txt', './len_output_nash.txt']
filenames = ['./nash_villeoutput.txt']

parsed_data = {}
for name in filenames:
    with open(name) as file:
        for line in file:
            if "Analyzing" in line:
                key = line.split(' ')[1].split('::')
                starting_time = line.split(' : ')[1].strip()
                if key[0] not in parsed_data:
                    parsed_data[key[0]] = {}
                if key[1] not in parsed_data[key[0]]:
                    parsed_data[key[0]][key[1]] = {}
                if key[2] not in parsed_data[key[0]][key[1]]:
                    parsed_data[key[0]][key[1]][key[2]] = {}
                parsed_data[key[0]][key[1]][key[2]]['changes'] = 0
                parsed_data[key[0]][key[1]][key[2]]['initial_time'] = starting_time

            elif "Nodes" in line:
                node_amt = line.split(' ')[1].strip()
                parsed_data[key[0]][key[1]][key[2]]['nodes'] = int(node_amt)

            elif "Edges" in line:
                edge_amt = line.split(' ')[1].strip()
                parsed_data[key[0]][key[1]][key[2]]['edges'] = int(edge_amt)

            elif "Starting" in line:
                starting_density = line.split('=')[1].strip()
                parsed_data[key[0]][key[1]][key[2]]['starter_density'] = starting_density[:-1]
            
            elif " lane" in line:
                parsed_data[key[0]][key[1]][key[2]]['changes'] = parsed_data[key[0]][key[1]][key[2]]['changes']+1
            
            elif "Budget remaining" in line:
                parsed_data[key[0]][key[1]][key[2]]['budget_left'] = float(line.split(': ')[1].strip()[:-1])
            
            elif 'Best possible' in line:
                parsed_data[key[0]][key[1]][key[2]]['optimized_density'] = line.split(': ')[1].strip()[:-1]

            elif 'Finished' in line:
                end_time = line.split(' : ')[1].strip()
                parsed_data[key[0]][key[1]][key[2]]['end_time'] = end_time

                elapsed_time = datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S.%f') - datetime.strptime(parsed_data[key[0]][key[1]][key[2]]['initial_time'], '%Y-%m-%d %H:%M:%S.%f')
                parsed_data[key[0]][key[1]][key[2]]['elapsed_time'] = elapsed_time

pprint(parsed_data)

with open("./table.tex", "w") as f:
    for entry in parsed_data:
        print(entry)
        f.write(f'\\begin{{table}}[ht]\n\\caption\u007b{entry}\u007d\n\\centering\n')
        f.write(f'\\begin{{tabular}}{{@{{}}c c@{{}}}}\n\t\\toprule\n\t{{\\bfseries Issue-Id}} & {{\\bfseries Summary}} \\\\\n\t\\midrule\n\t')
        f.write(f"\\\\ \n\t".join([f"{_k} & {_v}" for _k, _v in sorted(parsed_data[entry].items())]))
        f.write(f'\\\\\n\t\\bottomrule\n\\end{{tabular}}\n\\label{{table:nonlin}}\n\\end{{table}}\n\n')