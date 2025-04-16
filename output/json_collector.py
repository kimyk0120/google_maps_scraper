# json 파일의 객체들을 한 json 파일로 모은다.

import glob
import json

# JSON 파일 경로 패턴
json_filse_paths = ["./result/*/json/*.json"]

json_files = []

for pattern in json_filse_paths:
    json_files.extend(glob.glob(pattern))

print(f'json file len : {len(json_files)}')

raw_json_data_list = []
for json_file in json_files:
    with open(json_file, 'r', encoding='utf-8') as f:
        raw_json_data_list.append(json.load(f))

# json 파일로 쓰기
with open('./output.json', 'w', encoding='utf-8') as f:
    json.dump(raw_json_data_list, f, ensure_ascii=False, indent=4)


print("fin")