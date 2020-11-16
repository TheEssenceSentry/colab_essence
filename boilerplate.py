import os
import re
import random
import string
import urllib
import requests
import hashlib as hl
from urllib.request import urlopen
from google.colab import drive
import ast

"""
File paths must start with "/content/",
or be relative to "/content/",
or be of the form f"{DRIVE_PATH}subfolder"
"""

# Maybe use pathlib?
DRIVE_PATH = "/content/drive/My Drive/"
COLAB_PATH = f"{DRIVE_PATH}Colab Notebooks/"
DATA_PATH = f"{COLAB_PATH}data/"
KB, MB, GB = [2**(10*i) for i in (1, 2, 3)]


def hash_file(file_location, hash_fns={"MD5": hl.md5, "SHA1": hl.sha1}, buffer_size=4*GB):
    """
    Hash a file by default with MD5 and SHA1 and 4GB chunks.
    """
    hashes = [hash_fn() for hash_fn in hash_fns.values()]
    with open(file_location, "rb") as f:
        while True:
            data = f.read(buffer_size)
            if not data:
                break
            map(lambda h: h.update(data), hashes)
        return dict(zip(hash_fns.keys(), map(lambda h: h.hexdigest().upper(), hashes)))


def file_download_name(_url):
    """
    Find the download name of a file from its URL.
    """
    _url = urlopen(_url).url
    return os.path.basename(_url)


def mount_drive(force=False):
    """
    Mount Google Drive (prefer using the GUI if you can avoid this method).
    """
    drive.mount("drive", force_remount=force)


def exists(file_location):
    """
    Check the existence of a file.
    """
    try:
        os.path.exists(file_location)
    except:
        raise ValueError("There is not a file in the specified location.")


def env_vars(*vars, set_environ=False, env_file_location=f"{DRIVE_PATH}.env"):
    """
    Load requested enviroment variables from a given .env file.
    """
    exists(env_file_location)
    prefix = ""
    all_vars = dict()
    with open(env_file_location, "r") as lines:
        for line in lines:
            if not line.startswith("#") and "=" in line:
                line_splits = line.strip("\n").split("=")
                name, val = line_splits[0], "".join(line_splits[1:])
                if prefix:
                    name = f"{prefix}_{name}"
                all_vars.update({name: val})
            elif re.match(r"^\[\w+\]$", line):
                prefix = re.findall(r"^\[(\w+)\]$", line)[0]
            elif re.match(r"^\s*$", line):
                prefix = ""
            else:
                pass
    vars = vars or all_vars
    updated_vars = {k: v for (k, v) in all_vars.items() if k in vars}
    updated_values = list(updated_vars.values())
    if not updated_values:
        raise ValueError(
            "The variables could not be parsed, check if they are in the form VAR=VALUE"
        )
    if set_environ:
        os.environ.update(updated_vars)
    if len(updated_values) == 1:
        return updated_values[0]
    else:
        return updated_values


def clone_repo(repo_name, secret=False, user=None):
    """
    Clone a public or private GitHub repository.
    """
    if user == None:
        user = env_vars("GITHUB_NAME", set_environ=True)
    if secret == True:
        password = f":{urllib.parse.quote(env_vars('GITHUB_PASSWORD'))}"
    else:
        password = ""
    os.system(f"git clone https://{user}{password}@github.com/{user}/{repo_name}.git")
    assert os.path.exists(f"/content/{repo_name}"), "Error cloning the repository."
    return f"/content/{repo_name}"


def download(url, load_cookies=False, save_cookies=False):
    """
    Download a file from a URL.
    Save or load cookies for more involved downloads.
    """
    file_name = file_download_name(url)
    cookies = ""
    if save_cookies:
        cookies = "--save-cookies /tmp/cookies.txt --keep-session-cookies"
    elif load_cookies:
        cookies = "--load-cookies /tmp/cookies.txt"
    os.system(f"wget -c {cookies} '{url}'")
    return file_name


def uncompress(file_location):
    """
    Extract compressed files (.zip, .tar, .tar.gz, .tar.bz2, .tar.lz, .tar.lzma,
    .tar.xz).
    """
    if "/" in file_location:
        file_name = file_location.split("/")[-1]
        origin = "/".join(file_location.split("/")[:-1])
    else:
        file_name = file_location
        origin = "/content"
    filters = {
        "gz": "--gzip",
        "bz2": "--bzip2",
        "lz": "--lzip",
        "lzma": "--lzma",
        "xz": "--xz",
    }
    ext = file_name.split(".")[-1]
    if ext == "zip":
        base = " ".join(file_name.split(".")[:-1])
        command = f"unzip '{origin}/{file_name}' -d '/content/{base}'"
    if ext == "tar":
        base = " ".join(file_name.split(".")[:-1])
        command = (
            f"tar --get --file='{origin}/{file_name}' --directory='/content/{base}'"
        )
    elif file_name.split(".")[-2] == "tar" and ext in filters:
        base = " ".join(file_name.split(".")[:-2])
        command = f"tar --get {filters[ext]} --file='{origin}/{file_name}' --directory='/content/{base}'"
    else:
        raise ValueError("Cannot uncompress the file.")
    command = f"mkdir -p '/content/{base}'; {command}"
    os.system(command)


def generate_temp_password(
    length=32, symbols_weights={"lowercase": 5, "uppercase": 2, "digits": 2, "symbols": 1}
):
    symbols = {
        "lowercase": string.ascii_lowercase,
        "uppercase": string.ascii_uppercase,
        "digits": string.digits,
        "symbols": "#$%&\*+,-./:;<=>?@^_~",
    }
    return "".join(
        random.choice("".join(symbols_weights[s] * symbols[s] for s in symbols.keys()))
        for i in range(length)
    )


def github_id():
    """
    Identify yourself to GitHub.
    """
    env_vars("GITHUB_NAME", "GITHUB_EMAIL", set_environ=True)
    os.system(f"git config --global user.email {os.environ['GITHUB_EMAIL']}")
    os.system(f"git config --global user.name {os.environ['GITHUB_NAME']}")


def drive_link_to_id(link):
    """
    Extract the download link id string from different possible formats.
    """
    if "drive.google.com" in link:
        id = re.findall(r"\/file\/d\/(\w+)", link)[0]
    elif "docs.google.com" in link:
        id = re.findall(r"\Wid=(\w+)", link)[0]
    elif len(re.findall(r"\w{33}", link)) == 33:
        id = re.findall(r"(\w{33})", link)[0]
    elif len(link) == 33 and re.match(r"^\w+$", link):
        id = link
    return id


def big_drive_file(link, calculate_hash=False):
    """
    Download Google Drive files (publicly shared with a link) that cannot be
    downloaded directly without confirmation because of their size (Google does
    not perform antivirus analysis on them).
    """
    id = drive_link_to_id(link)
    temp = download(
        f"https://docs.google.com/uc?export=download&id={id}", save_cookies=True
    )
    with open(temp, "r") as t:
        content = t.read()
    code = re.findall(r"confirm=(\w+)", content)[0]
    file_name = re.findall(r"docs.google.com\/open\?id\=\w+\">([^<]+)</a>", content)[0]
    file = download(
        f"https://docs.google.com/uc?export=download&confirm={code}&id={id}",
        load_cookies=True,
    )
    os.system(f"mv '{file}' '{file_name}'")
    os.system(f"rm '/tmp/cookies.txt' '{temp}'")
    print(hash_file(file_name))
    return file_name


def to_drive(file_location, path=""):
    """
    Move file from the local Colaboratory hard disk to your Google Drive storage.
    """
    path = f"{DRIVE_PATH}{path}"
    file_name = file_location.split("/")[-1]
    if file.startswith("/content/"):
        os.system(f"cp '{file}' '{path}{file_name}'")
    else:
        os.system(f"cp '/content/{file}' '{path}{file_name}'")


def partial(func, *args, **kwargs):
    # Just use functools.partial
    def f(*f_args, **f_kwargs):
        return func(*(args + f_args), **{**kwargs, **f_kwargs})
    return f


def curry(func):
    """
    Create a curried version of a function that returns as soon as all the
    required arguments are passed.
    """
    def curried(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except TypeError:
            return curry(partial(func, *args, **kwargs))
    return curried


def F(expr):
    """
    Given an expression as a string, it returns a curried function that when 
    passed the needed arguments in alphabetical order, returns the result of the
    expression. Any variable used in the expression is a local argument of the 
    function, unless the variable is in the global scope.
    """
    _ast = ast.dump(ast.parse(expr))
    vars = sorted(list(set(v for v in re.findall(r"id='([\w_-]+)'", _ast) if v not in globals()))) or ["*args"]
    return curry(eval(f"lambda {', '.join(vars)}: {expr}"))

def install_dependencies():
    """
    Install some dependencies needed to run Visual Studio Code.
    """
    print("Installing dependencies...")
    os.system("apt install --yes ssh screen nano htop ranger git > /dev/null")
    os.system("wget -q -c -nc https://bin.equinox.io/c/4VmDzA7iaHb/ngrok-stable-linux-amd64.zip")
    os.system("unzip -qq -n ngrok-stable-linux-amd64.zip")


def setting_vscode():
    print("Setting Visual Studio Code server...")
    os.system("mkdir -p '/content/drive/My Drive/Colab Notebooks/root/.local/share/code-server'")
    os.system("ln -s '/content/drive/My Drive/Colab Notebooks' /")
    os.system("ln -s '/content/drive/My Drive/Colab Notebooks/root/.local/share/code-server' '/root/.local/share/'")
    os.system("curl -fsSL https://code-server.dev/install.sh | sh > /dev/null")


def setting_ssh(password):
    """
    Create a SSH connection to the Colab runtime.
    """
    print("Setting SSH connection to the Colab runtime...")
    os.system(f"echo 'root:{password}' | chpasswd")
    os.system("echo 'PasswordAuthentication yes' > /etc/ssh/sshd_config")
    os.system("echo 'PermitUserEnvironment yes' >> /etc/ssh/sshd_config")
    os.system("echo 'PermitRootLogin yes' >> /etc/ssh/sshd_config")
    os.system("service ssh restart > /dev/null")


def setting_ngrok():
    """
    Create a TCP connection using NGROK.
    """
    print("Creating TCP connection using NGROK...")
    authtoken = env_vars("NGROK_AUTHTOKEN")
    os.system(f"./ngrok authtoken '{authtoken}' && ./ngrok tcp 22 &")
    os.system("sleep 3")


def get_ssh_connection():
    """
    Get the SSH address to connect to the Visual Studio Code server instance.
    """
    print("Getting SSH address to server instance...")
    r = requests.get('http://localhost:4040/api/tunnels')
    str_ssh = r.json()['tunnels'][0]['public_url']
    str_ssh = str_ssh.replace("tcp://", "")
    str_ssh = str_ssh.replace(":", " -p ")
    str_ssh = f"ssh -L 9999:localhost:9999 root@{str_ssh}"
    print()
    print("SSH:", str_ssh)


def run_vscode():
    """
    Prepare the environment and run Visual Studio Code.
    Execute the SHH command in a terminal and open http://127.0.0.1:9999/
    in a browser tab.
    """
    install_dependencies()
    setting_vscode()
    try:
        password = env_vars("SSH_PASSWORD")
    except:
        password = generate_temp_password()
    setting_ssh(password)
    setting_ngrok()
    get_ssh_connection()
    print("Password:", password)
    print("Open http://127.0.0.1:9999/")
    os.system("code-server --bind-addr 127.0.0.1:9999 --auth none &")

#run_vscode()

os.system("pip3 install jupyter-tabnine")

from jupyter_tabnine import __file__ as f, _jupyter_nbextension_paths as n

entrypoint = os.path.normpath(os.path.join(os.path.dirname(f), n()[0]['src']))
os.system(f"jupyter nbextension install '{entrypoint}'")
os.system("jupyter nbextension enable static/main")

#TODO 
# Visualization recommender system. 
# See what other self-hosted services can be added.
# Improve download (local file system, Google Sheet, SQL, BigQuery)
# Add numpy, Sympy, LaTeX alternatives to F
# What about transformational programming like Bird-Meertens
# Ask or generate password if not present in .env file
# Input widgets for all functions
# Boilerplate for TPUs
# Keras + FastAI
# Original Jupyter
# Wrapping for mobile devices with text transformation and extra imput row.
# Try improving the autocompletion using Tabnine or Kite
# Add auto formatting, refactoring, debugging, profiling utilities
# Add property based testing with Hypothesis
