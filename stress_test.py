import argparse
import subprocess

langs = {
    'python': 'python client.py --host %s --port %s --name %s',
    'node': 'node node-client/client.js --host %s --port %s --name %s',
    'java': 'java java-client/Client.java --host %s --port %s --name %s',
    'go': 'go run go-client/main.go --host %s --port %s --name %s',
    'dotnet': 'cd csharp-client && dotnet run -- --host %s --port %s --name %s',
    'rust': 'cd rust-client && cargo run -- --host %s --port %s --name %s',
}


parser = argparse.ArgumentParser(prog="Stress test", description="Sends multiple requests quickly to the server")
parser.add_argument("-l", "--language", help="Sets client language. Python by default", default="python")
parser.add_argument("-i", "--ip", help="Server ip", required=True)
parser.add_argument("-p", "--port", help="Server port", default=5001)
parser.add_argument("-u", "--user", help="Client username", default="test")
parser.add_argument("-a", "--attempts", help="No. of requests to send", default=1)

args = parser.parse_args()

if args.language.lower() in langs.keys():
    for i in range(int(args.attempts)):
        subprocess.run((langs[args.language.lower()] % (args.ip, args.port, args.user)).split())
else:
    print("Invalid Language")

