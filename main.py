#!/usr/bin/env python3
"""
Collected-DBs - Uma ferramenta avançada para coleta de informações e bancos de dados de websites
Desenvolvido para uso otimizado no Termux (Android) sem necessidade de root

GitHub: https://github.com/sentinelzxofc/collected-dbs
Instagram: @sentinelzxofc

AVISO LEGAL: Esta ferramenta foi criada apenas para fins educacionais e de teste.
O autor não se responsabiliza pelo uso indevido desta ferramenta.
LEGAL DISCLAIMER: This tool is intended for educational and testing purposes only.
The author is not responsible for any misuse of this tool.
"""
import os
import sys
import time
import random
import requests
import threading
import subprocess
import json
import re
import signal
import gzip
import tarfile
import zipfile
import sqlite3
import csv
import yaml
from datetime import datetime
from urllib.parse import urlparse, urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed
from socket import socket, AF_INET, SOCK_STREAM
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from binascii import hexlify
try:
    from bs4 import BeautifulSoup
except ImportError:
    print("Erro: Biblioteca BeautifulSoup4 não encontrada. Execute: pkg install python && pip install beautifulsoup4")
    sys.exit(1)
try:
    from tqdm import tqdm
except ImportError:
    print("Erro: Biblioteca tqdm não encontrada. Execute: pip install tqdm")
    sys.exit(1)
try:
    from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
except ImportError:
    print("Erro: Biblioteca tenacity não encontrada. Execute: pip install tenacity")
    sys.exit(1)
try:
    import yaml
except ImportError:
    print("Erro: Biblioteca pyyaml não encontrada. Execute: pip install pyyaml")
    sys.exit(1)

VERSION = "3.5.0"
MAX_THREADS = min(10, os.cpu_count() * 2 or 8)
REQUEST_TIMEOUT = 20
USER_AGENTS = [
    "Mozilla/5.0 (Linux; Android 14; SM-G998B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.6668.81 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:131.0) Gecko/20100101 Firefox/131.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_7_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Safari/605.1.15"
]
DB_PATHS = [
    "/.env", "/.env.bak", "/.env.dev", "/.env.local", "/.env.prod", "/.env.save",
    "/env", "/config/env", "/backups/env",
    "/config.php", "/wp-config.php", "/wp-config.php.bak", "/configuration.php",
    "/settings.php", "/local.xml", "/config.json", "/config.yml", "/database.yml",
    "/app/config/parameters.yml", "/app/etc/env.php", "/WEB-INF/web.xml",
    "/secrets.json", "/secrets.yml", "/credentials.json", "/credentials.yml",
    "/docker-compose.yml", "/docker-compose.override.yml",
    "/backup.sql", "/database.sql", "/dump.sql", "/data.sql", "/db.sql", "/site.sql",
    "/mysql.sql", "/pgsql.sql", "/sqlite.sql", "/dbdump.sql", "/full_backup.sql",
    "/backups/full_backup.sql", "/sql/full_backup.sql", "/database/full_backup.sql",
    "/sql/backup.sql", "/sql/database.sql", "/sql/export.sql", "/archive/backup.sql",
    "/db/full_backup.sql", "/admin/backups/database.sql", "/backups/database.sql",
    "/data/backup.sql", "/export/database.sql", "/admin/dump.sql",
    "/backup.sql.gz", "/database.sql.gz", "/dump.sql.gz", "/data.sql.gz",
    "/backup.sql.zip", "/database.sql.zip", "/dump.sql.zip", "/data.sql.zip",
    "/backup.sql.tar.gz", "/database.sql.tar.gz", "/dump.sql.tar.gz",
    "/backup.sql.tar", "/database.sql.tar", "/dump.sql.tar",
    "/backup.db", "/database.db", "/site.db", "/database.sqlite", "/app.db",
    "/backup.bak", "/database.bak", "/dump.bak", "/site.bak",
    "/backup.csv", "/users.csv", "/customers.csv", "/orders.csv",
    "/backup.json", "/database.json", "/users.json", "/customers.json",
    "/backup.xml", "/database.xml", "/users.xml", "/orders.xml",
    "/private.key", "/id_rsa", "/secret_key", "/api_key",
    "/backup/", "/backups/", "/dump/", "/dumps/", "/sql/", "/data/", "/database/",
    "/wp-content/backup-db/", "/administrator/components/com_akeeba/backup/",
    "/var/backups/", "/storage/backups/",
    "/error_log", "/error.log", "/debug.log", "/access.log", "/logs/error.log",
    "/.git/config", "/.DS_Store", "/.bash_history", "/etc/passwd"
]
SENSITIVE_PATTERNS = {
    "DB_Credentials": re.compile(
        r"(DB_USER|DB_USERNAME|DATABASE_USER|MYSQL_USER|PGUSER|user(?:name)?)\s*[:=]\s*[\"\']?([a-zA-Z0-9_.-]+?)[\"\']?\s*.*?\s*(DB_PASS|DB_PASSWORD|DATABASE_PASS|MYSQL_PASSWORD|PGPASSWORD|pass(?:word)?)\s*[:=]\s*[\"\']?([^\"\'\s<>{}\[\]\(\)]+?)[\"\']?",
        re.IGNORECASE
    ),
    "DB_Host_Port": re.compile(
        r"(DB_HOST|DATABASE_HOST|MYSQL_HOST|PGHOST|host)\s*[:=]\s*[\"\']?([a-zA-Z0-9_.-]+?)[\"\']?.*?\s*(DB_PORT|DATABASE_PORT|MYSQL_PORT|PGPORT|port)\s*[:=]\s*[\"\']?(\d{1,5})[\"\']?",
        re.IGNORECASE
    ),
    "DB_Name": re.compile(
        r"(DB_NAME|DB_DATABASE|DATABASE_NAME|MYSQL_DB|PGDATABASE|dbname)\s*[:=]\s*[\"\']?([a-zA-Z0-9_.-]+?)[\"\']?",
        re.IGNORECASE
    ),
    "DB_Connection_String": re.compile(
        r"(postgres(?:ql)?|mysql|mongodb(?:\+srv)?|redis|oracle|sqlserver):\/\/(?:([^:@\/]+)(?::([^@\/]+))?@)?([\w.-]+(?:\:\d+)?)(?:\/([\w.-]+))?",
        re.IGNORECASE
    ),
    "API_Keys": re.compile(
        r"(api_key|apikey|api-key|client_secret|secret_key|auth_token|bearer_token|access_token)\s*[:=]\s*[\"\']?([a-zA-Z0-9_\-.\/+=]{16,})[\"\']?",
        re.IGNORECASE
    ),
    "SQL_Dumps": re.compile(
        r"(INSERT\s+INTO|CREATE\s+TABLE|DROP\s+TABLE|ALTER\s+TABLE|mysqldump|pg_dump)",
        re.IGNORECASE
    )
}
FILTER_PATTERNS = [
    re.compile(r"<title>403 Forbidden</title>", re.IGNORECASE),
    re.compile(r"<title>404 Not Found</title>", re.IGNORECASE),
    re.compile(r"<title>Access Denied</title>", re.IGNORECASE),
    re.compile(r"<title>Error</title>", re.IGNORECASE),
    re.compile(r"<title>DDoS-Guard</title>", re.IGNORECASE),
    re.compile(r"<!doctype html", re.IGNORECASE),
    re.compile(r"<html", re.IGNORECASE),
    re.compile(r"request blocked", re.IGNORECASE),
    re.compile(r"cloudflare|sucuri|incapsula|akamai", re.IGNORECASE),
    re.compile(r"wp-login\.php", re.IGNORECASE),
    re.compile(r"window\['_chunksDictionary'\]", re.IGNORECASE)
]

class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class Animation:
    @staticmethod
    def spinner(text="Processando", duration=3):
        spinner_chars = ["⢿", "⣻", "⣽", "⣾", "⣷", "⣯", "⣟", "⡿"]
        end_time = time.time() + duration
        i = 0
        while time.time() < end_time:
            char = spinner_chars[i % len(spinner_chars)]
            sys.stdout.write(f"\r{Colors.CYAN}{text} {char}{Colors.ENDC} ")
            sys.stdout.flush()
            time.sleep(0.1)
            i += 1
        sys.stdout.write("\r" + " " * (len(text) + 5) + "\r")
        sys.stdout.flush()

    @staticmethod
    def progress_bar(text="Progresso", duration=3, width=20):
        for i in range(width + 1):
            percent = i * 100.0 / width
            bar = '█' * i + '░' * (width - i)
            sys.stdout.write(f"\r{text}: {Colors.CYAN}[{bar}] {percent:.1f}%{Colors.ENDC}")
            sys.stdout.flush()
            time.sleep(duration / width)
        sys.stdout.write("\r" + " " * 70 + "\r")
        sys.stdout.flush()

class Logger:
    def __init__(self, log_file="collected_dbs.log"):
        self.log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
        os.makedirs(self.log_dir, exist_ok=True)
        self.log_path = os.path.join(self.log_dir, log_file)
        self.verbose = False

    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}\n"
        try:
            with open(self.log_path, "a", encoding='utf-8') as f:
                f.write(log_entry)
        except IOError as e:
            print(f"{Colors.RED}Erro ao escrever no log: {e}{Colors.ENDC}")
        if level == "ERROR":
            print(f"{Colors.RED}[ERRO] {message}{Colors.ENDC}")
        elif level == "WARNING" and self.verbose:
            print(f"{Colors.YELLOW}[AVISO] {message}{Colors.ENDC}")
        elif level == "SUCCESS":
            print(f"{Colors.GREEN}[SUCESSO] {message}{Colors.ENDC}")
        elif level == "INFO" and self.verbose:
            print(f"{Colors.BLUE}[INFO] {message}{Colors.ENDC}")

class Banner:
    @staticmethod
    def show():
        os.system('clear')
        banner = f"""
{Colors.CYAN}╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║   {Colors.RED} ██████╗ ██████╗ ██╗     ██╗     ███████╗ ██████╗████████╗{Colors.CYAN}   ║
║   {Colors.RED}██╔════╝██╔═══██╗██║     ██║     ██╔════╝██╔════╝╚══██╔══╝{Colors.CYAN}   ║
║   {Colors.RED}██║     ██║   ██║██║     ██║     █████╗  ██║        ██║{Colors.CYAN}      ║
║   {Colors.RED}██║     ██║   ██║██║     ██║     ██╔══╝  ██║        ██║{Colors.CYAN}      ║
║   {Colors.RED}╚██████╗╚██████╔╝███████╗███████╗███████╗╚██████╗   ██║{Colors.CYAN}      ║
║   {Colors.RED} ╚═════╝ ╚═════╝ ╚══════╝╚══════╝╚══════╝ ╚═════╝   ╚═╝{Colors.CYAN}      ║
║                                                               ║
║   {Colors.GREEN}██████╗ ██████╗ ███████╗{Colors.CYAN}    {Colors.YELLOW}Ferramenta Focada em DB{Colors.CYAN}     ║
║   {Colors.GREEN}██╔══██╗██╔══██╗██╔════╝{Colors.CYAN}                              ║
║   {Colors.GREEN}██║  ██║██████╔╝███████╗{Colors.CYAN}                              ║
║   {Colors.GREEN}██║  ██║██╔══██╗╚════██║{Colors.CYAN}                              ║
║   {Colors.GREEN}██████╔╝██████╔╝███████║{Colors.CYAN}                              ║
║   {Colors.GREEN}╚═════╝ ╚═════╝ ╚══════╝{Colors.CYAN}                              ║
║                                                               ║
╠═══════════════════════════════════════════════════════════════╣
║ {Colors.YELLOW}GitHub:{Colors.GREEN} https://github.com/sentinelzxofc/collected-dbs{Colors.CYAN}      ║
║ {Colors.YELLOW}Instagram:{Colors.GREEN} @sentinelzxofc{Colors.CYAN}                                   ║
║ {Colors.YELLOW}Versão:{Colors.GREEN} {VERSION}{Colors.CYAN}                                              ║
╚═══════════════════════════════════════════════════════════════╝
{Colors.ENDC}"""
        print(banner)
        print(f"{Colors.RED}{Colors.BOLD}AVISO LEGAL:{Colors.ENDC}{Colors.RED} Esta ferramenta foi criada apenas para fins educacionais e de teste.")
        print(f"O autor não se responsabiliza pelo uso indevido desta ferramenta.{Colors.ENDC}")
        print(f"{Colors.YELLOW}{Colors.BOLD}LEGAL DISCLAIMER:{Colors.ENDC}{Colors.YELLOW} This tool is intended for educational and testing purposes only.")
        print(f"The author is not responsible for any misuse of this tool.{Colors.ENDC}\n")

class CacheManager:
    def __init__(self, cache_file="cache.json"):
        self.cache_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache", cache_file)
        os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
        self.cache = self.load_cache()

    def load_cache(self):
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"{Colors.RED}Erro ao carregar cache: {e}{Colors.ENDC}")
        return {}

    def save_cache(self):
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"{Colors.RED}Erro ao salvar cache: {e}{Colors.ENDC}")

    def get(self, url):
        return self.cache.get(url)

    def set(self, url, result):
        self.cache[url] = {"result": result, "timestamp": datetime.now().isoformat()}
        self.save_cache()

class CollectionTools:
    def __init__(self, logger, proxy_config=None):
        self.logger = logger
        self.results_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resultados")
        self.downloads_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "downloads")
        self.invalid_dir = os.path.join(self.downloads_dir, "invalid")
        self.cache_manager = CacheManager()
        self.proxy_config = proxy_config
        os.makedirs(self.results_dir, exist_ok=True)
        os.makedirs(self.downloads_dir, exist_ok=True)
        os.makedirs(self.invalid_dir, exist_ok=True)
        self.session_cache = {}
        self.request_count = {}
        self.cookies = self.load_cookies()
        self.cookies_mtime = self.get_cookies_mtime()

    def get_cookies_mtime(self):
        cookies_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cookies.json")
        try:
            return os.path.getmtime(cookies_file) if os.path.exists(cookies_file) else 0
        except:
            return 0

    def load_cookies(self):
        cookies_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cookies.json")
        if os.path.exists(cookies_file):
            try:
                with open(cookies_file, 'r', encoding='utf-8') as f:
                    cookies = json.load(f)
                for domain, cookie_dict in cookies.items():
                    if not isinstance(cookie_dict, dict):
                        self.logger.log(f"Formato inválido para cookies do domínio {domain}", "ERROR")
                        return {}
                return cookies
            except Exception as e:
                self.logger.log(f"Erro ao carregar cookies.json: {e}", "ERROR")
        return {}

    def reload_cookies_if_changed(self):
        current_mtime = self.get_cookies_mtime()
        if current_mtime > self.cookies_mtime:
            self.logger.log("Cookies.json modificado, recarregando...", "INFO")
            self.cookies = self.load_cookies()
            self.cookies_mtime = current_mtime
            self.session_cache.clear()

    def get_random_user_agent(self):
        return random.choice(USER_AGENTS)

    def get_session(self, url):
        self.reload_cookies_if_changed()
        domain = urlparse(url).netloc
        if domain not in self.session_cache:
            session = requests.Session()
            session.headers.update({
                "User-Agent": self.get_random_user_agent(),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Referer": url,
                "Origin": urlparse(url).scheme + "://" + urlparse(url).netloc,
                "DNT": "1",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "same-origin",
                "Sec-Fetch-User": "?1",
                "Sec-CH-UA": '"Chromium";v="129", "Not=A?Brand";v="8"',
                "Upgrade-Insecure-Requests": "1"
            })
            if domain in self.cookies:
                for name, value in self.cookies[domain].items():
                    session.cookies.set(name, value, domain=domain)
            if self.proxy_config:
                session.proxies = self.proxy_config
            self.session_cache[domain] = session
            self.request_count[domain] = 0
        self.request_count[domain] += 1
        return self.session_cache[domain]

    def save_results(self, data, filename_prefix, target):
        safe_target = re.sub(r"[^a-zA-Z0-9_.-]", "_", target)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{filename_prefix}_{safe_target}_{timestamp}.json"
        filepath = os.path.join(self.results_dir, filename)
        try:
            with open(filepath, "w", encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            self.logger.log(f"Resultados salvos em: {filepath}", "SUCCESS")
            return True
        except IOError as e:
            self.logger.log(f"Erro ao salvar resultados em {filepath}: {e}", "ERROR")
            return False

    def analyze_file(self, filepath):
        try:
            with open(filepath, 'rb') as f:
                content = f.read(4096)
            content_text = content.decode('utf-8', errors='ignore')
            if any(pattern.search(content_text) for pattern in FILTER_PATTERNS):
                return {"type": "HTML", "details": f"Contém página de erro: {content_text[:100]}"}
            entropy = self.calculate_entropy(content)
            if entropy > 7.0:
                return {"type": "Criptografado", "details": f"Alta entropia ({entropy:.2f}): {hexlify(content[:50]).decode()}"}
            if content_text.strip():
                if content_text.startswith('<!DOCTYPE') or '<html' in content_text.lower():
                    return {"type": "HTML", "details": f"Contém HTML: {content_text[:100]}"}
                if any(p.search(content_text) for p in SENSITIVE_PATTERNS.values()):
                    return {"type": "Texto Sensível", "details": f"Contém padrões sensíveis: {content_text[:100]}"}
            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    reader = csv.reader(f)
                    headers = next(reader, None)
                    if headers and len(headers) > 1:
                        return {"type": "CSV", "details": f"Cabeçalhos: {len(headers)}"}
            except:
                pass
            return {"type": "Desconhecido", "details": f"Não identificado: {hexlify(content[:50]).decode()}"}
        except Exception as e:
            return {"type": "Erro", "details": f"Erro ao analisar: {e}"}

    def calculate_entropy(self, data):
        if not data:
            return 0.0
        from math import log2
        from collections import Counter
        counter = Counter(data)
        length = len(data)
        entropy = -sum((count / length) * log2(count / length) for count in counter.values())
        return entropy

    def validate_db_file(self, filepath, content_text):
        filename = os.path.basename(filepath).lower()
        try:
            if '<html' in content_text.lower() or any(pattern.search(content_text) for pattern in FILTER_PATTERNS):
                return {"valid": False, "type": "HTML", "details": f"Contém página de erro: {content_text[:100]}"}
            sensitive_found = False
            for key, pattern in SENSITIVE_PATTERNS.items():
                if pattern.search(content_text):
                    sensitive_found = True
                    break
            if filename.endswith('.sql'):
                if SENSITIVE_PATTERNS["SQL_Dumps"].search(content_text):
                    return {"valid": True, "type": "SQL Dump", "details": "Contém comandos SQL válidos"}
                return {"valid": False, "type": "SQL Dump", "details": f"Não contém comandos SQL válidos: {content_text[:100]}"}
            elif filename.endswith(('.sqlite', '.db')):
                try:
                    conn = sqlite3.connect(filepath)
                    cursor = conn.cursor()
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                    tables = cursor.fetchall()
                    conn.close()
                    if tables:
                        return {"valid": True, "type": "SQLite", "details": f"Tabelas encontradas: {len(tables)}"}
                    return {"valid": False, "type": "SQLite", "details": f"Nenhuma tabela encontrada: {content_text[:100]}"}
                except sqlite3.Error as e:
                    return {"valid": False, "type": "SQLite", "details": f"Erro ao abrir: {e}"}
            elif filename.endswith('.csv'):
                try:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        reader = csv.reader(f)
                        headers = next(reader, None)
                        if headers and len(headers) > 1 and not any('<' in h for h in headers):
                            return {"valid": True, "type": "CSV", "details": f"Cabeçalhos: {len(headers)}"}
                        return {"valid": False, "type": "CSV", "details": f"Formato inválido ou contém HTML: {content_text[:100]}"}
                except csv.Error as e:
                    return {"valid": False, "type": "CSV", "details": f"Erro ao ler: {e}"}
            elif filename.endswith('.gz'):
                try:
                    with gzip.open(filepath, 'rt', encoding='utf-8', errors='ignore') as f:
                        content = f.read(1024 * 1024)
                        if SENSITIVE_PATTERNS["SQL_Dumps"].search(content):
                            return {"valid": True, "type": "Gzip SQL", "details": "Contém comandos SQL válidos"}
                        return {"valid": False, "type": "Gzip SQL", "details": f"Não contém comandos SQL válidos: {content[:100]}"}
                except gzip.BadGzipFile:
                    return {"valid": False, "type": "Gzip", "details": "Arquivo gzip inválido"}
            elif filename.endswith('.tar.gz') or filename.endswith('.tar'):
                try:
                    with tarfile.open(filepath, 'r:*') as t:
                        for member in t.getmembers():
                            if member.name.lower().endswith(('.sql', '.db', '.sqlite', '.csv')):
                                return {"valid": True, "type": "Tar", "details": f"Contém: {member.name}"}
                        return {"valid": False, "type": "Tar", "details": "Nenhum arquivo DB relevante encontrado"}
                except tarfile.TarError:
                    return {"valid": False, "type": "Tar", "details": "Arquivo tar inválido"}
            elif filename.endswith('.zip'):
                try:
                    with zipfile.ZipFile(filepath) as z:
                        for zinfo in z.infolist():
                            if zinfo.filename.lower().endswith(('.sql', '.db', '.sqlite', '.csv')):
                                return {"valid": True, "type": "Zip", "details": f"Contém: {zinfo.filename}"}
                        return {"valid": False, "type": "Zip", "details": "Nenhum arquivo DB relevante encontrado"}
                except zipfile.BadZipFile:
                    return {"valid": False, "type": "Zip", "details": "Arquivo zip inválido"}
            elif filename.endswith(('.env', '.env.save', '.env.bak')):
                if sensitive_found:
                    return {"valid": True, "type": "ENV", "details": "Contém padrões sensíveis"}
                return {"valid": False, "type": "ENV", "details": "Sem padrões sensíveis"}
            elif filename.endswith(('.yml', '.yaml')):
                try:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        yaml.safe_load(f)
                        if sensitive_found:
                            return {"valid": True, "type": "YAML", "details": "Formato YAML válido com padrões sensíveis"}
                        return {"valid": True, "type": "YAML", "details": "Formato YAML válido, sem padrões sensíveis"}
                except yaml.YAMLError:
                    return {"valid": False, "type": "YAML", "details": "Formato YAML inválido"}
            elif filename.endswith('.json'):
                try:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        json.load(f)
                        if sensitive_found:
                            return {"valid": True, "type": "JSON", "details": "Formato JSON válido com padrões sensíveis"}
                        return {"valid": True, "type": "JSON", "details": "Formato JSON válido, sem padrões sensíveis"}
                except json.JSONDecodeError:
                    return {"valid": False, "type": "JSON", "details": "Formato JSON inválido"}
            elif filename.endswith(('.log', '.key', '.xml', '.bak')):
                if sensitive_found:
                    return {"valid": True, "type": filename.split('.')[-1].upper(), "details": "Contém padrões sensíveis"}
                return {"valid": False, "type": filename.split('.')[-1].upper(), "details": "Sem padrões sensíveis"}
            return {"valid": False, "type": "Desconhecido", "details": "Formato não suportado"}
        except Exception as e:
            return {"valid": False, "type": "Desconhecido", "details": f"Erro ao validar: {e}"}

    def check_db_port(self, host, port, timeout=2):
        try:
            sock = socket(AF_INET, SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
            sock.close()
            if result == 0:
                return {"open": True, "port": port, "details": f"Porta {port} aberta (potencial serviço de banco de dados)"}
            return {"open": False, "port": port, "details": f"Porta {port} fechada"}
        except Exception as e:
            return {"open": False, "port": port, "details": f"Erro ao verificar porta: {e}"}

    def check_db_exposure(self, url):
        print(f"\n{Colors.RED}{Colors.BOLD}AVISO LEGAL IMPORTANTE:{Colors.ENDC}")
        print(f"{Colors.RED}Você deve ter autorização explícita do proprietário do sistema para realizar esta verificação.{Colors.ENDC}")
        print(f"{Colors.RED}O uso desta ferramenta sem permissão é ilegal e de sua total responsabilidade.{Colors.ENDC}")
        print(f"{Colors.YELLOW}Confirme que você possui autorização e está em um ambiente controlado (s/n):{Colors.ENDC} ")
        confirm = input().strip().lower()
        if confirm != 's':
            print(f"{Colors.RED}Operação cancelada. Autorização não confirmada.{Colors.ENDC}")
            self.logger.log("Verificação cancelada: Autorização não confirmada")
            return []
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        parsed_url = urlparse(url)
        domain = parsed_url.netloc or url
        if not domain:
            print(f"{Colors.RED}URL inválida.{Colors.ENDC}")
            return []
        print(f"{Colors.BLUE}Verificando exposição de banco de dados em {url}...{Colors.ENDC}")
        self.logger.log(f"Verificando exposição em {url}")
        exposed_paths = []
        session = self.get_session(url)
        db_ports = [
            (3306, "MySQL"), (5432, "PostgreSQL"), (1433, "SQL Server"),
            (27017, "MongoDB"), (6379, "Redis")
        ]
        for port, db_type in db_ports:
            port_result = self.check_db_port(domain, port)
            if port_result["open"]:
                exposed_paths.append({
                    "type": "port",
                    "url": f"{domain}:{port}",
                    "details": port_result["details"],
                    "db_type": db_type
                })
                print(f"{Colors.YELLOW}[!] Porta aberta detectada: {port_result['details']}{Colors.ENDC}")
        print(f"{Colors.CYAN}Total de caminhos a verificar: {len(DB_PATHS)}{Colors.ENDC}")
        with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
            futures = {}
            for path in DB_PATHS:
                full_url = url.rstrip('/') + path
                cached_result = self.cache_manager.get(full_url)
                if cached_result:
                    if cached_result["result"]:
                        exposed_paths.append(cached_result["result"])
                        print(f"{Colors.GREEN}[+] Exposição encontrada (cache): {cached_result['result']['url']} (Status: {cached_result['result']['status_code']}, Tamanho: {cached_result['result']['content_length']} bytes){Colors.ENDC}")
                    continue
                futures[executor.submit(self.check_path, session, full_url)] = full_url
            progress = tqdm(total=len(futures), desc="Verificando caminhos", unit="path", ncols=70)
            for future in as_completed(futures):
                full_url = futures[future]
                result = future.result()
                self.cache_manager.set(full_url, result)
                if result:
                    exposed_paths.append(result)
                    print(f"{Colors.GREEN}[+] Exposição encontrada: {result['url']} (Status: {result['status_code']}, Tamanho: {result['content_length']} bytes){Colors.ENDC}")
                    if result.get("sensitive_keywords"):
                        print(f"{Colors.YELLOW}    -> Padrões sensíveis: {', '.join(result['sensitive_keywords'])}{Colors.ENDC}")
                    if result.get("content_preview"):
                        print(f"{Colors.YELLOW}    -> Prévia: {result['content_preview'][:150]}...{Colors.ENDC}")
                progress.update(1)
            progress.close()
        print(f"\n{Colors.GREEN}Verificação concluída! Encontrados: {len(exposed_paths)}{Colors.ENDC}")
        if exposed_paths:
            self.save_results(exposed_paths, "db_exposure", domain)
        else:
            print(f"{Colors.YELLOW}Nenhuma exposição encontrada.{Colors.ENDC}")
        return exposed_paths

    @retry(
        stop=stop_after_attempt(10),
        wait=wait_exponential(multiplier=1, min=4, max=20),
        retry=retry_if_exception_type((requests.exceptions.SSLError, requests.exceptions.RequestException)),
        before_sleep=lambda retry_state: print(f"{Colors.YELLOW}Tentando novamente em {retry_state.next_action.sleep} segundos...{Colors.ENDC}")
    )
    def check_path(self, session, url):
        start_time = time.time()
        try:
            head_response = session.head(url, timeout=REQUEST_TIMEOUT/2, verify=False, allow_redirects=False)
            status_code = head_response.status_code
            headers = head_response.headers
            content_type = headers.get('Content-Type', 'Desconhecido').lower()
            content_length = int(headers.get('Content-Length', 0)) or 0
            path_part = urlparse(url).path
            if status_code in [404, 410, 301, 302, 307, 308]:
                return None
            if any(ct in content_type for ct in ['image/', 'text/css', 'javascript', 'font/']) and not any(url.endswith(p) for p in ['.sql', '.db', '.env']):
                return None
            if content_type.startswith('text/html') and any(url.endswith(ext) for ext in ['.gz', '.zip', '.csv', '.tar']):
                return None
            get_response = session.get(url, timeout=REQUEST_TIMEOUT, verify=False, allow_redirects=True, stream=True)
            status_code = get_response.status_code
            if status_code in [404, 410, 301, 302, 307, 308]:
                return None
            content_sample = b""
            for chunk in get_response.iter_content(chunk_size=1024):
                content_sample += chunk
                if len(content_sample) > 10240:
                    break
            content_length = content_length or len(content_sample)
            content_text = content_sample.decode('utf-8', errors='ignore')
            if url.endswith(('.gz', '.tar.gz')):
                try:
                    content_text = gzip.decompress(content_sample).decode('utf-8', errors='ignore')
                except gzip.BadGzipFile:
                    return None
            if any(pattern.search(content_text) for pattern in FILTER_PATTERNS):
                return None
            result_data = {
                "path": path_part,
                "url": url,
                "status_code": status_code,
                "content_length": content_length,
                "content_type": content_type,
                "sensitive_keywords": [],
                "content_preview": "",
                "headers": dict(headers),
                "response_time": time.time() - start_time
            }
            found_sensitive = False
            for key, pattern in SENSITIVE_PATTERNS.items():
                matches = pattern.finditer(content_text)
                for match in matches:
                    result_data["sensitive_keywords"].append(key)
                    found_sensitive = True
                    if not result_data["content_preview"]:
                        result_data["content_preview"] = f"Padrão '{key}': {match.group(0)[:100]}..."
            if found_sensitive:
                return result_data
            if any(st in content_type or url.endswith(f".{st}") for st in ['sql', 'db', 'sqlite', 'env', 'bak', 'zip', 'gz', 'tar', 'yml', 'json', 'csv', 'log', 'key', 'xml']) and status_code == 200 and content_length > 50:
                result_data["content_preview"] = content_text[:150].replace('\n', ' ') + "..."
                return result_data
            if status_code == 403 and any(re.search(p, path_part, re.IGNORECASE) for p in [r"\.env", r"\.sql", r"backup\.", r"config\.php"]):
                result_data["content_preview"] = "Arquivo protegido (403), mas potencialmente sensível."
                return result_data
            return None
        except requests.exceptions.SSLError as e:
            self.logger.log(f"Erro SSL em {url}: {e}", "WARNING")
            if url.startswith('https://'):
                return self.check_path(session, url.replace('https://', 'http://'))
            return None
        except requests.exceptions.RequestException:
            return None
        except Exception as e:
            self.logger.log(f"Erro ao verificar {url}: {e}", "WARNING")
            return None

    @retry(
        stop=stop_after_attempt(10),
        wait=wait_exponential(multiplier=1, min=4, max=20),
        retry=retry_if_exception_type((requests.exceptions.SSLError, requests.exceptions.RequestException)),
        before_sleep=lambda retry_state: print(f"{Colors.YELLOW}Tentando novamente em {retry_state.next_action.sleep} segundos...{Colors.ENDC}")
    )
    def download_file(self, url, filename, skip_validation=False):
        time.sleep(random.uniform(0.5, 2.0))
        print(f"{Colors.BLUE}Tentando baixar: {url}{Colors.ENDC}")
        self.logger.log(f"Iniciando download de {url}")
        domain = urlparse(url).netloc
        session = self.get_session(url)
        if self.request_count.get(domain, 0) % 3 == 0 and self.proxy_config:
            self.proxy_config = self.proxy_manager.rotate_proxy()
            session.proxies = self.proxy_config
            self.logger.log(f"Rotacionando proxy para {url}: {self.proxy_config}", "INFO")
        safe_filename = re.sub(r'[^a-zA-Z0-9._-]', '_', filename) or f"downloaded_{int(time.time())}"
        if '.' not in safe_filename and '.' in filename:
            safe_filename += os.path.splitext(filename)[1]
        save_path = os.path.join(self.downloads_dir, safe_filename)
        invalid_path = os.path.join(self.invalid_dir, safe_filename)
        try:
            response = session.get(url, stream=True, timeout=60, verify=False, allow_redirects=True)
            response.raise_for_status()
            content_sample = b""
            for chunk in response.iter_content(chunk_size=1024):
                content_sample += chunk
                if len(content_sample) >= 4096:
                    break
            content_text = content_sample.decode('utf-8', errors='ignore')
            if any(pattern.search(content_text) for pattern in FILTER_PATTERNS):
                self.logger.log(f"Download inválido: {url} contém página de erro: {content_text[:200]}", "ERROR")
                print(f"{Colors.RED}Erro: Arquivo parece ser uma página de erro.{Colors.ENDC}")
                return False
            total_size = int(response.headers.get('content-length', 0))
            if os.path.exists(save_path):
                overwrite = input(f"{Colors.YELLOW}Arquivo '{safe_filename}' já existe. Sobrescrever? (s/n): {Colors.ENDC}").lower()
                if not overwrite.startswith('s'):
                    print(f"{Colors.YELLOW}Download cancelado.{Colors.ENDC}")
                    return False
            progress = tqdm(total=total_size, unit='iB', unit_scale=True, desc=safe_filename, ncols=70)
            downloaded_size = 0
            with open(save_path, 'wb') as f:
                response = session.get(url, stream=True, timeout=60, verify=False, allow_redirects=True)
                for data in response.iter_content(chunk_size=8192):
                    progress.update(len(data))
                    f.write(data)
                    downloaded_size += len(data)
            progress.close()
            if total_size != 0 and downloaded_size != total_size:
                self.logger.log(f"Erro no download: Tamanho incorreto ({downloaded_size}/{total_size}) para {url}", "ERROR")
                print(f"{Colors.RED}Erro: Tamanho do arquivo não corresponde ({downloaded_size}/{total_size}).{Colors.ENDC}")
                os.remove(save_path)
                return False
            if downloaded_size == 0:
                self.logger.log(f"Erro no download: Arquivo vazio para {url}", "ERROR")
                print(f"{Colors.RED}Erro: Arquivo baixado está vazio.{Colors.ENDC}")
                os.remove(save_path)
                return False
            analysis = self.analyze_file(save_path)
            self.logger.log(f"Análise de {safe_filename}: {analysis}", "INFO")
            print(f"{Colors.CYAN}Análise: {analysis['type']} - {analysis['details']}{Colors.ENDC}")
            if skip_validation:
                self.logger.log(f"Validação ignorada para {safe_filename}", "INFO")
                print(f"{Colors.GREEN}Download concluído (validação ignorada): {safe_filename} salvo em {self.downloads_dir}{Colors.ENDC}")
                return True
            validation = self.validate_db_file(save_path, content_text)
            self.logger.log(f"Validação de {safe_filename}: {validation}", "INFO")
            print(f"{Colors.CYAN}Validação: {validation['type']} - {'Válido' if validation['valid'] else 'Inválido'} ({validation['details']}){Colors.ENDC}")
            if not validation["valid"]:
                print(f"{Colors.YELLOW}Arquivo inválido movido para {self.invalid_dir}{Colors.ENDC}")
                os.rename(save_path, invalid_path)
                return False
            print(f"{Colors.GREEN}Download concluído: {safe_filename} salvo em {self.downloads_dir}{Colors.ENDC}")
            return True
        except requests.exceptions.SSLError as e:
            self.logger.log(f"Erro SSL ao baixar {url}: {e}", "ERROR")
            if url.startswith('https://'):
                return self.download_file(url.replace('https://', 'http://'), filename, skip_validation)
            return False
        except requests.exceptions.RequestException as e:
            self.logger.log(f"Erro de requisição ao baixar {url}: {e}", "ERROR")
            print(f"{Colors.RED}Erro de requisição: {e}{Colors.ENDC}")
            return False
        except Exception as e:
            self.logger.log(f"Erro ao baixar {url}: {e}", "ERROR")
            print(f"{Colors.RED}Erro inesperado: {e}{Colors.ENDC}")
            return False

class DependencyChecker:
    @staticmethod
    def check_dependencies():
        required_packages = ["requests", "bs4", "tqdm", "tenacity", "pyyaml"]
        missing_packages = []
        for package in required_packages:
            try:
                __import__(package)
            except ImportError:
                missing_packages.append(package)
        return missing_packages

    @staticmethod
    def install_dependencies(packages):
        if not packages:
            return True
        print(f"{Colors.YELLOW}Instalando dependências: {', '.join(packages)}{Colors.ENDC}")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade"] + packages)
            return True
        except subprocess.CalledProcessError:
            print(f"{Colors.RED}Falha ao instalar dependências. Execute: pkg install python && pip install {' '.join(packages)}{Colors.ENDC}")
            return False

class ProxyManager:
    def __init__(self, logger):
        self.logger = logger
        self.proxies = []
        self.current_proxy = None
        self.load_proxies()

    def load_proxies(self):
        proxies_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "proxies.txt")
        if os.path.exists(proxies_file):
            try:
                with open(proxies_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            try:
                                proxy_type, proxy_url = line.split("://", 1)
                                if proxy_type in ["http", "socks4", "socks5"]:
                                    self.add_proxy(proxy_type, proxy_url)
                            except ValueError:
                                self.logger.log(f"Formato inválido no proxies.txt: {line}", "WARNING")
            except Exception as e:
                self.logger.log(f"Erro ao carregar proxies.txt: {e}", "ERROR")

    def add_proxy(self, proxy_type, proxy_url):
        if not proxy_url:
            return False
        if proxy_type not in ["http", "socks4", "socks5"]:
            self.logger.log(f"Tipo de proxy inválido: {proxy_type}", "ERROR")
            return False
        proxy_full_url = f"{proxy_type}://{proxy_url}" if not proxy_url.startswith(('http://', 'https://', 'socks4://', 'socks5://')) else proxy_url
        try:
            response = requests.get("https://httpbin.org/ip", proxies={"http": proxy_full_url, "https": proxy_full_url}, timeout=10)
            response.raise_for_status()
            self.proxies.append({"type": proxy_type, "url": proxy_full_url})
            return True
        except requests.exceptions.RequestException as e:
            self.logger.log(f"Proxy inválido: {proxy_full_url} ({e})", "WARNING")
            return False

    def set_proxy(self, proxy_type, proxy_url):
        if not proxy_url:
            self.current_proxy = None
            self.proxies = []
            return True
        if self.add_proxy(proxy_type, proxy_url):
            self.current_proxy = {"http": self.proxies[-1]["url"], "https": self.proxies[-1]["url"]}
            self.logger.log(f"Proxy configurado: {self.proxies[-1]['url']}", "SUCCESS")
            return True
        return False

    def get_proxy_config(self):
        return self.current_proxy

    def rotate_proxy(self):
        if not self.proxies:
            return None
        self.current_proxy = {"http": random.choice(self.proxies)["url"], "https": random.choice(self.proxies)["url"]}
        self.logger.log(f"Proxy rotacionado: {self.current_proxy}", "INFO")
        return self.current_proxy

class CollectedDBS:
    def __init__(self):
        self.logger = Logger()
        self.proxy_manager = ProxyManager(self.logger)
        self.tools = CollectionTools(self.logger, self.proxy_manager.get_proxy_config())
        self.last_exposed_files = []
        signal.signal(signal.SIGINT, self.signal_handler)

    def signal_handler(self, sig, frame):
        print(f"\n{Colors.YELLOW}Programa interrompido.{Colors.ENDC}")
        self.logger.log("Programa interrompido pelo usuário")
        sys.exit(0)

    def check_setup(self):
        for dir_path in ["logs", "resultados", "downloads", "downloads/invalid", "cache"]:
            os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)), dir_path), exist_ok=True)
        missing_packages = DependencyChecker.check_dependencies()
        if missing_packages:
            if not DependencyChecker.install_dependencies(missing_packages):
                print(f"{Colors.RED}Erro ao instalar dependências.{Colors.ENDC}")
                return False
        return True

    def main_menu(self):
        while True:
            Banner.show()
            print(f"{Colors.CYAN}╔═══════════════════════════════════════════════════════════════╗{Colors.ENDC}")
            print(f"{Colors.CYAN}║                 {Colors.YELLOW}CAPTURA DE BANCOS DE DADOS{Colors.CYAN}                 ║{Colors.ENDC}")
            print(f"{Colors.CYAN}╠═══════════════════════════════════════════════════════════════╣{Colors.ENDC}")
            print(f"{Colors.CYAN}║ {Colors.GREEN}[1]{Colors.CYAN} Verificar Exposição de Banco de Dados              ║{Colors.ENDC}")
            print(f"{Colors.CYAN}║ {Colors.GREEN}[2]{Colors.CYAN} Download de Arquivos Expostos                      ║{Colors.ENDC}")
            print(f"{Colors.CYAN}║ {Colors.GREEN}[3]{Colors.CYAN} Configurar Proxy                                   ║{Colors.ENDC}")
            print(f"{Colors.CYAN}║ {Colors.GREEN}[4]{Colors.CYAN} Alternar Modo Verbose                              ║{Colors.ENDC}")
            print(f"{Colors.CYAN}║ {Colors.GREEN}[5]{Colors.CYAN} Sobre o Programa                                   ║{Colors.ENDC}")
            print(f"{Colors.CYAN}║ {Colors.GREEN}[0]{Colors.CYAN} Sair                                               ║{Colors.ENDC}")
            print(f"{Colors.CYAN}╚═══════════════════════════════════════════════════════════════╝{Colors.ENDC}")
            print(f"{Colors.CYAN}Modo Verbose: {'Ativado' if self.logger.verbose else 'Desativado'}{Colors.ENDC}")
            choice = input(f"\n{Colors.YELLOW}Escolha uma opção:{Colors.ENDC} ")
            if choice == "1":
                self.db_exposure_menu()
            elif choice == "2":
                self.download_exposed_files_menu()
            elif choice == "3":
                self.proxy_menu()
            elif choice == "4":
                self.logger.verbose = not self.logger.verbose
                print(f"{Colors.GREEN}Modo Verbose {'ativado' if self.logger.verbose else 'desativado'}!{Colors.ENDC}")
                time.sleep(1)
            elif choice == "5":
                self.about()
            elif choice == "0":
                print(f"{Colors.GREEN}Obrigado por usar o Collected-DBs!{Colors.ENDC}")
                sys.exit(0)
            else:
                print(f"{Colors.RED}Opção inválida.{Colors.ENDC}")
            time.sleep(1)

    def db_exposure_menu(self):
        Banner.show()
        print(f"{Colors.CYAN}╔═══════════════════════════════════════════════════════════════╗{Colors.ENDC}")
        print(f"{Colors.CYAN}║              {Colors.YELLOW}VERIFICAÇÃO DE EXPOSIÇÃO DE DB{Colors.CYAN}              ║{Colors.ENDC}")
        print(f"{Colors.CYAN}╚═══════════════════════════════════════════════════════════════╝{Colors.ENDC}")
        url = input(f"\n{Colors.YELLOW}Digite a URL do website (ex: exemplo.com):{Colors.ENDC} ").strip()
        if not url:
            print(f"{Colors.RED}URL inválida.{Colors.ENDC}")
            time.sleep(2)
            return
        self.last_exposed_files = self.tools.check_db_exposure(url)
        input(f"\n{Colors.GREEN}Pressione Enter para continuar...{Colors.ENDC}")

    def download_exposed_files_menu(self):
        Banner.show()
        print(f"{Colors.CYAN}╔═══════════════════════════════════════════════════════════════╗{Colors.ENDC}")
        print(f"{Colors.CYAN}║                {Colors.YELLOW}DOWNLOAD DE ARQUIVOS EXPOSTOS{Colors.CYAN}               ║{Colors.ENDC}")
        print(f"{Colors.CYAN}╚═══════════════════════════════════════════════════════════════╝{Colors.ENDC}")
        if not self.last_exposed_files:
            print(f"{Colors.YELLOW}Nenhum arquivo exposto encontrado. Execute a verificação primeiro.{Colors.ENDC}")
            input(f"\n{Colors.GREEN}Pressione Enter para continuar...{Colors.ENDC}")
            return
        print(f"\n{Colors.CYAN}Arquivos expostos encontrados:{Colors.ENDC}")
        downloadable_files = [f for f in self.last_exposed_files if f.get('status_code') == 200 or f.get('type') == 'port']
        for i, file_info in enumerate(downloadable_files, 1):
            print(f"{Colors.GREEN}[{i}]{Colors.ENDC} {file_info['url']} (Status: {file_info.get('status_code', 'N/A')}, Tamanho: {file_info.get('content_length', 'N/A')} bytes)")
        if not downloadable_files:
            print(f"{Colors.YELLOW}Nenhum arquivo baixável encontrado.{Colors.ENDC}")
            input(f"\n{Colors.GREEN}Pressione Enter para continuar...{Colors.ENDC}")
            return
        print(f"{Colors.GREEN}[A]{Colors.ENDC} Baixar todos os listados")
        print(f"{Colors.GREEN}[B]{Colors.ENDC} Baixar todos sem validação")
        print(f"{Colors.GREEN}[0]{Colors.ENDC} Voltar")
        choice = input(f"\n{Colors.YELLOW}Digite o número do arquivo (ou 'A'/'B' para todos, '0' para voltar):{Colors.ENDC} ").strip().lower()
        if choice == '0':
            return
        elif choice == 'a':
            print(f"\n{Colors.RED}AVISO: Confirme que você possui autorização para baixar todos os arquivos.{Colors.ENDC}")
            confirm = input(f"{Colors.YELLOW}Confirmar (s/n):{Colors.ENDC} ").strip().lower()
            if confirm != 's':
                print(f"{Colors.RED}Download cancelado.{Colors.ENDC}")
                return
            success_count = sum(1 for file_info in downloadable_files if self.tools.download_file(file_info['url'], os.path.basename(urlparse(file_info['url']).path)))
            print(f"{Colors.GREEN}Download concluído para {success_count} arquivos.{Colors.ENDC}")
        elif choice == 'b':
            print(f"\n{Colors.RED}AVISO: Confirme que você possui autorização para baixar todos os arquivos (sem validação).{Colors.ENDC}")
            confirm = input(f"{Colors.YELLOW}Confirmar (s/n):{Colors.ENDC} ").strip().lower()
            if confirm != 's':
                print(f"{Colors.RED}Download cancelado.{Colors.ENDC}")
                return
            success_count = sum(1 for file_info in downloadable_files if self.tools.download_file(file_info['url'], os.path.basename(urlparse(file_info['url']).path), skip_validation=True))
            print(f"{Colors.GREEN}Download concluído para {success_count} arquivos (sem validação).{Colors.ENDC}")
        else:
            try:
                index = int(choice) - 1
                if 0 <= index < len(downloadable_files):
                    file_info = downloadable_files[index]
                    print(f"\n{Colors.RED}AVISO: Confirme que você possui autorização para baixar este arquivo.{Colors.ENDC}")
                    print(f"{Colors.YELLOW}Ignorar validação para este arquivo? (s/n):{Colors.ENDC}")
                    skip_validation = input().strip().lower() == 's'
                    confirm = input(f"{Colors.YELLOW}Confirmar download (s/n):{Colors.ENDC} ").strip().lower()
                    if confirm != 's':
                        print(f"{Colors.RED}Download cancelado.{Colors.ENDC}")
                        return
                    self.tools.download_file(file_info['url'], os.path.basename(urlparse(file_info['url']).path), skip_validation)
                else:
                    print(f"{Colors.RED}Número inválido.{Colors.ENDC}")
            except ValueError:
                print(f"{Colors.RED}Entrada inválida.{Colors.ENDC}")
        input(f"\n{Colors.GREEN}Pressione Enter para continuar...{Colors.ENDC}")

    def proxy_menu(self):
        Banner.show()
        print(f"{Colors.CYAN}╔═══════════════════════════════════════════════════════════════╗{Colors.ENDC}")
        print(f"{Colors.CYAN}║                   {Colors.YELLOW}CONFIGURAÇÃO DE PROXY{Colors.CYAN}                   ║{Colors.ENDC}")
        print(f"{Colors.CYAN}╚═══════════════════════════════════════════════════════════════╝{Colors.ENDC}")
        current_proxy = self.proxy_manager.get_proxy_config()
        print(f"{Colors.CYAN}Proxy atual:{Colors.GREEN} {current_proxy['http'] if current_proxy else 'Desativado'}{Colors.ENDC}")
        print(f"\n{Colors.CYAN}Escolha o tipo de proxy:{Colors.ENDC}")
        print(f"{Colors.GREEN}[1]{Colors.ENDC} HTTP")
        print(f"{Colors.GREEN}[2]{Colors.ENDC} SOCKS4")
        print(f"{Colors.GREEN}[3]{Colors.ENDC} SOCKS5")
        print(f"{Colors.GREEN}[4]{Colors.ENDC} Adicionar múltiplos proxies")
        print(f"{Colors.GREEN}[5]{Colors.ENDC} Desativar proxy")
        print(f"{Colors.GREEN}[0]{Colors.ENDC} Voltar")
        choice = input(f"\n{Colors.YELLOW}Escolha uma opção:{Colors.ENDC} ")
        if choice == "0":
            return
        elif choice == "5":
            self.proxy_manager.set_proxy(None, None)
            self.tools = CollectionTools(self.logger, None)
            print(f"{Colors.GREEN}Proxy desativado!{Colors.ENDC}")
        elif choice in ["1", "2", "3"]:
            proxy_types = {"1": "http", "2": "socks4", "3": "socks5"}
            proxy_url = input(f"\n{Colors.YELLOW}Digite o endereço do proxy (ip:porta ou usuario:senha@ip:porta):{Colors.ENDC} ").strip()
            if self.proxy_manager.set_proxy(proxy_types[choice], proxy_url):
                self.tools = CollectionTools(self.logger, self.proxy_manager.get_proxy_config())
                print(f"{Colors.GREEN}Proxy configurado!{Colors.ENDC}")
            else:
                print(f"{Colors.RED}Falha ao configurar proxy.{Colors.ENDC}")
        elif choice == "4":
            print(f"{Colors.YELLOW}Digite os proxies (um por linha, formato: tipo://ip:porta). Digite vazio para finalizar:{Colors.ENDC}")
            while True:
                proxy_line = input().strip()
                if not proxy_line:
                    break
                try:
                    proxy_type, proxy_url = proxy_line.split("://", 1)
                    if proxy_type in ["http", "socks4", "socks5"]:
                        self.proxy_manager.add_proxy(proxy_type, proxy_url)
                    else:
                        print(f"{Colors.RED}Tipo de proxy inválido: {proxy_type}{Colors.ENDC}")
                except ValueError:
                    print(f"{Colors.RED}Formato inválido. Use: tipo://ip:porta{Colors.ENDC}")
            if self.proxy_manager.proxies:
                self.tools = CollectionTools(self.logger, self.proxy_manager.rotate_proxy())
                print(f"{Colors.GREEN}Proxies adicionados! Rotação ativada.{Colors.ENDC}")
        else:
            print(f"{Colors.RED}Opção inválida.{Colors.ENDC}")
        time.sleep(2)

    def about(self):
        Banner.show()
        print(f"{Colors.CYAN}╔═══════════════════════════════════════════════════════════════╗{Colors.ENDC}")
        print(f"{Colors.CYAN}║                      {Colors.YELLOW}SOBRE O PROGRAMA{Colors.CYAN}                     ║{Colors.ENDC}")
        print(f"{Colors.CYAN}╚═══════════════════════════════════════════════════════════════╝{Colors.ENDC}")
        print(f"\n{Colors.GREEN}Collected-DBs{Colors.ENDC} - Ferramenta para detecção de bancos de dados expostos.")
        print(f"\n{Colors.YELLOW}Versão:{Colors.ENDC} {VERSION}")
        print(f"{Colors.YELLOW}Autor:{Colors.ENDC} sentinelzxofc")
        print(f"{Colors.YELLOW}GitHub:{Colors.ENDC} https://github.com/sentinelzxofc/collected-dbs")
        print(f"\n{Colors.RED}AVISO LEGAL:{Colors.ENDC} Uso apenas com autorização explícita.")
        input(f"\n{Colors.GREEN}Pressione Enter para continuar...{Colors.ENDC}")

    def run(self):
        if not self.check_setup():
            return
        Banner.show()
        Animation.progress_bar("Inicializando", 2)
        self.main_menu()

if __name__ == "__main__":
    import warnings
    warnings.filterwarnings("ignore", category=requests.packages.urllib3.exceptions.InsecureRequestWarning)
    app = CollectedDBS()
    app.run()