import sys
import os

sys.path.append(os.path.abspath("../src"))


import subprocess
from primitives import Pool, POOLS

user = os.getenv("USER")
host = os.getenv("HOST")
port = os.getenv("PORT")
db = os.getenv("DB")
password = os.getenv("PASSWORD")

events = ["burns", "mints", "swaps"]
pools = [
    Pool(raw_pool["token0"], raw_pool["token1"], raw_pool["fee"]) for raw_pool in POOLS
]

for pool in pools:
    for event in events:
        name = f"{event}-{pool.name()}.csv"
        print(f"Exporting {name}")
        bashCommand = f'mysql -h {host} -u{user} -p{password} {db} -e \'select * from {event} WHERE pool="{pool.address()}" ORDER BY block_time\' | sed \'s/\\t/","/g;s/^/"/;s/$/"/;s/\\n//g\' > data/{name}'
        print(bashCommand)
        process = subprocess.Popen(["bash", "-c", bashCommand])
        process.wait()
        print(f"Finished exporting {name}")
