#!/data/data/com.termux/files/usr/bin/bash

RED='\033[1;31m'
GREEN='\033[1;32m'
YELLOW='\033[1;33m'
CYAN='\033[1;36m'
BLUE='\033[1;34m'
NC='\033[0m'
BOLD='\033[1m'

loading_animation() {
    local msg="$1"
    local duration="$2"
    local chars=("⠋" "⠙" "⠹" "⠸" "⠼" "⠴" "⠦" "⠧" "⠇" "⠏")
    local end=$((SECONDS + duration))
    local i=0
    while [ $SECONDS -lt $end ]; do
        printf "\r${CYAN}${msg} ${chars[i]}${NC}"
        ((i = (i + 1) % ${#chars[@]}))
        sleep 0.1
    done
    printf "\r\033[K"
}

progress_bar() {
    local msg="$1"
    local duration="$2"
    local width=30
    local steps=20
    local sleep_time=$(echo "$duration / $steps" | bc -l)
    for ((i=0; i<=steps; i++)); do
        local percent=$((i * 100 / steps))
        local filled=$((i * width / steps))
        local empty=$((width - filled))
        local bar=$(printf '█%.0s' $(seq 1 $filled))
        local empty_bar=$(printf '░%.0s' $(seq 1 $empty))
        printf "\r${CYAN}${msg}: [${GREEN}${bar}${NC}${empty_bar}] ${percent}%%"
        sleep $sleep_time
    done
    printf "\r\033[K"
}

show_banner() {
    clear
    echo -e "${CYAN}╔═══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║                                                               ║${NC}"
    echo -e "${CYAN}║   ${RED} ██████╗ ██████╗ ██╗     ██╗     ███████╗ ██████╗████████╗${CYAN}   ║${NC}"
    echo -e "${CYAN}║   ${RED}██╔════╝██╔═══██╗██║     ██║     ██╔════╝██╔════╝╚══██╔══╝${CYAN}   ║${NC}"
    echo -e "${CYAN}║   ${RED}██║     ██║   ██║██║     ██║     █████╗  ██║        ██║${CYAN}      ║${NC}"
    echo -e "${CYAN}║   ${RED}██║     ██║   ██║██║     ██║     ██╔══╝  ██║        ██║${CYAN}      ║${NC}"
    echo -e "${CYAN}║   ${RED}╚██████╗╚██████╔╝███████╗███████╗███████╗╚██████╗   ██║${CYAN}      ║${NC}"
    echo -e "${CYAN}║   ${RED} ╚═════╝ ╚═════╝ ╚══════╝╚══════╝╚══════╝ ╚═════╝   ╚═╝${CYAN}      ║${NC}"
    echo -e "${CYAN}║                                                               ║${NC}"
    echo -e "${CYAN}║   ${GREEN}██████╗ ██████╗ ███████╗${CYAN}                              ║${NC}"
    echo -e "${CYAN}║   ${GREEN}██╔══██╗██╔══██╗██╔════╝${CYAN}                              ║${NC}"
    echo -e "${CYAN}║   ${GREEN}██║  ██║██████╔╝███████╗${CYAN}                              ║${NC}"
    echo -e "${CYAN}║   ${GREEN}██║  ██║██╔══██╗╚════██║${CYAN}                              ║${NC}"
    echo -e "${CYAN}║   ${GREEN}██████╔╝██████╔╝███████║${CYAN}                              ║${NC}"
    echo -e "${CYAN}║   ${GREEN}╚═════╝ ╚═════╝ ╚══════╝${CYAN}                              ║${NC}"
    echo -e "${CYAN}║                                                               ║${NC}"
    echo -e "${CYAN}╠═══════════════════════════════════════════════════════════════╣${NC}"
    echo -e "${CYAN}║ ${YELLOW}Script de Instalação - Versão 1.1.0${CYAN}                         ║${NC}"
    echo -e "${CYAN}║ ${YELLOW}GitHub: ${GREEN}https://github.com/sentinelzxofc/collected-dbs${CYAN}      ║${NC}"
    echo -e "${CYAN}║ ${YELLOW}Instagram: ${GREEN}@sentinelzxofc${CYAN}                             ║${NC}"
    echo -e "${CYAN}╚═══════════════════════════════════════════════════════════════╝${NC}"
    echo -e "${RED}${BOLD}AVISO LEGAL: Use apenas para fins educacionais e testes éticos."
    echo -e "O autor não se responsabiliza por qualquer uso indevido.${NC}\n"
    sleep 2
}

check_internet() {
    echo -e "${YELLOW}Verificando conexão com a internet...${NC}"
    if ! ping -c 1 8.8.8.8 &> /dev/null; then
        echo -e "${RED}Sem conexão com a internet. Verifique e tente novamente.${NC}"
        exit 1
    fi
    echo -e "${GREEN}Conexão OK!${NC}"
}

check_storage() {
    echo -e "${YELLOW}Verificando armazenamento disponível...${NC}"
    local available=$(df -h /data/data/com.termux/files/home | tail -1 | awk '{print $4}')
    local available_mb=$(echo $available | sed 's/G/*1024/' | sed 's/M//' | bc)
    if (( $(echo "$available_mb < 100" | bc -l) )); then
        echo -e "${RED}Espaço insuficiente (<100MB). Libere espaço e tente novamente.${NC}"
        exit 1
    fi
    echo -e "${GREEN}Armazenamento OK: ${available} disponíveis${NC}"
}

install_termux_packages() {
    local packages=("python" "git" "curl" "nmap" "wget" "tar")
    echo -e "${YELLOW}Verificando pacotes do Termux...${NC}"
    progress_bar "Atualizando repositórios" 3
    pkg update -y && pkg upgrade -y
    for package in "${packages[@]}"; do
        if ! command -v "$package" &> /dev/null; then
            echo -e "${YELLOW}Instalando ${package}...${NC}"
            loading_animation "Instalando $package" 2
            pkg install "$package" -y || {
                echo -e "${RED}Erro ao instalar ${package}. Verifique sua conexão e tente novamente.${NC}"
                exit 1
            }
        else
            echo -e "${GREEN}${package} já está instalado.${NC}"
        fi
    done
}

install_python_dependencies() {
    local packages=("requests" "beautifulsoup4" "tqdm" "tenacity" "pyyaml")
    echo -e "${YELLOW}Verificando dependências Python...${NC}"
    pip install --upgrade pip
    for package in "${packages[@]}"; do
        if ! python3 -c "import $package" 2> /dev/null; then
            echo -e "${YELLOW}Instalando ${package} (Python)...${NC}"
            loading_animation "Instalando $package" 2
            pip install --upgrade "$package" || {
                echo -e "${RED}Erro ao instalar ${package} (Python). Verifique sua conexão e tente novamente.${NC}"
                exit 1
            }
        else
            echo -e "${GREEN}${package} já está instalado.${NC}"
        fi
    done
}

clone_repository() {
    echo -e "${YELLOW}Verificando repositório...${NC}"
    if [ -d "collected-dbs" ]; then
        echo -e "${YELLOW}Diretório collected-dbs já existe. Fazendo backup...${NC}"
        mv collected-dbs collected-dbs-backup-$(date +%F-%H%M%S)
        echo -e "${YELLOW}Atualizando...${NC}"
        loading_animation "Clonando repositório" 3
        git clone https://github.com/sentinelzxofc/collected-dbs.git || {
            echo -e "${RED}Erro ao clonar o repositório. Verifique sua conexão e tente novamente.${NC}"
            exit 1
        }
    else
        echo -e "${YELLOW}Clonando repositório...${NC}"
        loading_animation "Clonando repositório" 3
        git clone https://github.com/sentinelzxofc/collected-dbs.git || {
            echo -e "${RED}Erro ao clonar o repositório. Verifique sua conexão e tente novamente.${NC}"
            exit 1
        }
    fi
    echo -e "${GREEN}Repositório configurado com sucesso!${NC}"
}

set_permissions() {
    echo -e "${YELLOW}Configurando permissões...${NC}"
    loading_animation "Configurando permissões" 2
    chmod +x collected-dbs/main.py
    echo -e "${GREEN}Permissões configuradas com sucesso!${NC}"
}

create_config_files() {
    echo -e "${YELLOW}Criando arquivos de configuração...${NC}"
    cd collected-dbs
    if [ ! -f "cookies.json" ]; then
        echo -e "{\"example.com\": {\"__ddg1\": \"example_cookie\"}}" > cookies.json
        echo -e "${GREEN}cookies.json criado com exemplo.${NC}"
    fi
    if [ ! -f "proxies.txt" ]; then
        echo -e "http://example.proxy:8080" > proxies.txt
        echo -e "${GREEN}proxies.txt criado com exemplo.${NC}"
    fi
    cd ..
}

set_alias() {
    echo -e "${YELLOW}Configurando alias...${NC}"
    local alias_cmd="alias collected-dbs='cd $(pwd)/collected-dbs && python3 main.py'"
    if ! grep -Fx "$alias_cmd" ~/.bashrc &> /dev/null; then
        echo "$alias_cmd" >> ~/.bashrc
        source ~/.bashrc
        echo -e "${GREEN}Alias 'collected-dbs' configurado!${NC}"
    else
        echo -e "${GREEN}Alias já configurado.${NC}"
    fi
}

main() {
    show_banner
    echo -e "${CYAN}Iniciando configuração do ambiente para Collected-DBs...${NC}"
    progress_bar "Preparando ambiente" 3
    if [ ! -d "/data/data/com.termux/files/usr" ]; then
        echo -e "${RED}Este script deve ser executado no Termux.${NC}"
        exit 1
    fi
    check_internet
    check_storage
    install_termux_packages
    install_python_dependencies
    clone_repository
    set_permissions
    create_config_files
    set_alias
    echo -e "\n${GREEN}${BOLD}Instalação concluída com sucesso!${NC}"
    echo -e "${CYAN}Para executar o Collected-DBs, use:${NC}"
    echo -e "${GREEN}collected-dbs${NC}"
    echo -e "${YELLOW}Certifique-se de usar a ferramenta de forma ética e legal.${NC}"
}

main