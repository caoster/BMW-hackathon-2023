import json

part_1 = json.load(open("./model/part1.json"))
part_2 = json.load(open("./part2/greedy_out.json"))

result = part_1 | part_2

with open("./result.json", "w") as f:
    json.dump(result, f)
