import sys
import os

root = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(root)


import subprocess
from strategy.primitives import Pool, POOLS

user = os.getenv("USER")
host = os.getenv("HOST")
port = os.getenv("PORT")
db = os.getenv("DB")
password = os.getenv("PASSWORD")

events = ["burn", "mint", "swap"]
pools = [
    Pool(raw_pool["token0"], raw_pool["token1"], raw_pool["fee"]) for raw_pool in POOLS
]

for pool in pools:
    for event in events:
        name = f"{event}-{pool.name}.csv"
        print(f"Exporting {name}")
        bashCommand = f'mysql -h {host} -u{user} -p{password} {db} -e \'select * from {event} WHERE pool="{pool.address}" ORDER BY block_time\' | sed \'s/\\t/","/g;s/^/"/;s/$/"/;s/\\n//g\' > {root}/scripts/data/{name}'
        print(bashCommand)
        process = subprocess.Popen(["bash", "-c", bashCommand])
        process.wait()
        print(f"Finished exporting {name}")
