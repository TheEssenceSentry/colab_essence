{
  "nbformat": 4,
  "nbformat_minor": 0,
  "metadata": {
    "colab": {
      "name": "boilerplate.ipynb",
      "provenance": [],
      "collapsed_sections": [],
      "mount_file_id": "1QJFH_U4qF60OeRdE4R3Tlm9Uphkk8pXn",
      "authorship_tag": "ABX9TyP/O9VoIJPaD6gIE6s9O/s7",
      "include_colab_link": true
    },
    "kernelspec": {
      "name": "python3",
      "display_name": "Python 3"
    }
  },
  "cells": [
    {
      "cell_type": "markdown",
      "metadata": {
        "id": "view-in-github",
        "colab_type": "text"
      },
      "source": [
        "<a href=\"https://colab.research.google.com/github/TheEssenceSentry/colab_essence/blob/main/boilerplate.py\" target=\"_parent\"><img src=\"https://colab.research.google.com/assets/colab-badge.svg\" alt=\"Open In Colab\"/></a>"
      ]
    },
    {
      "cell_type": "code",
      "metadata": {
        "id": "xRCbuMxDsK7N"
      },
      "source": [
        "import os\n",
        "import re\n",
        "import urllib\n",
        "import hashlib as hl\n",
        "from urllib.request import urlopen\n",
        "from google.colab import drive\n",
        "\n",
        "\n",
        "\"\"\"\n",
        "file paths must start with \"/content/\",\n",
        "or be relative to \"/content/\",\n",
        "or be of the form f\"{DRIVE_PATH}subfolder\"\n",
        "\"\"\"\n",
        "\n",
        "\n",
        "DRIVE_PATH = \"/content/drive/My Drive/\"\n",
        "COLAB_PATH = f\"{DRIVE_PATH}Colab Notebooks/\"\n",
        "DATA_PATH = f\"{COLAB_PATH}data/\"\n",
        "KB, MB, GB = [2**(10*i) for i in (1, 2, 3)]\n",
        "\n",
        "\n",
        "def hash_file(file_location, hash_fns={\"MD5\": hl.md5, \"SHA1\": hl.sha1}, buffer_size=4*GB):\n",
        "    \"\"\"\n",
        "    Hash a file by default with MD5 and SHA1 and 4GB chunks\n",
        "    \"\"\"\n",
        "    hashes = [hash_fn() for hash_fn in hash_fns.values()]\n",
        "    with open(file_location, \"rb\") as f:\n",
        "        while True:\n",
        "            data = f.read(buffer_size)\n",
        "            if not data:\n",
        "                break\n",
        "            map(lambda h: h.update(data), hashes)\n",
        "        return dict(zip(hash_fns.keys(), map(lambda h: h.hexdigest().upper(), hashes)))\n",
        "\n",
        "\n",
        "def file_download_name(_url):\n",
        "    \"\"\"\n",
        "    Find the download name of a file from its URL\n",
        "    \"\"\"\n",
        "    _url = urlopen(_url).url\n",
        "    return os.path.basename(_url)\n",
        "\n",
        "\n",
        "def mount_drive(force=False):\n",
        "    \"\"\"\n",
        "    Mount Google Drive (prefer using the GUI if you can avoid this method)\n",
        "    \"\"\"\n",
        "    drive.mount(\"drive\", force_remount=force)\n",
        "\n",
        "\n",
        "def exists(file_location):\n",
        "    \"\"\"\n",
        "    Check the existance of a file\n",
        "    \"\"\"\n",
        "    try:\n",
        "        os.path.exists(file_location)\n",
        "    except:\n",
        "        raise ValueError(\"There is not a file in the specified location.\")\n",
        "\n",
        "\n",
        "def env_vars(vars=None, env_file_location=f\"{DRIVE_PATH}.env\"):\n",
        "    \"\"\"\n",
        "    Load requested enviroment variables from a given .env file\n",
        "    \"\"\"\n",
        "    exists(env_file_location)\n",
        "    prefix = \"\"\n",
        "    all_vars = dict()\n",
        "    with open(env_file_location, \"r\") as lines:\n",
        "        for line in lines:\n",
        "            if \"=\" in line:\n",
        "                if len(line.split(\"=\") == 2):\n",
        "                    name, val = line.split(\"=\")\n",
        "                    if prefix:\n",
        "                        name = f\"{prefix}_{name}\"\n",
        "                    all_vars.update({name: val})\n",
        "                else:\n",
        "                    raise ValueError(\"Variables have to be of the form NAME=VALUE\")\n",
        "            elif re.match(r\"^\\[\\w+\\]$\", line):\n",
        "                prefix = re.findall(r\"^\\[(\\w+)\\]$\", line)[0]\n",
        "            elif line == \"\":\n",
        "                prefix = \"\"\n",
        "            else:\n",
        "                pass\n",
        "    if all_vars:\n",
        "        vars = vars or all_vars\n",
        "        updated_vars = {(k, v) for (k, v) in all_vars.items() if k in vars}\n",
        "        try:\n",
        "            del all_vars\n",
        "        except:\n",
        "            pass\n",
        "        os.environ.update(updated_vars)\n",
        "        return updated_vars\n",
        "    else:\n",
        "        raise ValueError(\n",
        "            \"The file does not containt valid variables of the form NAME=VALUE\"\n",
        "        )\n",
        "\n",
        "\n",
        "def clone_repo(repo_name, secret=False, user=None):\n",
        "    \"\"\"\n",
        "    Clone a public or private GitHub repository\n",
        "    \"\"\"\n",
        "    if user == None:\n",
        "        env_vars([\"GITHUB_NAME\"])\n",
        "        user = os.environ[\"GITHUB_NAME\"]\n",
        "    if secret == True:\n",
        "        env_vars([\"GITHUB_PASSWORD\"])\n",
        "        password = f\":{urllib.parse.quote(os.environ['GITHUB_PASSWORD'])}\"\n",
        "    else:\n",
        "        password = \"\"\n",
        "    os.system(f\"git clone https://{user}{password}@github.com/{user}/{repo_name}.git\")\n",
        "    try:\n",
        "        del password\n",
        "        del os.environ[\"GITHUB_PASSWORD\"]\n",
        "    except:\n",
        "        pass\n",
        "    assert os.path.exists(f\"/content/{repo_name}\"), \"Error cloning the repository.\"\n",
        "    return f\"/content/{repo_name}\"\n",
        "\n",
        "\n",
        "def download(url, load_cookies=False, save_cookies=False):\n",
        "    \"\"\"\n",
        "    Download a file from a URL\n",
        "    Save or load cookies for more involved downloads\n",
        "    \"\"\"\n",
        "    file_name = file_download_name(url)\n",
        "    cookies = \"\"\n",
        "    if save_cookies:\n",
        "        cookies = \"--save-cookies /tmp/cookies.txt --keep-session-cookies\"\n",
        "    elif load_cookies:\n",
        "        cookies = \"--load-cookies /tmp/cookies.txt\"\n",
        "    os.system(f\"wget -c {cookies} '{url}'\")\n",
        "    return file_name\n",
        "\n",
        "\n",
        "def uncompress(file_location):\n",
        "    \"\"\"\n",
        "    Extract compressed files (.zip, .tar, .tar.gz, .tar.bz2, .tar.lz, .tar.lzma,\n",
        "    .tar.xz)\n",
        "    \"\"\"\n",
        "    if \"/\" in file_location:\n",
        "        file_name = file_location.split(\"/\")[-1]\n",
        "        origin = \"/\".join(file_location.split(\"/\")[:-1])\n",
        "    else:\n",
        "        file_name = file_location\n",
        "        origin = \"/content\"\n",
        "    filters = {\n",
        "        \"gz\": \"--gzip\",\n",
        "        \"bz2\": \"--bzip2\",\n",
        "        \"lz\": \"--lzip\",\n",
        "        \"lzma\": \"--lzma\",\n",
        "        \"xz\": \"--xz\",\n",
        "    }\n",
        "    ext = file_name.split(\".\")[-1]\n",
        "    if ext == \"zip\":\n",
        "        base = \" \".join(file_name.split(\".\")[:-1])\n",
        "        command = f\"unzip '{origin}/{file_name}' -d '/content/{base}'\"\n",
        "    if ext == \"tar\":\n",
        "        base = \" \".join(file_name.split(\".\")[:-1])\n",
        "        command = (\n",
        "            f\"tar --get --file='{origin}/{file_name}' --directory='/content/{base}'\"\n",
        "        )\n",
        "    elif file_name.split(\".\")[-2] == \"tar\" and ext in filters:\n",
        "        base = \" \".join(file_name.split(\".\")[:-2])\n",
        "        command = f\"tar --get {filters[ext]} --file='{origin}/{file_name}' --directory='/content/{base}'\"\n",
        "    else:\n",
        "        raise ValueError(\"Cannot uncompress the file.\")\n",
        "    command = f\"mkdir -p '/content/{base}'; {command}\"\n",
        "    os.system(command)\n",
        "\n",
        "\n",
        "def github_id():\n",
        "    \"\"\"\n",
        "    Identify yourself to GitHub\n",
        "    \"\"\"\n",
        "    env_vars([\"GITHUB_NAME\", \"GITHUB_EMAIL\"])\n",
        "    os.system(f\"git config --global user.email {os.environ['GITHUB_EMAIL']}\")\n",
        "    os.system(f\"git config --global user.name {os.environ['GITHUB_NAME']}\")\n",
        "\n",
        "\n",
        "def drive_link_to_id(link):\n",
        "    \"\"\"\n",
        "    Extract the link id string from different possible link formats\n",
        "    \"\"\"\n",
        "    if \"drive.google.com\" in link:\n",
        "        id = re.findall(r\"\\/file\\/d\\/(\\w+)\", link)[0]\n",
        "    elif \"docs.google.com\" in link:\n",
        "        id = re.findall(r\"\\Wid=(\\w+)\", link)[0]\n",
        "    elif len(re.findall(r\"\\w{33}\", link)) == 33:\n",
        "        id = re.findall(r\"(\\w{33})\", link)[0]\n",
        "    elif len(link) == 33 and re.match(r\"^\\w+$\", link):\n",
        "        id = link\n",
        "    return id\n",
        "\n",
        "\n",
        "def big_drive_file(link, calculate_hash=False):\n",
        "    \"\"\"\n",
        "    download Google Drive files (publicly shared with a link) that cannot be\n",
        "    downloaded directly without confirmation because of their size (Google does\n",
        "    not perform antivirus analysis on them)\n",
        "    \"\"\"\n",
        "    id = drive_link_to_id(link)\n",
        "    temp = download(\n",
        "        f\"https://docs.google.com/uc?export=download&id={id}\", save_cookies=True\n",
        "    )\n",
        "    with open(temp, \"r\") as t:\n",
        "        content = t.read()\n",
        "    code = re.findall(r\"confirm=(\\w+)\", content)[0]\n",
        "    file_name = re.findall(r\"docs.google.com\\/open\\?id\\=\\w+\\\">([^<]+)</a>\", content)[0]\n",
        "    file = download(\n",
        "        f\"https://docs.google.com/uc?export=download&confirm={code}&id={id}\",\n",
        "        load_cookies=True,\n",
        "    )\n",
        "    os.system(f\"mv '{file}' '{file_name}'\")\n",
        "    os.system(f\"rm '/tmp/cookies.txt' '{temp}'\")\n",
        "    print(hash_file(file_name))\n",
        "    return file_name\n",
        "\n",
        "\n",
        "def to_drive(file_location, path=\"\"):\n",
        "    \"\"\"\n",
        "    Move file from the local Colaboratory hard disk to your Google Drive storage\n",
        "    \"\"\"\n",
        "    path = f\"{DRIVE_PATH}{path}\"\n",
        "    file_name = file_location.split(\"/\")[-1]\n",
        "    if file.startswith(\"/content/\"):\n",
        "        os.system(f\"cp '{file}' '{path}{file_name}'\")\n",
        "    else:\n",
        "        os.system(f\"cp '/content/{file}' '{path}{file_name}'\")\n"
      ],
      "execution_count": 2,
      "outputs": []
    }
  ]
}