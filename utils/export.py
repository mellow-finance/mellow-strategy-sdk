import os
import subprocess

user = os.getenv("USER")
host = os.getenv("HOST")
port = os.getenv("PORT")
db = os.getenv("DB")
password = os.getenv("PASSWORD")

pools = {
    "ETHUSDC": "0x8ad599c3A0ff1De082011EFDDc58f1908eb6e6D8",
    "ETHWBTC": "0x7858E59e0C01EA06Df3aF3D20aC7B0003275D4Bf",
}

events = ["burns", "mints", "swaps"]

for pool, address in pools.items():
    for event in events:
        name = f"{event}-{pool}.csv"
        print(f"Exporting {name}")
        bashCommand = f'mysql -h {host} -u{user} -p{password} {db} -e \'select * from {event} WHERE pool="{address}"\' | sed \'s/\\t/","/g;s/^/"/;s/$/"/;s/\\n//g\' > data/{name}'
        print(bashCommand)
        process = subprocess.Popen(["bash", "-c", bashCommand])
        process.wait()
        print(f"Finished exporting {name}")
